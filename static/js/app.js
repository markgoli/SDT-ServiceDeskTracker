(function () {
  function getCookie(name) {
    const match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
    return match ? decodeURIComponent(match[2]) : null;
  }

  function showToast(message, isError) {
    const toast = document.getElementById("toast");
    if (!toast) return;
    toast.textContent = message;
    toast.className = "toast show " + (isError ? "toast-error" : "toast-ok");
    setTimeout(() => toast.classList.remove("show"), 3500);
  }

  function refreshData(reason) {
    const btn = document.getElementById("refresh-btn");
    if (btn) {
      btn.disabled = true;
      btn.classList.add("is-loading");
    }

    fetch(window.REFRESH_URL, {
      method: "POST",
      headers: { "X-CSRFToken": getCookie("csrftoken") },
    })
      .then((res) => res.json().then((data) => ({ ok: res.ok, data })))
      .then(({ ok, data }) => {
        if (ok && data.success) {
          showToast(`Synced ${data.rows_read} row(s) — ${data.created} new, ${data.updated} updated.`, false);
          setTimeout(() => window.location.reload(), 900);
        } else {
          showToast("Refresh failed: " + (data.message || "unknown error"), true);
          if (btn) {
            btn.disabled = false;
            btn.classList.remove("is-loading");
          }
        }
      })
      .catch((err) => {
        showToast("Refresh failed: " + err, true);
        if (btn) {
          btn.disabled = false;
          btn.classList.remove("is-loading");
        }
      });
  }

  document.addEventListener("DOMContentLoaded", function () {
    const btn = document.getElementById("refresh-btn");
    if (btn) {
      btn.addEventListener("click", () => refreshData("manual"));
    }

    const minutes = parseInt(window.AUTO_REFRESH_MINUTES, 10);
    if (minutes > 0) {
      setInterval(() => refreshData("auto"), minutes * 60 * 1000);
    }
  });
})();
