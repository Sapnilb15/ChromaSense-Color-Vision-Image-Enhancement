// Step 3: show the result. For an enhanced result, the enhanced image covers the left part of
// the frame, as far as the comparison slider, so both versions show the same area.
const section = document.getElementById("compare-section");
const message = document.getElementById("compare-message");
const frame = document.getElementById("compare-frame");
const original = document.getElementById("compare-original");
const enhanced = document.getElementById("compare-enhanced");
const caption = document.getElementById("compare-caption");
const control = document.getElementById("compare-control");
const slider = document.getElementById("compare-position");
const value = document.getElementById("compare-value");
const download = document.getElementById("download-section");

function applyPosition() {
  const percent = Number(slider.value);
  enhanced.style.clipPath = `inset(0 ${100 - percent}% 0 0)`;
  value.textContent = `${percent} percent enhanced`;
}

export function showResult({ outcome, text, type, severity }) {
  const stamp = Date.now();
  const label = `${type}, severity ${severity}`;
  original.src = `/api/image/view/original?v=${stamp}`;
  message.textContent = text;
  section.hidden = false;

  if (outcome === "enhanced") {
    enhanced.src = `/api/image/view/enhanced?v=${stamp}`;
    enhanced.alt = `Enhanced image for ${label}`;
    enhanced.hidden = false;
    control.hidden = false;
    frame.classList.add("comparing");
    caption.textContent = `Original and enhanced image for ${label}.`;
    applyPosition();
    download.hidden = false;
  } else {
    enhanced.removeAttribute("src");
    enhanced.alt = "";
    enhanced.hidden = true;
    control.hidden = true;
    frame.classList.remove("comparing");
    caption.textContent = "Original image. No enhanced image was produced.";
    download.hidden = true;
  }
}

export function resetResult() {
  section.hidden = true;
  download.hidden = true;
  message.textContent = "";
  enhanced.removeAttribute("src");
}

slider.addEventListener("input", applyPosition);
applyPosition();
