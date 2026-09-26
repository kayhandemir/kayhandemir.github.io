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
