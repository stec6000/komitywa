(function () {
    "use strict";

    // Mobile nav toggle
    var toggle = document.querySelector(".nav-toggle");
    var links = document.getElementById("mainNav");
    if (toggle && links) {
        toggle.addEventListener("click", function () {
            var open = links.classList.toggle("open");
            toggle.setAttribute("aria-expanded", open ? "true" : "false");
        });

        document.addEventListener("click", function (e) {
            if (!links.contains(e.target) && !toggle.contains(e.target)) {
                links.classList.remove("open");
                toggle.setAttribute("aria-expanded", "false");
            }
        });
    }

    // Smooth-scroll for in-page anchors (#about, #recipes, #shop)
    document.querySelectorAll('a[href^="#"]').forEach(function (a) {
        var href = a.getAttribute("href");
        if (href.length < 2) return;
        var target = document.querySelector(href);
        if (!target) return;
        a.addEventListener("click", function (e) {
            e.preventDefault();
            target.scrollIntoView({ behavior: "smooth", block: "start" });
        });
    });
})();
