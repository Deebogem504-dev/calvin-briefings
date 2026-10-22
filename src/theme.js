(function () {
  var root = document.documentElement;
  var key = "calvin-theme";
  var stored = null;
  try {
    stored = localStorage.getItem(key);
  } catch (err) {
    stored = null;
  }
  /* Dark olive is the default even when the system theme is light.
     A stored "light" or "dark" value is an explicit visitor choice. */
  if (stored === "light" || stored === "dark") {
    root.setAttribute("data-theme", stored);
  } else {
    root.setAttribute("data-theme", "dark");
  }

  var button = document.getElementById("theme-toggle");
  if (!button) return;

  function mode() {
    return root.getAttribute("data-theme") === "light" ? "light" : "dark";
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
