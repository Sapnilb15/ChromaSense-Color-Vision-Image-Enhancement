import io

import numpy as np
import pytest
from PIL import Image
from playwright.sync_api import expect

DONE_UPLOAD = "Done: Image uploaded, 60 by 40 pixels."
ENHANCED_MESSAGE = "Adjusted 1 of 1 color pairs likely to be confused."


def _upload(page, path):
    page.locator("#file-input").set_input_files(path)
    expect(page.locator("#status")).to_contain_text("Done: Image uploaded")


def _enhance_requests(page):
    bodies = []
    page.on(
        "request",
        lambda r: r.url.endswith("/api/image/enhance") and bodies.append(r.post_data_json),
    )
    return bodies


def _red_blue_png(tmp_path):
    pixels = np.full((40, 60, 3), 128, dtype=np.uint8)
    pixels[:, :20] = (200, 40, 40)
    pixels[:, 20:40] = (40, 40, 200)
    path = tmp_path / "red-blue.png"
    Image.fromarray(pixels).save(path)
    return str(path)


def test_enhance_button_needs_an_image_and_a_profile(page, sample):
    button = page.get_by_role("button", name="Enhance image")
    expect(button).to_be_disabled()
    page.get_by_label("Deutan").check()
    expect(button).to_be_disabled()
    _upload(page, sample("valid.png"))
    expect(button).to_be_enabled()


def test_only_protan_and_deutan_are_offered(page):
    values = page.locator('input[name="cvd-type"]').evaluate_all("els => els.map(e => e.value)")
    assert values == ["protan", "deutan"]
    expect(page.locator('input[name="cvd-type"]:checked')).to_have_count(0)


@pytest.mark.parametrize(("profile", "severity"), [("Protan", "0"), ("Deutan", "100")])
def test_profile_and_severity_limits_are_sent(page, sample, profile, severity):
    bodies = _enhance_requests(page)
    _upload(page, sample("valid.png"))
    page.get_by_label(profile).check()
    page.locator("#severity").fill(severity)
    expect(page.locator("#severity-value")).to_have_text(f"{severity}%")
    page.get_by_role("button", name="Enhance image").click()
    expect(page.locator("#status")).to_contain_text("Done:")
    assert bodies == [{"type": profile.lower(), "severity": float(severity) / 100}]


def test_severity_starts_at_full_strength(page):
    expect(page.locator("#severity")).to_have_value("100")
    expect(page.locator("#severity-value")).to_have_text("100%")
    expect(page.locator("#severity")).to_have_attribute("min", "0")
    expect(page.locator("#severity")).to_have_attribute("max", "100")


def test_enhanced_result_compares_the_same_area_and_downloads_the_shown_png(page, sample, server):
    _upload(page, sample("valid.png"))
    page.get_by_label("Deutan").check()
    page.get_by_role("button", name="Enhance image").click()

    expect(page.locator("#status")).to_have_text(f"Done: {ENHANCED_MESSAGE}")
    expect(page.locator("#compare-section")).to_be_visible()
    expect(page.locator("#compare-message")).to_have_text(ENHANCED_MESSAGE)
    enhanced = page.locator("#compare-enhanced")
    expect(enhanced).to_have_attribute("alt", "Enhanced image for deutan, severity 1")
    page.wait_for_function(
        "document.getElementById('compare-enhanced').naturalWidth === 60"
        " && document.getElementById('compare-original').naturalWidth === 60"
    )

    # Both images cover exactly the same box, so the slider compares the same area.
    original_box = page.locator("#compare-original").bounding_box()
    enhanced_box = enhanced.bounding_box()
    assert original_box == enhanced_box

    slider = page.locator("#compare-position")
    slider.fill("20")
    expect(page.locator("#compare-value")).to_have_text("20 percent enhanced")
    assert enhanced.evaluate("e => e.style.clipPath") == "inset(0px 80% 0px 0px)"
    slider.fill("100")
    assert enhanced.evaluate("e => e.style.clipPath") == "inset(0px 0% 0px 0px)"

    link = page.get_by_role("link", name="Download enhanced PNG")
    expect(link).to_be_visible()
    with page.expect_download() as download_info:
        link.click()
    download = download_info.value
    assert download.suggested_filename == "chromasense-enhanced.png"
    downloaded = Image.open(download.path())
    assert downloaded.format == "PNG"

    shown = page.request.get(f"{server.url}/api/image/view/enhanced").body()
    np.testing.assert_array_equal(
        np.asarray(downloaded.convert("RGB")),
        np.asarray(Image.open(io.BytesIO(shown)).convert("RGB")),
    )


def test_no_confusable_pairs_shows_the_message_and_no_download(page, tmp_path):
    _upload(page, _red_blue_png(tmp_path))
    page.get_by_label("Deutan").check()
    page.get_by_role("button", name="Enhance image").click()

    message = (
        "No colors likely to be confused were found for the deutan profile at severity 1. "
        "The original image is unchanged."
    )
    expect(page.locator("#status")).to_have_text(f"Done: {message}")
    expect(page.locator("#compare-message")).to_have_text(message)
    expect(page.locator("#compare-original")).to_be_visible()
    expect(page.locator("#compare-enhanced")).to_be_hidden()
    expect(page.locator("#compare-control")).to_be_hidden()
    expect(page.locator("#download-section")).to_be_hidden()


def test_changing_the_profile_and_enhancing_again_updates_the_result(page, sample):
    bodies = _enhance_requests(page)
    _upload(page, sample("valid.png"))
    page.get_by_label("Deutan").check()
    page.get_by_role("button", name="Enhance image").click()
    expect(page.locator("#compare-message")).to_have_text(ENHANCED_MESSAGE)

    page.get_by_label("Protan").check()
    page.get_by_role("button", name="Enhance image").click()

    expect(page.locator("#compare-message")).to_contain_text("for the protan profile")
    expect(page.locator("#download-section")).to_be_hidden()
    assert [body["type"] for body in bodies] == ["deutan", "protan"]


def test_new_upload_hides_the_previous_result(page, sample):
    _upload(page, sample("valid.png"))
    page.get_by_label("Deutan").check()
    page.get_by_role("button", name="Enhance image").click()
    expect(page.locator("#download-section")).to_be_visible()

    _upload(page, sample("valid.jpg"))

    expect(page.locator("#compare-section")).to_be_hidden()
    expect(page.locator("#download-section")).to_be_hidden()


def test_enhance_status_announces_the_request(page, sample):
    _upload(page, sample("valid.png"))
    page.get_by_label("Deutan").check()
    statuses = []
    page.expose_function("recordStatus", lambda text: statuses.append(text))
    page.evaluate(
        """() => {
            const region = document.getElementById('status');
            new MutationObserver(() => window.recordStatus(region.textContent))
                .observe(region, {childList: true, characterData: true, subtree: true});
        }"""
    )
    page.get_by_role("button", name="Enhance image").click()
    expect(page.locator("#status")).to_have_text(f"Done: {ENHANCED_MESSAGE}")
    assert statuses[0] == "Enhancing: applying the deutan profile at severity 1."
