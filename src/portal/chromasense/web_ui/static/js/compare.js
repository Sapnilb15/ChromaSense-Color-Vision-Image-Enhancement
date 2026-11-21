const byId = (id) => document.getElementById(id);
const frame = byId("compare-frame");
const slider = byId("compare-position");
const enhanced = byId("compare-enhanced");
const mode = byId("mode");
const labels = {
  enhanced: "Enhancement complete",
  no_confusable_pairs: "No confusable pairs",
  not_improved: "No improvement",
};

function position() {
  const percent = Number(slider.value);
  enhanced.style.clipPath = frame.classList.contains("split") ? "none" : `inset(0 ${100 - percent}% 0 0)`;
  frame.style.setProperty("--position", `${percent}%`);
  byId("compare-value").textContent = `${percent} percent enhanced`;
  slider.setAttribute("aria-valuetext", `${percent} percent enhanced`);
}

function setMode(split, available) {
  mode.setAttribute("aria-pressed", String(split));
  mode.hidden = !available;
  frame.classList.toggle("split", split);
  frame.classList.toggle("overlay", available && !split);
  byId("divider").hidden = byId("compare-control").hidden = split || !available;
  position();
}

export function resetResult() {
  byId("compare-section").hidden = true;
  byId("download-section").hidden = true;
  enhanced.removeAttribute("src");
  byId("compare-original").removeAttribute("src");
}

export async function showResult(result, type, severity) {
  const available = result.outcome === "enhanced";
  const original = byId("compare-original");
  original.src = byId("original-image").src;
  enhanced.hidden = byId("enhanced-tile").hidden = !available;
  if (available) {
    enhanced.alt = `Enhanced image for ${type}, severity ${severity}`;
    enhanced.src = `/api/image/view/enhanced?v=${Date.now()}`;
    await enhanced.decode();
  }
  await original.decode();
  slider.value = 50;
  setMode(false, available);
  byId("compare-message").textContent = result.message;
  byId("result-title").textContent = labels[result.outcome];
  const { eligible_count: eligible, improved_count: improved } = result;
  const percent = eligible > 0 ? ` (${Math.round(100 * improved / eligible)}%)` : "";
  byId("metrics").textContent = `${type} · ${Math.round(severity * 100)}% severity · ${eligible} eligible pairs · ${improved} improved${percent}`;
  byId("original-section").hidden = true;
  byId("compare-section").hidden = false;
  byId("download-section").hidden = !available;
  byId("view-label").textContent = available ? "Comparison" : "Original";
}

function drag(event) {
  const box = frame.getBoundingClientRect();
  slider.value = Math.round(100 * (event.clientX - box.left) / box.width);
  position();
}

frame.addEventListener("pointerdown", (event) => {
  if (!frame.classList.contains("overlay") || !event.isPrimary || event.button !== 0) return;
  frame.setPointerCapture(event.pointerId);
  drag(event);
});
frame.addEventListener("pointermove", (event) => {
  if (frame.hasPointerCapture(event.pointerId)) drag(event);
});
frame.addEventListener("dragstart", (event) => event.preventDefault());
mode.addEventListener("click", () => setMode(!frame.classList.contains("split"), true));
slider.addEventListener("input", position);
