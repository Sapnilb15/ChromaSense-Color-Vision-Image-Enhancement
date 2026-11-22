"""Cross-browser checks for the comparison modes and session recovery."""

import base64
import io
import sys
from pathlib import Path

import pytest
from axe_playwright_python.sync_playwright import Axe
from PIL import Image
from playwright.sync_api import expect

AXE_OPTIONS = {"runOnly": {"type": "tag", "values": ["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"]}}


@pytest.mark.parametrize("engine", ["chromium", "firefox", "webkit"])
@pytest.mark.parametrize("width", [375, 1280])
@pytest.mark.parametrize("keyboard", [False, True], ids=["pointer", "keyboard"])
def test_compare_and_export(browsers, server, sample, engine, width, keyboard):
    context = browsers(engine).new_context(viewport={"width": width, "height": 800})
    page = context.new_page()
    page.goto(server.url)

    # Safari on macOS uses Option-Tab to include all controls.
    tab = "Alt+Tab" if engine == "webkit" and sys.platform == "darwin" else "Tab"

    def activate(control):
        if keyboard:
            for _ in range(40):
                if control.evaluate("e => e === document.activeElement"):
                    break
                page.keyboard.press(tab)
            expect(control).to_be_focused()
            page.keyboard.press("Enter")
        else:
            control.click()

    picker = page.get_by_label("Choose a PNG or JPEG image")
    with page.expect_file_chooser() as choosing:
        activate(picker)
    choosing.value.set_files(sample("valid.png"))
    expect(page.get_by_role("status").filter(has_text="Image uploaded")).to_be_visible()
    if keyboard:
        page.keyboard.press(tab)
        expect(page.get_by_label("Protan", exact=True)).to_be_focused()
        page.keyboard.press("ArrowDown")
    else:
        page.get_by_label("Deutan", exact=True).check()
    activate(page.get_by_role("button", name="Enhance image"))
    expect(page.locator("#eligible")).to_have_text("1")
    expect(page.locator("#improved")).to_have_text("1")
    expect(page.locator("#percent")).to_have_text("100%")
    switch = page.get_by_role("button", name="Side by side")
    activate(switch)
    expect(switch).to_have_attribute("aria-pressed", "true")
    original = page.locator("#compare-original").bounding_box()
    enhanced = page.locator("#compare-enhanced").bounding_box()
    assert enhanced["x"] >= original["x"] + original["width"] or (
        enhanced["y"] >= original["y"] + original["height"]
    )
    activate(switch)
    if keyboard:
        page.keyboard.press(tab)
        expect(page.get_by_label("Comparison position")).to_be_focused()
        page.keyboard.press("ArrowRight")
        expect(page.locator("#compare-value")).to_have_text("51 percent enhanced")
    else:
        frame = page.locator("#compare-frame")
        frame.scroll_into_view_if_needed()
        box = frame.bounding_box()
        page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        page.mouse.down()
        page.mouse.move(box["x"] + box["width"] / 4, box["y"] + box["height"] / 2)
        page.mouse.up()
        expect(page.locator("#compare-value")).to_have_text("25 percent enhanced")
    with page.expect_download() as saving:
        activate(page.get_by_role("link", name="Download enhanced PNG"))
    saved = saving.value
    assert saved.suggested_filename == "chromasense-enhanced.png"
    shown = page.request.get(f"{server.url}/api/image/view/enhanced")
    assert Image.open(saved.path()).tobytes() == Image.open(io.BytesIO(shown.body())).tobytes()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    context.close()


def test_expired_session_recovers_by_uploading_again(page, server, sample):
    picker = page.get_by_label("Choose a PNG or JPEG image")
    picker.set_input_files(sample("valid.png"))
    expect(page.locator("#status")).to_contain_text("Done:")
    page.get_by_label("Deutan", exact=True).check()
    page.request.post(f"{server.url}/api/session/end")
    enhance = page.get_by_role("button", name="Enhance image")
    enhance.click()
    expect(page.locator("#status")).to_contain_text("Error: Upload an image first.")
    expect(enhance).to_be_disabled()
    expect(page.locator("#download-section")).to_be_hidden()
    picker.set_input_files(sample("valid.jpg"))
    expect(enhance).to_be_enabled()


def test_drop_and_retry_block_conflicting_requests(page, sample):
    payload = base64.b64encode(Path(sample("valid.png")).read_bytes()).decode()
    transfer = page.evaluate_handle(
        """data => {
            const transfer = new DataTransfer();
            const bytes = Uint8Array.from(atob(data), c => c.charCodeAt(0));
            transfer.items.add(new File([bytes], 'chart.png', {type: 'image/png'}));
            return transfer;
        }""",
        payload,
    )
    held = []
    page.route("**/api/image", lambda route: held.append(route))
    stage = page.locator("#stage")
    stage.dispatch_event("dragover", {"dataTransfer": transfer})
    assert "dragging" in stage.get_attribute("class")
    stage.dispatch_event("drop", {"dataTransfer": transfer})
    expect(page.locator("#status")).to_contain_text("Uploading:")
    stage.dispatch_event("drop", {"dataTransfer": transfer})
    expect(page.get_by_label("Deutan", exact=True)).to_be_disabled()
    assert len(held) == 1
    assert Axe().run(page, options=AXE_OPTIONS).violations_count == 0
    held.pop().continue_()
    expect(page.locator("#status")).to_contain_text("Image uploaded")
    page.get_by_label("Deutan", exact=True).check()
    page.route("**/api/image/enhance", lambda route: held.append(route))
    enhance = page.get_by_role("button", name="Enhance image")
    enhance.click()
    expect(page.locator("#status")).to_contain_text("Enhancing:")
    expect(enhance).to_be_disabled()
    expect(page.locator("#original-image")).to_be_visible()
    expect(page.locator("#download-link")).to_be_hidden()
    assert Axe().run(page, options=AXE_OPTIONS).violations_count == 0
    held.pop().abort()
    expect(page.locator("#status")).to_contain_text("Error:")
    page.unroute("**/api/image/enhance")
    enhance.click()
    expect(page.locator("#download-link")).to_be_visible()


def test_no_improvement_keeps_original_and_reports_zero_percent(page, tmp_path):
    path = tmp_path / "violet-pair.png"
    picture = Image.new("RGB", (60, 40), (150, 25, 232))
    picture.paste((194, 6, 158), (30, 0, 60, 40))
    picture.save(path)
    page.get_by_label("Choose a PNG or JPEG image").set_input_files(path)
    expect(page.locator("#status")).to_contain_text("Image uploaded")
    page.get_by_label("Protan", exact=True).check()
    page.get_by_role("button", name="Enhance image").click()
    expect(page.locator("#result-title")).to_have_text("No improvement")
    expect(page.locator("#eligible")).to_have_text("1")
    expect(page.locator("#improved")).to_have_text("0")
    expect(page.locator("#percent")).to_have_text("0%")
    expect(page.locator("#compare-original")).to_be_visible()
    expect(page.locator("#download-link")).to_be_hidden()
    assert Axe().run(page, options=AXE_OPTIONS).violations_count == 0
