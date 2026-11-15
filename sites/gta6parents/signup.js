(function () {
  var SB_URL = "https://ckauuurdpltrqjimjgbt.supabase.co";
  var SB_KEY = "sb_publishable_hPcyV-d9mcWJdcYO44Bavw_3bjgCn22";
  var SOURCE = "gta6-parents";
  var DONE = "tg_gta6_lead";
  var EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  var forms = document.querySelectorAll('form[data-signup="gta6-parents"]');
  if (!forms.length) return;

  function showSuccess(form, focus) {
    var fields = form.querySelector(".fields");
    var ok = form.querySelector(".ok");
    if (fields) fields.hidden = true;
    if (!ok) return;
    ok.hidden = false;
    if (focus) {
      var strong = ok.querySelector("p");
      if (strong) strong.focus();
    }
  }
  function say(form, text, bad) {
    var el = form.querySelector(".msg");
    if (!el) return;
    el.textContent = text || "";
    if (bad) el.setAttribute("data-state", "err");
    else el.removeAttribute("data-state");
  }
  function allSuccess() {
    forms.forEach(function (form) { showSuccess(form, false); });
  }
  function headers() {
    return {
      apikey: SB_KEY,
      Authorization: "Bearer " + SB_KEY,
      "Content-Type": "application/json",
      Prefer: "return=minimal"
    };
  }
  function joinExisting(email, name) {
    var body = { p_email: email };
    if (name) body.p_name = name;
    return fetch(SB_URL + "/rest/v1/rpc/signup_gta6_parent", {
      method: "POST",
      headers: {
        apikey: SB_KEY,
        Authorization: "Bearer " + SB_KEY,
        "Content-Type": "application/json"
      },
      body: JSON.stringify(body)
    }).then(function (r) {
      if (!r.ok) return { ok: false };
      return r.json().then(function (value) {
        return { ok: value === "created" || value === "queued" || value === "already" };
      }).catch(function () { return { ok: false }; });
    });
  }

  try { if (sessionStorage.getItem(DONE) === "1") allSuccess(); } catch (e) {}

  forms.forEach(function (form) {
    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var fd = new FormData(form);
      if (String(fd.get("company") || "").trim()) {
        try { sessionStorage.setItem(DONE, "1"); } catch (e) {}
        showSuccess(form, true);
        return;
      }
      var email = String(fd.get("email") || "").trim().toLowerCase();
      var name = String(fd.get("name") || "").trim();
      if (!email) return say(form, "Enter an email address.", true);
      if (email.length < 6 || email.length > 320 || !EMAIL.test(email)) return say(form, "That email doesn't look right.", true);
      if (name.length > 80) return say(form, "First name is too long.", true);
      var btn = form.querySelector("button[type=submit]");
      if (btn) { btn.disabled = true; btn.textContent = "Sending…"; }
      say(form, "", false);
      var row = { email: email, source: SOURCE };
      if (name) row.name = name;
      fetch(SB_URL + "/rest/v1/leads", {
        method: "POST",
        headers: headers(),
        body: JSON.stringify(row)
      }).then(function (r) {
        if (r.status === 201 || r.status === 204) return { ok: true };
        return r.json().catch(function () { return {}; }).then(function (j) {
          if (j && j.code === "23505") return joinExisting(email, name);
          return { ok: false };
        });
      }).then(function (res) {
        if (res && res.ok) {
          try { sessionStorage.setItem(DONE, "1"); } catch (e) {}
          allSuccess();
          showSuccess(form, true);
          return;
        }
        say(form, "That didn't go through. Try again in a minute.", true);
        if (btn) { btn.disabled = false; btn.textContent = "Get free updates"; }
      }).catch(function () {
        say(form, "That didn't go through. Try again in a minute.", true);
        if (btn) { btn.disabled = false; btn.textContent = "Get free updates"; }
      });
    });
  });
})();
