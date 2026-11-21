import time

import pytest
from playwright.sync_api import expect


def _status(page):
    return page.locator("#status")


@pytest.mark.parametrize("name", ["valid.png", "valid.jpg"])
def test_valid_upload_shows_the_original_and_announces_its_size(page, sample, name):
    page.locator("#file-input").set_input_files(sample(name))

    expect(_status(page)).to_have_text("Done: Image uploaded, 60 by 40 pixels.")
    expect(page.locator("#original-section")).to_be_visible()
    image = page.locator("#original-image")
    expect(image).to_have_attribute("alt", "Original image")
    page.wait_for_function("document.getElementById('original-image').naturalWidth === 60")
    expect(page.locator("#original-caption")).to_have_text(f"{name}, 60 by 40 pixels.")


@pytest.mark.parametrize(
    ("name", "message"),
    [
        ("not_an_image.png", "Error: This file is not a PNG or JPEG image."),
        ("truncated.jpg", "Error: This image file is damaged or incomplete and cannot be opened."),
    ],
)
def test_invalid_file_shows_the_reason_and_no_image(page, sample, name, message):
    view_requests = []
    page.on("request", lambda r: "/api/image/view/" in r.url and view_requests.append(r.url))

    page.locator("#file-input").set_input_files(sample(name))

    expect(_status(page)).to_have_text(message)
    expect(_status(page)).to_have_attribute("data-kind", "error")
    expect(page.locator("#original-section")).to_be_hidden()
    assert view_requests == []


def test_error_after_a_valid_upload_keeps_the_earlier_original(page, sample):
    page.locator("#file-input").set_input_files(sample("valid.png"))
    expect(_status(page)).to_have_text("Done: Image uploaded, 60 by 40 pixels.")

    page.locator("#file-input").set_input_files(sample("not_an_image.png"))

    expect(_status(page)).to_have_text("Error: This file is not a PNG or JPEG image.")
    expect(page.locator("#original-section")).to_be_visible()


def test_focus_stays_on_the_file_input(page, sample):
    page.locator("#file-input").focus()
    page.locator("#file-input").set_input_files(sample("valid.png"))
    expect(_status(page)).to_have_text("Done: Image uploaded, 60 by 40 pixels.")
    assert page.evaluate("document.activeElement.id") == "file-input"


def test_status_region_and_limits_are_exposed_to_screen_readers(page):
    status = _status(page)
    expect(status).to_have_attribute("role", "status")
    expect(status).to_have_attribute("aria-live", "polite")
    file_input = page.get_by_label("Choose a PNG or JPEG image")
    expect(file_input).to_have_attribute("aria-describedby", "file-limits")
    expect(page.locator("#file-limits")).to_have_text("PNG or JPEG, up to 10 MB and 12 megapixels.")


def test_footer_makes_no_medical_claim(page):
    footer = page.locator("footer").inner_text()
    assert "does not diagnose" in footer and "does not show exactly" in footer


def test_closing_the_tab_ends_the_session(page, server, sample):
    page.locator("#file-input").set_input_files(sample("valid.png"))
    expect(_status(page)).to_have_text("Done: Image uploaded, 60 by 40 pixels.")
    assert len(server.session_folders()) == 1

    page.close()

    deadline = time.monotonic() + 5
    while server.session_folders() and time.monotonic() < deadline:
        time.sleep(0.05)
    assert server.session_folders() == []
