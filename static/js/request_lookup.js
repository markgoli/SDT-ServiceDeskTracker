(function () {
  function showError(message) {
    const toast = document.getElementById("toast");
    if (!toast) return;
    toast.textContent = message;
    toast.className = "toast show toast-error";
    setTimeout(() => toast.classList.remove("show"), 3500);
  }

  function openLookupModal(requestId, subject, sections) {
    const overlay = document.getElementById("lookup-modal-overlay");
    if (!overlay) return;

    document.getElementById("lookup-modal-ref").textContent = `Request #${requestId}`;
    document.getElementById("lookup-modal-title").textContent = subject || "Request Details";

    const body = document.getElementById("lookup-modal-body");
    body.innerHTML = "";

    sections.forEach((section) => {
      const heading = document.createElement("div");
      heading.className = "modal-section-label";
      heading.textContent = section.label;
      body.appendChild(heading);

      section.rows.forEach((row) => {
        if (row.block) {
          const block = document.createElement("div");
          block.className = "detail-block";
          block.innerHTML = '<div class="detail-label"></div><div class="detail-block-text"></div>';
          block.querySelector(".detail-label").textContent = row.label;
          block.querySelector(".detail-block-text").textContent = row.value;
          body.appendChild(block);
          return;
        }
        const line = document.createElement("div");
        line.className = "detail-row";
        line.innerHTML = '<span class="detail-label"></span><span class="detail-value"></span>';
        line.querySelector(".detail-label").textContent = row.label;
        line.querySelector(".detail-value").textContent = row.value;
        body.appendChild(line);
      });
    });

    overlay.hidden = false;
    document.body.style.overflow = "hidden";
  }

  function closeLookupModal() {
    const overlay = document.getElementById("lookup-modal-overlay");
    if (!overlay) return;
    overlay.hidden = true;
    document.body.style.overflow = "";
  }

  function runLookup() {
    const input = document.getElementById("lookup-input");
    const btn = document.getElementById("lookup-btn");
    if (!input || !btn) return;

    const id = input.value.trim();
    if (!id) return;

    btn.disabled = true;
    btn.classList.add("is-loading");

    fetch(`${window.REQUEST_LOOKUP_URL}?id=${encodeURIComponent(id)}`)
      .then((res) => res.json().then((data) => ({ ok: res.ok, data })))
      .then(({ ok, data }) => {
        if (ok && data.success) {
          openLookupModal(data.request_id, data.subject, data.sections);
        } else {
          showError(data.message || "Lookup failed.");
        }
      })
      .catch((err) => showError(String(err)))
      .finally(() => {
        btn.disabled = false;
        btn.classList.remove("is-loading");
      });
  }

  document.addEventListener("DOMContentLoaded", function () {
    const btn = document.getElementById("lookup-btn");
    const input = document.getElementById("lookup-input");

    if (btn) btn.addEventListener("click", runLookup);
    if (input) {
      input.addEventListener("keydown", (event) => {
        if (event.key === "Enter") runLookup();
      });
    }

    document.body.addEventListener("click", function (event) {
      if (
        event.target.closest("#lookup-modal-close") ||
        event.target === document.getElementById("lookup-modal-overlay")
      ) {
        closeLookupModal();
      }
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") closeLookupModal();
    });
  });
})();
