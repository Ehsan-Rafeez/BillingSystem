(function () {
  "use strict";

  function addToggle(input) {
    if (!input || input.dataset.passwordToggleReady === "true") return;

    input.dataset.passwordToggleReady = "true";
    var button = document.createElement("button");
    button.type = "button";
    button.className = "button shop-owner-password-toggle";
    button.textContent = "Show";
    button.style.marginLeft = "8px";
    button.addEventListener("click", function () {
      var visible = input.type === "text";
      input.type = visible ? "password" : "text";
      button.textContent = visible ? "Show" : "Hide";
    });
    input.insertAdjacentElement("afterend", button);
  }

  function init() {
    document.querySelectorAll("input.shop-owner-password").forEach(addToggle);
  }

  document.addEventListener("DOMContentLoaded", init);
})();
