var GUMROAD_URL = "https://arkitekture3.gumroad.com/l/mgfjd";
document.querySelectorAll("[data-gumroad]").forEach(function (el) {
  el.href = GUMROAD_URL;
  el.setAttribute("data-gumroad-url", GUMROAD_URL);
  if (/^https?:\/\//i.test(GUMROAD_URL)) {
    el.target = "_blank";
    el.rel = "noopener noreferrer";
  }
});
