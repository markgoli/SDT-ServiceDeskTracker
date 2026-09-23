(function () {
  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".lifetime-bar-cover[data-remaining]").forEach((el) => {
      el.style.width = el.dataset.remaining + "%";
    });
  });
})();
