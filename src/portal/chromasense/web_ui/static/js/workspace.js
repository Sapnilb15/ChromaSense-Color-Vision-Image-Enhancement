import "./session.js";
import { resetResult, showResult } from "./compare.js";
import { setStatus } from "./status.js";

const byId = (id) => document.getElementById(id);
const stage = byId("stage");
const input = byId("file-input");
const original = byId("original-image");
const button = byId("enhance-button");
const severity = byId("severity");
const profile = document.querySelector(".profile");
const selected = () => profile.querySelector(":checked")?.value;
let hasImage = false;
let busy = false;

function syncControls() {
  button.disabled = !hasImage || !selected();
  button.setAttribute("aria-disabled", String(button.disabled || busy));
  input.setAttribute("aria-disabled", String(busy));
  profile.disabled = severity.disabled = busy;
  byId("enhance-hint").hidden = !button.disabled;
}

function showOriginal(available) {
  hasImage = available;
  resetResult();
  stage.classList.toggle("loaded", available);
  byId("empty-content").hidden = available;
  byId("original-section").hidden = !available;
  byId("picker-caption").textContent = available ? "Replace image" : "Browse files";
  byId("view-label").textContent = available ? "Original" : "Empty canvas";
  if (!available) original.removeAttribute("src");
}

async function request(action, fallback) {
  if (busy) return;
  busy = true;
  syncControls();
  try {
    await action();
  } catch (error) {
    setStatus(error instanceof RequestError ? error.message : fallback, "error");
  } finally {
    busy = false;
    syncControls();
  }
}

class RequestError extends Error {}

async function check(response, fallback) {
  if (response.ok) return;
  if (response.status === 404) showOriginal(false);
  const body = await response.json().catch(() => ({}));
  throw new RequestError(body.message || fallback);
}

function upload(file) {
  if (!file) return;
  request(async () => {
    setStatus(`sending ${file.name}.`, "info", "Uploading");
    showOriginal(hasImage);
    const form = new FormData();
    form.append("file", file);
    let response;
    try {
      response = await fetch("/api/image", { method: "POST", body: form });
    } catch (error) {
      showOriginal(false);
      throw error;
    }
    await check(response, "The upload could not be completed. Try again.");
    showOriginal(false);
    const { width, height } = await response.json();
    original.src = `/api/image/view/original?v=${Date.now()}`;
    await original.decode();
    byId("original-caption").textContent = `${file.name}, ${width} by ${height} pixels.`;
    byId("file-size").textContent = file.size < 1000 ? `${file.size} B` : `${(file.size / 1000).toLocaleString(undefined, { maximumFractionDigits: 1 })} kB`;
    showOriginal(true);
    setStatus(`Image uploaded, ${width} by ${height} pixels.`, "success");
  }, "The upload or preview could not be loaded. Choose the image again.");
}

input.addEventListener("click", (event) => { if (busy) event.preventDefault(); });
input.addEventListener("change", () => {
  upload(input.files[0]);
  input.value = "";
});
stage.addEventListener("dragover", (event) => {
  event.preventDefault();
  if (!busy) stage.classList.add("dragging");
});
stage.addEventListener("dragleave", (event) => {
  if (!stage.contains(event.relatedTarget)) stage.classList.remove("dragging");
});
stage.addEventListener("drop", (event) => {
  event.preventDefault();
  stage.classList.remove("dragging");
  if (busy) return;
  if (event.dataTransfer.files.length !== 1) return setStatus("Choose one image at a time.", "error");
  upload(event.dataTransfer.files[0]);
});

function updateSettings() {
  const percent = severity.value + "%";
  byId("severity-value").textContent = percent;
  severity.setAttribute("aria-valuetext", percent);
  if (!byId("compare-section").hidden) {
    showOriginal(true);
    setStatus("Settings changed. Enhance the image to compare again.", "success");
  }
  syncControls();
}
profile.addEventListener("change", updateSettings);
severity.addEventListener("input", updateSettings);
button.addEventListener("click", () => request(async () => {
  if (!hasImage || !selected()) return;
  const type = selected();
  const level = Number(severity.value) / 100;
  showOriginal(true);
  setStatus(`applying the ${type} profile at severity ${level}.`, "info", "Enhancing");
  const response = await fetch("/api/image/enhance", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ type, severity: level }),
  });
  await check(response, "Processing failed. Try enhancing the image again.");
  const result = await response.json();
  await showResult(result, type, level);
  setStatus(result.message, "success");
}, "Processing or preview failed. Try enhancing the image again."));

byId("download-link").addEventListener("click", (event) => {
  event.preventDefault();
  request(async () => {
    const response = await fetch("/api/image/export");
    await check(response, "The download could not be completed. Try again.");
    const link = document.createElement("a");
    link.href = URL.createObjectURL(await response.blob());
    link.download = response.headers.get("Content-Disposition")?.match(/filename="([^"]+)"/)?.[1] || "";
    link.click();
    setTimeout(() => URL.revokeObjectURL(link.href), 60000);
  }, "The download did not finish. Try again.");
});

document.querySelectorAll("[data-dialog]").forEach((trigger) => {
  trigger.addEventListener("click", () => byId(trigger.dataset.dialog).showModal());
});
const theme = byId("theme");
function applyTheme(light) {
  document.documentElement.dataset.theme = light ? "light" : "dark";
  theme.setAttribute("aria-pressed", String(light));
}
try {
  applyTheme(localStorage.getItem("theme") === "light");
} catch { applyTheme(false); }
theme.addEventListener("click", () => {
  applyTheme(theme.getAttribute("aria-pressed") !== "true");
  try { localStorage.setItem("theme", document.documentElement.dataset.theme); } catch { /* Storage is optional. */ }
});
updateSettings();
