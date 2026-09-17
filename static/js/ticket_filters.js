(function () {
  document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("filter-form");
    if (!form) return;

    const searchInput = form.querySelector('input[name="q"]');
    const selects = form.querySelectorAll("select");

    let debounceTimer;
    if (searchInput) {
      searchInput.addEventListener("input", function () {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => form.submit(), 450);
      });
    }

    selects.forEach((select) => {
      select.addEventListener("change", () => form.submit());
    });
  });
})();
