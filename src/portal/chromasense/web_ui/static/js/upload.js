// Step 1: send the chosen file to the server and show the original image it returns.
// The browser does no pixel work. Keyboard focus stays on the file input.
import { setStatus } from "./status.js";

const input = document.getElementById("file-input");
const section = document.getElementById("original-section");
const image = document.getElementById("original-image");
const caption = document.getElementById("original-caption");

async function errorMessage(response) {
  try {
    const body = await response.json();
    if (body && body.message) return body.message;
  } catch {
    // Fall through to the generic message.
  }
  return "The upload could not be completed. Try again.";
}

async function upload() {
  const file = input.files && input.files[0];
  if (!file) return;

  setStatus(`sending ${file.name}.`, "info", "Uploading");
  const form = new FormData();
  form.append("file", file);

  let response;
  try {
    response = await fetch("/api/image", { method: "POST", body: form });
  } catch {
    setStatus("The upload did not reach the server. Try again.", "error");
    return;
  }
  if (response.status !== 201) {
    // Keep any earlier original on screen.
    setStatus(await errorMessage(response), "error");
    return;
  }

  const { width, height } = await response.json();
  image.src = `/api/image/view/original?v=${Date.now()}`;
  image.width = width;
  image.height = height;
  caption.textContent = `${file.name}, ${width} by ${height} pixels.`;
  section.hidden = false;
  setStatus(`Image uploaded, ${width} by ${height} pixels.`, "success");
  document.dispatchEvent(new CustomEvent("chromasense:uploaded", { detail: { width, height } }));
}

input.addEventListener("change", upload);
