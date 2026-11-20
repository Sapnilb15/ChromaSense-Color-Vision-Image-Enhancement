"""Accessibility, layout, and interface copy checks (SRS-NFR-002, SRS-NFR-003, SRS-NFR-006)."""

import re
from pathlib import Path

import pytest
from axe_playwright_python.sync_playwright import Axe
from playwright.sync_api import expect

from chromasense.core.models import Outcome
from chromasense.core.policy.outcome import message_for
from color_engine.models import CvdProfile, CvdType, SeparationReport5

AXE_OPTIONS = {
    "runOnly": {"type": "tag", "values": ["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"]},
    "resultTypes": ["violations"],
}
VIEWPORTS = [(375, 812), (1280, 800)]
BANNED = ["diagnos", "medical", "cure", "correct your vision", "see what others see"]
# The footer states what ChromaSense does not do; those two phrases are the only allowed uses.
ALLOWED = ["does not diagnose", "give medical advice"]


def _axe_violations(page) -> str:
    results = Axe().run(page, options=AXE_OPTIONS)
    return "" if results.violations_count == 0 else results.generate_report()


def _upload(page, path):
    page.locator("#file-input").set_input_files(path)
    expect(page.locator("#status")).to_contain_text("Done: Image uploaded")


def _enhance(page, profile="Deutan"):
    page.get_by_label(profile).check()
    page.get_by_role("button", name="Enhance image").click()
    expect(page.locator("#status")).to_contain_text("Done:")
    page.wait_for_function(
        "!document.getElementById('compare-original').src"
        " || document.getElementById('compare-original').complete"
    )


def _focused(page) -> dict:
    return page.evaluate(
        """() => {
            const e = document.activeElement;
            const style = getComputedStyle(e);
            return {
                id: e.id, tag: e.tagName, type: e.type || '', text: (e.textContent || '').trim(),
                outline: style.outlineStyle, outlineWidth: parseFloat(style.outlineWidth),
                focusVisible: e.matches(':focus-visible'),
            };
        }"""
    )


def _tab_to(page, element_id, limit=30):
    for _ in range(limit):
        page.keyboard.press("Tab")
        state = _focused(page)
        if state["id"] == element_id:
            return state
    raise AssertionError(f"Tab never reached #{element_id}")


def _assert_visible_focus(state):
    assert state["focusVisible"], state
    assert state["outline"] != "none" and state["outlineWidth"] >= 2, state


# Keyboard


def test_full_workflow_by_keyboard_with_visible_focus(page, sample):
    stops = []

    stops.append(_tab_to(page, "file-input"))
    page.locator("#file-input").set_input_files(sample("valid.png"))
    expect(page.locator("#status")).to_contain_text("Done: Image uploaded")

    stops.append(_tab_to(page, "type-protan"))
    page.keyboard.press("ArrowDown")  # moves to and checks Deutan
    expect(page.get_by_label("Deutan")).to_be_checked()
    stops.append(_focused(page))

    stops.append(_tab_to(page, "severity"))
    page.keyboard.press("ArrowLeft")
    expect(page.locator("#severity")).to_have_value("0.95")
    page.keyboard.press("End")
    expect(page.locator("#severity")).to_have_value("1")

    stops.append(_tab_to(page, "enhance-button"))
    page.keyboard.press("Enter")
    expect(page.locator("#status")).to_have_text(
        "Done: Adjusted 1 of 1 color pairs likely to be confused."
    )

    stops.append(_tab_to(page, "compare-position"))
    page.keyboard.press("ArrowRight")
    expect(page.locator("#compare-value")).to_have_text("51 percent enhanced")

    stops.append(_tab_to(page, "download-link"))
    with page.expect_download() as download_info:
        page.keyboard.press("Enter")
    assert download_info.value.suggested_filename == "chromasense-enhanced.png"

    for state in stops:
        _assert_visible_focus(state)


def test_skip_link_is_the_first_stop_and_moves_to_main(page):
    page.keyboard.press("Tab")
    state = _focused(page)
    assert state["text"] == "Skip to main content"
    _assert_visible_focus(state)
    page.keyboard.press("Enter")
    assert page.evaluate("document.activeElement.id") == "main"


def test_no_keyboard_trap(page, sample):
    _upload(page, sample("valid.png"))
    _enhance(page)
    seen = []
    for _ in range(40):
        page.keyboard.press("Tab")
        seen.append(_focused(page)["id"] or _focused(page)["tag"])
    # Focus moves past the last control and wraps, so nothing holds it.
    assert "download-link" in seen
    assert seen.index("download-link") < len(seen) - 1
    for _ in range(40):
        page.keyboard.press("Shift+Tab")
    assert _focused(page)["id"] != "download-link"


# Automated WCAG checks


def test_axe_before_upload(page):
    assert _axe_violations(page) == ""


def test_axe_after_upload(page, sample):
    _upload(page, sample("valid.png"))
    assert _axe_violations(page) == ""


def test_axe_after_an_enhanced_result(page, sample):
    _upload(page, sample("valid.png"))
    _enhance(page)
    expect(page.locator("#download-section")).to_be_visible()
    assert _axe_violations(page) == ""


def test_axe_after_an_error(page, sample):
    page.locator("#file-input").set_input_files(sample("not_an_image.png"))
    expect(page.locator("#status")).to_contain_text("Error:")
    assert _axe_violations(page) == ""


def test_axe_after_a_no_pairs_result(page, sample):
    _upload(page, sample("valid.png"))
    _enhance(page, profile="Protan")
    expect(page.locator("#compare-message")).to_contain_text("No colors likely to be confused")
    assert _axe_violations(page) == ""


# Layout


@pytest.mark.parametrize(("width", "height"), VIEWPORTS)
def test_no_horizontal_scroll_and_the_workflow_completes(browser, server, sample, width, height):
    context = browser.new_context(viewport={"width": width, "height": height})
    page = context.new_page()
    page.goto(server.url)

    def no_horizontal_scroll():
        return page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")

    assert no_horizontal_scroll()
    _upload(page, sample("valid.png"))
    assert no_horizontal_scroll()
    _enhance(page)
    expect(page.get_by_role("link", name="Download enhanced PNG")).to_be_visible()
    assert no_horizontal_scroll()
    assert _axe_violations(page) == ""
    context.close()


@pytest.mark.parametrize(("width", "height"), VIEWPORTS)
def test_large_image_fits_the_viewport(browser, server, tmp_path, width, height):
    import numpy as np
    from PIL import Image

    pixels = np.full((900, 2400, 3), 128, dtype=np.uint8)
    pixels[:, :1200] = (200, 40, 40)
    pixels[:, 1200:] = (40, 160, 40)
    path = tmp_path / "wide.png"
    Image.fromarray(pixels).save(path)

    context = browser.new_context(viewport={"width": width, "height": height})
    page = context.new_page()
    page.goto(server.url)
    _upload(page, str(path))
    _enhance(page)
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    context.close()


# Not color alone


def test_every_status_message_starts_with_a_text_label(page, sample):
    page.locator("#file-input").set_input_files(sample("not_an_image.png"))
    expect(page.locator("#status")).to_have_text(re.compile(r"^Error: "))
    _upload(page, sample("valid.png"))
    expect(page.locator("#status")).to_have_text(re.compile(r"^Done: "))


def test_every_control_has_a_text_label(page, sample):
    _upload(page, sample("valid.png"))
    _enhance(page)
    unlabeled = page.evaluate(
        """() => [...document.querySelectorAll('input, button, a[href]')]
            .filter(e => e.offsetParent !== null || e.type === 'file')
            .filter(e => {
                const labelled = e.labels && e.labels.length && e.labels[0].textContent.trim();
                const text = e.textContent && e.textContent.trim();
                return !(labelled || text || e.getAttribute('aria-label'));
            })
            .map(e => e.outerHTML)"""
    )
    assert unlabeled == []


# Copy


def _assert_no_claims(text: str) -> None:
    lowered = text.lower()
    for allowed in ALLOWED:
        lowered = lowered.replace(allowed, "")
    found = [phrase for phrase in BANNED if phrase in lowered]
    assert found == [], f"banned wording {found} in: {text}"


def test_page_copy_makes_no_medical_or_perception_claims(page, sample):
    _assert_no_claims(page.locator("body").inner_text())
    _upload(page, sample("valid.png"))
    _enhance(page)
    _assert_no_claims(page.locator("body").inner_text())


def test_templates_and_scripts_make_no_claims():
    web_ui = Path(__file__).resolve().parents[2] / "chromasense" / "web_ui"
    for path in [*web_ui.rglob("*.html"), *web_ui.rglob("*.js")]:
        _assert_no_claims(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("outcome", list(Outcome))
def test_outcome_messages_make_no_claims(outcome):
    report = SeparationReport5(pairs=(), newly_confusable=(), eligible_count=2, improved_count=1)
    _assert_no_claims(message_for(outcome, report, CvdProfile(CvdType.DEUTAN, 0.5)))


def test_axe_check_can_fail(page):
    """Guard: prove the axe run is real by breaking the page and expecting violations."""
    page.evaluate(
        """() => {
            document.querySelector('label[for="file-input"]').remove();
            document.getElementById('file-input').removeAttribute('aria-describedby');
            const faint = document.createElement('p');
            faint.textContent = 'Faint text';
            faint.style.color = '#dddddd';
            document.getElementById('main').append(faint);
        }"""
    )
    report = _axe_violations(page)
    assert "label" in report.lower()
    assert "contrast" in report.lower()
