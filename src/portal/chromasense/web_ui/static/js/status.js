// One shared live region for every status message. Each message starts with a text label,
// so its meaning never depends on color.
const LABELS = { info: "Working", success: "Done", error: "Error" };

export function setStatus(text, kind = "info", label = LABELS[kind]) {
  const region = document.getElementById("status");
  region.textContent = `${label}: ${text}`;
  region.dataset.kind = kind;
}
