(function () {
  const el = document.getElementById("app-config-data");
  if (!el) return;
  const config = JSON.parse(el.textContent);
  window.REFRESH_URL = config.refreshUrl;
  window.REQUEST_LOOKUP_URL = config.requestLookupUrl;
  window.AUTO_REFRESH_MINUTES = config.autoRefreshMinutes;
})();
