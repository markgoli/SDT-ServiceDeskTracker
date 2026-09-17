(function () {
  function formatRelative(date) {
    const seconds = Math.round((Date.now() - date.getTime()) / 1000);
    if (seconds < 45) return "just now";
    const minutes = Math.round(seconds / 60);
    if (minutes < 60) return `${minutes} minute${minutes === 1 ? "" : "s"} ago`;
    const hours = Math.round(minutes / 60);
    if (hours < 24) return `${hours} hour${hours === 1 ? "" : "s"} ago`;
    const days = Math.round(hours / 24);
    return `${days} day${days === 1 ? "" : "s"} ago`;
  }

  function tick() {
    const el = document.getElementById("last-synced-relative");
    if (!el) return;
    const timestamp = el.getAttribute("data-timestamp");
    if (!timestamp) return;
    el.textContent = formatRelative(new Date(timestamp));
  }

  document.addEventListener("DOMContentLoaded", function () {
    tick();
    setInterval(tick, 30000);
  });
})();
