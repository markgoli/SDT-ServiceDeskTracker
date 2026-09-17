(function () {
  const SECTIONS = [
    {
      label: "Assignment",
      fields: [
        ["Technician", "technician"],
        ["Requester", "responsible"],
        ["Template", "template"],
      ],
    },
    {
      label: "SLA",
      fields: [
        ["SLA Policy", "slaPolicy"],
        ["SLA Due", "slaDue"],
        ["Days Open / Elapsed", "daysOpen"],
      ],
    },
    {
      label: "Approval",
      fields: [
        ["Approval Status", "approvalStatus"],
        ["Approved (observed)", "approved"],
        ["Approver 1", "approver1"],
        ["Approver 2", "approver2"],
        ["Team", "approvalTeam"],
      ],
    },
    {
      label: "Timeline",
      fields: [
        ["Created", "created"],
        ["Closed", "closed"],
        ["Last Synced", "lastSynced"],
      ],
    },
  ];

  function hexToRgba(hex, alpha) {
    const clean = (hex || "").replace("#", "");
    if (clean.length !== 6) return `rgba(102, 112, 133, ${alpha})`;
    const r = Number.parseInt(clean.slice(0, 2), 16);
    const g = Number.parseInt(clean.slice(2, 4), 16);
    const b = Number.parseInt(clean.slice(4, 6), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }

  function classBadge(className, text) {
    return `<span class="badge badge-${className}">${text}</span>`;
  }

  function colorBadge(hex, text) {
    const color = hex || "#0055c6";
    return `<span class="badge" style="background:${hexToRgba(color, 0.14)}; color:${color}">${text}</span>`;
  }

  function openModal(data) {
    const overlay = document.getElementById("detail-modal-overlay");
    if (!overlay) return;

    const modal = document.getElementById("detail-modal");
    modal.style.setProperty("--modal-accent", data.statusColor || "#0055c6");

    document.getElementById("detail-modal-ref").textContent = data.ref || "";
    document.getElementById("detail-modal-title").textContent = data.system || "";

    const badges = document.getElementById("detail-modal-badges");
    badges.innerHTML =
      (data.status ? colorBadge(data.statusColor, data.status) : "") +
      (data.slaState ? classBadge(data.slaStateKey, data.slaState) : "");

    const body = document.getElementById("detail-modal-body");
    body.innerHTML = "";

    SECTIONS.forEach((section) => {
      const rows = section.fields.filter(([, key]) => data[key]);
      if (!rows.length) return;

      const heading = document.createElement("div");
      heading.className = "modal-section-label";
      heading.textContent = section.label;
      body.appendChild(heading);

      rows.forEach(([label, key]) => {
        const row = document.createElement("div");
        row.className = "detail-row";
        row.innerHTML = `<span class="detail-label">${label}</span><span class="detail-value"></span>`;
        row.querySelector(".detail-value").textContent = data[key];
        body.appendChild(row);
      });
    });

    overlay.hidden = false;
    document.body.style.overflow = "hidden";
  }

  function closeModal() {
    const overlay = document.getElementById("detail-modal-overlay");
    if (!overlay) return;
    overlay.hidden = true;
    document.body.style.overflow = "";
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.body.addEventListener("click", function (event) {
      const trigger = event.target.closest("[data-modal-trigger]");
      if (trigger) {
        openModal(trigger.dataset);
        return;
      }
      if (event.target.closest("#detail-modal-close") || event.target === document.getElementById("detail-modal-overlay")) {
        closeModal();
      }
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") closeModal();
    });
  });
})();
