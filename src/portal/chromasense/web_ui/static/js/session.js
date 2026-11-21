// End the session when the page closes, so the server deletes this browser's images.
window.addEventListener("pagehide", () => {
  navigator.sendBeacon("/api/session/end");
});
