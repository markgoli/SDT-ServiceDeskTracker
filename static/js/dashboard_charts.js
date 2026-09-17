(function () {
  function readData(id) {
    const el = document.getElementById(id);
    return el ? JSON.parse(el.textContent) : null;
  }

  function truncate(text, max) {
    if (!text) return "";
    return text.length > max ? text.slice(0, max - 1) + "…" : text;
  }

  const statusData = readData("status-chart-data");
  const slaData = readData("sla-chart-data");
  const monthlyData = readData("monthly-chart-data");
  const weeklyData = readData("weekly-chart-data");
  const workloadData = readData("workload-chart-data");
  const technicianSlaData = readData("technician-sla-chart-data");
  const slaLifetimeData = readData("sla-lifetime-chart-data");
  const dueDatesData = readData("due-dates-chart-data");

  // Wall-display default: every chart shows its own values permanently
  // (no hover/click required to read the numbers).
  const barValueLabels = {
    color: "#101828",
    anchor: "end",
    align: "end",
    offset: 2,
    font: { weight: "700", size: 11 },
    formatter: (value) => value || "",
  };

  const statusCanvas = document.getElementById("statusChart");
  if (statusCanvas && statusData) {
    new Chart(statusCanvas, {
      type: "bar",
      data: {
        labels: statusData.labels,
        datasets: [{
          data: statusData.data,
          backgroundColor: statusData.colors,
          borderRadius: 5,
          maxBarThickness: 26,
        }],
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        layout: { padding: { right: 26 } },
        scales: {
          x: { beginAtZero: true, ticks: { precision: 0, font: { size: 10 } }, grid: { display: false } },
          y: { ticks: { font: { size: 11 } }, grid: { display: false } },
        },
        plugins: { legend: { display: false }, datalabels: barValueLabels },
      },
    });
  }

  const slaCanvas = document.getElementById("slaChart");
  if (slaCanvas && slaData) {
    new Chart(slaCanvas, {
      type: "doughnut",
      data: {
        labels: slaData.labels,
        datasets: [{ data: slaData.data, backgroundColor: slaData.colors, borderWidth: 0 }],
      },
      options: {
        cutout: "50%",
        responsive: true,
        maintainAspectRatio: false,
        layout: { padding: 12 },
        plugins: {
          legend: { position: "bottom", labels: { boxWidth: 9, font: { size: 10.5 } } },
          datalabels: {
            color: "#fff",
            font: { weight: "700", size: 12 },
            textAlign: "center",
            formatter: (value, ctx) => {
              if (!value) return "";
              const total = ctx.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
              const pct = total ? Math.round((value / total) * 100) : 0;
              return [String(value), `${pct}%`];
            },
          },
        },
      },
    });
  }

  const monthlyCanvas = document.getElementById("monthlyChart");
  if (monthlyCanvas && monthlyData && monthlyData.labels.length) {
    new Chart(monthlyCanvas, {
      type: "bar",
      data: {
        labels: monthlyData.labels,
        datasets: [
          { label: "Within SLA", data: monthlyData.within, backgroundColor: "#1fae5e", borderRadius: 4 },
          { label: "Outside SLA", data: monthlyData.outside, backgroundColor: "#f0453a", borderRadius: 4 },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { stacked: true, ticks: { font: { size: 10 } }, grid: { display: false } },
          y: { stacked: true, beginAtZero: true, ticks: { precision: 0, font: { size: 10 } } },
        },
        plugins: {
          legend: { position: "bottom", labels: { boxWidth: 9, font: { size: 10.5 } } },
          datalabels: {
            color: "#fff",
            font: { weight: "700", size: 10 },
            formatter: (value) => (value > 0 ? value : ""),
          },
        },
      },
    });
  }

  const weeklyCanvas = document.getElementById("weeklyChart");
  if (weeklyCanvas && weeklyData && weeklyData.labels.length) {
    new Chart(weeklyCanvas, {
      type: "bar",
      data: {
        labels: weeklyData.labels,
        datasets: [
          { label: "Within SLA", data: weeklyData.within, backgroundColor: "#1fae5e", borderRadius: 4 },
          { label: "Outside SLA", data: weeklyData.outside, backgroundColor: "#f0453a", borderRadius: 4 },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { stacked: true, ticks: { font: { size: 10 } }, grid: { display: false } },
          y: { stacked: true, beginAtZero: true, ticks: { precision: 0, font: { size: 10 } } },
        },
        plugins: {
          legend: { position: "bottom", labels: { boxWidth: 9, font: { size: 10.5 } } },
          datalabels: {
            color: "#fff",
            font: { weight: "700", size: 10 },
            formatter: (value) => (value > 0 ? value : ""),
          },
        },
      },
    });
  }

  const technicianSlaCanvas = document.getElementById("technicianSlaChart");
  if (technicianSlaCanvas && technicianSlaData && technicianSlaData.labels.length) {
    new Chart(technicianSlaCanvas, {
      type: "bar",
      data: {
        labels: technicianSlaData.labels,
        datasets: [
          { label: "Within SLA", data: technicianSlaData.within, backgroundColor: "#1fae5e", borderRadius: 4, maxBarThickness: 12 },
          { label: "Outside SLA", data: technicianSlaData.outside, backgroundColor: "#f0453a", borderRadius: 4, maxBarThickness: 12 },
        ],
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        layout: { padding: { right: 20 } },
        scales: {
          x: { beginAtZero: true, ticks: { precision: 0, font: { size: 10 } }, grid: { display: false } },
          y: { ticks: { font: { size: 10.5 } }, grid: { display: false } },
        },
        plugins: {
          legend: { position: "bottom", labels: { boxWidth: 9, font: { size: 10.5 } } },
          datalabels: {
            color: "#101828",
            anchor: "end",
            align: "end",
            offset: 2,
            font: { weight: "700", size: 9.5 },
            formatter: (value) => value || "",
          },
        },
      },
    });
  }

  const slaLifetimeCanvas = document.getElementById("slaLifetimeChart");
  if (slaLifetimeCanvas && slaLifetimeData && slaLifetimeData.labels.length) {
    new Chart(slaLifetimeCanvas, {
      type: "bar",
      data: {
        labels: slaLifetimeData.labels,
        datasets: [
          { label: "Within SLA", data: slaLifetimeData.within, backgroundColor: "#1fae5e", stack: "sla", maxBarThickness: 14 },
          { label: "Overdue", data: slaLifetimeData.over, backgroundColor: "#f0453a", stack: "sla", maxBarThickness: 14 },
        ],
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        layout: { padding: { right: 34 } },
        scales: {
          x: {
            stacked: true,
            beginAtZero: true,
            ticks: { precision: 0, font: { size: 10 } },
            grid: { display: false },
            title: { display: true, text: "Days elapsed since assignment", font: { size: 10.5 } },
          },
          y: { stacked: true, ticks: { font: { size: 10 } }, grid: { display: false } },
        },
        plugins: {
          legend: { position: "bottom", labels: { boxWidth: 9, font: { size: 10.5 } } },
          datalabels: {
            display: (ctx) => ctx.datasetIndex === 1,
            color: "#101828",
            anchor: "end",
            align: "end",
            offset: 2,
            font: { weight: "700", size: 10 },
            formatter: (value, ctx) => {
              const idx = ctx.dataIndex;
              const within = ctx.chart.data.datasets[0].data[idx];
              const total = within + value;
              return total > 0 ? `${total}d` : "";
            },
          },
        },
      },
    });
  }

  function dueDateColor(daysUntil) {
    if (daysUntil < 0) return "#f0453a";
    if (daysUntil === 0) return "#f5a623";
    return "#1fae5e";
  }

  function dueDateSuffix(daysUntil) {
    if (daysUntil < 0) return ` (${Math.abs(daysUntil)}d overdue)`;
    if (daysUntil === 0) return " (today)";
    return ` (in ${daysUntil}d)`;
  }

  const dueDatesCanvas = document.getElementById("dueDatesChart");
  if (dueDatesCanvas && dueDatesData && dueDatesData.labels.length) {
    const dueDatesColors = dueDatesData.data.map(dueDateColor);
    new Chart(dueDatesCanvas, {
      type: "bar",
      data: {
        labels: dueDatesData.labels,
        datasets: [{ data: dueDatesData.data, backgroundColor: dueDatesColors, borderRadius: 4, maxBarThickness: 14 }],
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        layout: { padding: { right: 90 } },
        scales: {
          x: { ticks: { precision: 0, font: { size: 10 } }, grid: { display: false } },
          y: { ticks: { font: { size: 10 } }, grid: { display: false } },
        },
        plugins: {
          legend: { display: false },
          datalabels: {
            color: "#101828",
            anchor: "end",
            align: "end",
            offset: 2,
            font: { weight: "700", size: 9.5 },
            formatter: (value, ctx) => {
              const idx = ctx.dataIndex;
              const label = dueDatesData.due_labels[idx];
              return `${label}${dueDateSuffix(value)}`;
            },
          },
        },
      },
    });
  }

  // --- Open Workload: click a bar for the full ticket list, hover for a preview ---
  function openWorkloadModal(technician, count, ticketList) {
    const overlay = document.getElementById("workload-modal-overlay");
    if (!overlay) return;

    document.getElementById("workload-modal-eyebrow").textContent =
      `${count} Open Request${count === 1 ? "" : "s"}`;
    document.getElementById("workload-modal-title").textContent = technician;

    const body = document.getElementById("workload-modal-body");
    body.innerHTML = "";
    if (!ticketList.length) {
      body.innerHTML = '<div class="empty-state">No open ticket details available.</div>';
    } else {
      ticketList.forEach((t) => {
        const row = document.createElement("div");
        row.className = "detail-row";
        row.innerHTML = '<span class="detail-label ref-id"></span><span class="detail-value"></span>';
        row.querySelector(".detail-label").textContent = t.ref;
        row.querySelector(".detail-value").textContent = t.system;
        body.appendChild(row);
      });
    }

    overlay.hidden = false;
    document.body.style.overflow = "hidden";
  }

  function closeWorkloadModal() {
    const overlay = document.getElementById("workload-modal-overlay");
    if (!overlay) return;
    overlay.hidden = true;
    document.body.style.overflow = "";
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.body.addEventListener("click", function (event) {
      if (
        event.target.closest("#workload-modal-close") ||
        event.target === document.getElementById("workload-modal-overlay")
      ) {
        closeWorkloadModal();
      }
    });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") closeWorkloadModal();
    });
  });

  const workloadCanvas = document.getElementById("workloadChart");
  if (workloadCanvas && workloadData && workloadData.labels.length) {
    new Chart(workloadCanvas, {
      type: "bar",
      data: {
        labels: workloadData.labels,
        datasets: [{ data: workloadData.data, backgroundColor: "#0055c6", borderRadius: 5, maxBarThickness: 26 }],
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        layout: { padding: { right: 26 } },
        onHover: (event, elements) => {
          event.native.target.style.cursor = elements.length ? "pointer" : "default";
        },
        onClick: (_event, elements) => {
          if (!elements.length) return;
          const idx = elements[0].index;
          const tickets = workloadData.tickets?.[idx] || [];
          openWorkloadModal(workloadData.labels[idx], workloadData.data[idx], tickets);
        },
        scales: {
          x: { beginAtZero: true, ticks: { precision: 0, font: { size: 10 } }, grid: { display: false } },
          y: { ticks: { font: { size: 11 } }, grid: { display: false } },
        },
        plugins: {
          legend: { display: false },
          datalabels: barValueLabels,
          tooltip: {
            callbacks: {
              title: (contexts) => contexts[0].label,
              label: (context) => {
                const idx = context.dataIndex;
                const count = workloadData.data[idx];
                const tickets = workloadData.tickets?.[idx] || [];
                if (!tickets.length) {
                  return `${count} Open Request${count === 1 ? "" : "s"}`;
                }
                const preview = tickets
                  .slice(0, 5)
                  .map((t) => `${t.ref} — ${truncate(t.system, 38)}`);
                const remaining = count - Math.min(5, tickets.length);
                if (remaining > 0) {
                  preview.push(`+${remaining} more — click bar for full list`);
                }
                return preview;
              },
            },
          },
        },
      },
    });
  }
})();
