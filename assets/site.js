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

// Live ticker under the header: game facts, plus Bumper Brawl numbers from /api/stats (tools/server/stats_server.py)
// once there are any, refreshed every 30 seconds while the tab is visible. Without the stats it shows the facts alone.
(function () {
  var section = document.getElementById("live");
  if (!section) return;
  var texts = JSON.parse(section.getAttribute("data-texts"));
  var facts = texts.info || [];
  var track = section.querySelector(".live-items");
  var lang = document.documentElement.lang || "en";
  var reducedMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var shownKey = "";
  var pending = null;

  var num = function (n) { return Number(n).toLocaleString(lang); };
  var fill = function (key, values) {
    return texts[key].replace(/\{(\w+)\}/g, function (_, name) { return values[name]; });
  };
  var ago = function (seconds) {
    if (seconds < 60) return texts.now;
    if (seconds < 3600) return fill("min", { n: Math.floor(seconds / 60) });
    return fill("hour", { n: Math.floor(seconds / 3600) });
  };

  var items = function (stats) {
    var list = [];
    var today = stats.today, total = stats.total;
    if (stats.online > 0) {
      list.push(stats.online === 1 ? texts.online_one : fill("online", { n: num(stats.online) }));
      if (stats.in_match > 0) list.push(fill("in_match", { n: num(stats.in_match) }));
    }
    (stats.recent || []).slice(0, 3).forEach(function (r) {
      var when = " · " + ago(stats.now - r.t);
      if (r.e === "match_end" && r.m) list.push(fill("recent_match", { map: r.m, mode: r.g, n: num(r.n) }) + when);
      else if (r.e === "room_created") list.push(texts.recent_room + when);
    });
    if (today.matches > 0) list.push(fill("today_matches", { n: num(today.matches) }));
    if (today.rooms > 0) list.push(fill("today_rooms", { n: num(today.rooms) }));
    if (today.sessions > 0) list.push(fill("today_sessions", { n: num(today.sessions) }));
    if (today.top_map) list.push(fill("top_map", { map: today.top_map }));
    if (total.matches > 0) list.push(fill("total_matches", { n: num(total.matches) }));
    if (total.player_minutes >= 60) list.push(fill("total_hours", { n: num(Math.floor(total.player_minutes / 60)) }));
    if (total.peak_online > 1) list.push(fill("peak", { n: num(total.peak_online) }));
    var net = stats.net;
    if (net) {
      var mbps = net.mbps_in + net.mbps_out;
      if (mbps >= 0.01) list.push(fill("net_rate", { n: mbps.toLocaleString(lang, { maximumFractionDigits: 2 }) }));
      if (net.month_gb >= 1) list.push(fill("net_month", { n: num(Math.round(net.month_gb)) }));
    }
    return list;
  };

  var render = function (list) {
    track.textContent = "";
    // Two copies side by side, so the strip loops without a gap (the second is hidden from screen readers).
    for (var copy = 0; copy < (reducedMotion ? 1 : 2); copy++) {
      var group = document.createElement("span");
      group.className = "live-group";
      if (copy > 0) group.setAttribute("aria-hidden", "true");
      list.forEach(function (text) {
        var item = document.createElement("span");
        item.className = "live-item";
        item.textContent = text;
        group.appendChild(item);
      });
      track.appendChild(group);
    }
    // About 70 pixels a second, whatever the text length.
    track.style.animationDuration = Math.max(20, track.scrollWidth / 2 / 70) + "s";
  };

  // A new text waits until the strip has gone round once, so it doesn't jump mid-sentence.
  track.addEventListener("animationiteration", function () {
    if (pending) { render(pending); pending = null; }
  });

  var load = function () {
    if (document.hidden || !window.fetch) return;
    fetch("/api/stats", { cache: "no-store" })
      .then(function (response) { return response.ok ? response.json() : null; })
      .catch(function () { return null; })
      .then(function (stats) {
        var list = (stats ? items(stats) : []).concat(facts);
        var key = list.join("|");
        if (key === shownKey || !list.length) return;
        section.hidden = false;
        // The first text goes up at once; later changes wait for the strip to come round.
        if (!shownKey || reducedMotion) { render(list); pending = null; }
        else pending = list;
        shownKey = key;
      });
  };
  load();
  setInterval(load, 30000);
  document.addEventListener("visibilitychange", load);
})();
