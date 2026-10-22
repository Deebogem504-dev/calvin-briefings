(function () {
  var root = document.documentElement;
  var key = "calvin-theme";
  var stored = null;
  try {
    stored = localStorage.getItem(key);
  } catch (err) {
    stored = null;
  }
  if (stored === "light" || stored === "dark") {
    root.setAttribute("data-theme", stored);
  }

  var button = document.getElementById("theme-toggle");
  if (!button) return;

  function mode() {
    var set = root.getAttribute("data-theme");
    if (set === "light" || set === "dark") return set;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  function paint() {
    var dark = mode() === "dark";
    button.setAttribute("aria-pressed", dark ? "true" : "false");
    button.textContent = dark ? "Light" : "Dark";
  }

  paint();
  button.addEventListener("click", function () {
    var next = mode() === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", next);
    try {
      localStorage.setItem(key, next);
    } catch (err) {
      /* private mode */
    }
    paint();
  });
})();
