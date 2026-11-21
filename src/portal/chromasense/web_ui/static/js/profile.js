// Step 2: choose a profile and severity, then ask the server for an enhanced result.
import { resetResult, showResult } from "./compare.js";
import { setStatus } from "./status.js";

const button = document.getElementById("enhance-button");
const hint = document.getElementById("enhance-hint");
const severity = document.getElementById("severity");
const severityValue = document.getElementById("severity-value");
let hasImage = false;
let busy = false;

function chosenType() {
  const checked = document.querySelector('input[name="cvd-type"]:checked');
  return checked ? checked.value : null;
}

function updateButton() {
  const ready = hasImage && chosenType() !== null;
  button.disabled = !ready;
  // While a request runs, the button stays focusable so keyboard focus is not lost; it only
  // reports itself as unavailable, and enhance() ignores presses until the result arrives.
  if (busy) button.setAttribute("aria-disabled", "true");
  else button.removeAttribute("aria-disabled");
  hint.hidden = ready;
}

function showSeverity() {
  severityValue.textContent = Number(severity.value).toFixed(2);
}

async function errorMessage(response) {
  try {
    const body = await response.json();
    if (body && body.message) return body.message;
  } catch {
    // Fall through to the generic message.
  }
  return "The image could not be enhanced. Try again.";
}

async function enhance() {
  const type = chosenType();
  if (!hasImage || !type || busy) return;
  const level = Number(severity.value);

  busy = true;
  updateButton();
  setStatus(`applying the ${type} profile at severity ${level}.`, "info", "Enhancing");
  try {
    const response = await fetch("/api/image/enhance", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type, severity: level }),
    });
    if (response.status !== 200) {
      setStatus(await errorMessage(response), "error");
      return;
    }
    const result = await response.json();
    showResult({ outcome: result.outcome, text: result.message, type, severity: level });
    setStatus(result.message, "success");
  } catch {
    setStatus("The request did not reach the server. Try again.", "error");
  } finally {
    busy = false;
    updateButton();
  }
}

document.addEventListener("chromasense:uploaded", () => {
  hasImage = true;
  resetResult();
  updateButton();
});
document.querySelectorAll('input[name="cvd-type"]').forEach((radio) => {
  radio.addEventListener("change", updateButton);
});
severity.addEventListener("input", showSeverity);
button.addEventListener("click", enhance);
showSeverity();
updateButton();
