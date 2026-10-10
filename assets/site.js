// Copy-email button in the contact section; falls back to selecting the address.
(function () {
  var button = document.getElementById("copy-email");
  if (!button) return;
  var label = button.textContent;
  button.addEventListener("click", function () {
    var email = button.getAttribute("data-email");
    var done = function () {
      button.textContent = button.getAttribute("data-done");
      setTimeout(function () { button.textContent = label; }, 2000);
    };
    var select = function () {
      var link = button.parentNode.querySelector("a");
      var range = document.createRange();
      range.selectNodeContents(link);
      var selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(email).then(done, select);
    } else {
      select();
    }
  });
})();

// Light / dark toggle. The page starts in the system theme; a click stores the visitor's choice.
(function () {
  var button = document.getElementById("theme-toggle");
  if (!button) return;
  var root = document.documentElement;
  var systemDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)");
  button.addEventListener("click", function () {
    var current = root.getAttribute("data-theme") || (systemDark && systemDark.matches ? "dark" : "light");
    var next = current === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", next);
    try { localStorage.setItem("ukg-theme", next); } catch (e) {}
  });
})();

// Contact form: posts to /api/contact (tools/server/contact_server.py) and shows the result under the button.
(function () {
  var form = document.getElementById("contact-form");
  if (!form || !window.fetch) return;
  var status = form.querySelector(".form-status");
  var button = form.querySelector("button[type=submit]");
  var say = function (key, isError) {
    status.textContent = form.getAttribute("data-" + key);
    status.className = "form-status" + (isError ? " is-error" : " is-ok");
  };
  form.addEventListener("submit", function (event) {
    event.preventDefault();
    var data = {};
    Array.prototype.forEach.call(form.elements, function (field) { if (field.name) data[field.name] = field.value; });
    if (!data.name.trim() || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(data.email.trim()) || data.message.trim().length < 5) {
      say("invalid", true);
      return;
    }
    button.disabled = true;
    say("sending", false);
    fetch(form.action, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) })
      .then(function (response) {
        if (response.ok) { form.reset(); say("sent", false); }
        else if (response.status === 429) { say("limited", true); }
        else if (response.status === 400) { say("invalid", true); }
        else { say("error", true); }
      })
      .catch(function () { say("error", true); })
      .then(function () { button.disabled = false; });
  });
})();
