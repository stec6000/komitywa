(function () {
    "use strict";

    var reduceMotionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");

    // Homepage motion: content stays visible by default; JS only activates the
    // authored entrance and one-time line drawing when motion is welcome.
    var revealItems = document.querySelectorAll("[data-kk-reveal]");
    if (!reduceMotionQuery.matches && revealItems.length) {
        document.documentElement.classList.add("kk-motion-ready");

        if ("IntersectionObserver" in window) {
            var revealObserver = new IntersectionObserver(function (entries, observer) {
                entries.forEach(function (entry) {
                    if (!entry.isIntersecting) return;
                    entry.target.classList.add("is-visible");
                    observer.unobserve(entry.target);
                });
            }, {
                rootMargin: "0px 0px -10% 0px",
                threshold: 0.12
            });

            revealItems.forEach(function (item) {
                revealObserver.observe(item);
            });
        } else {
            revealItems.forEach(function (item) {
                item.classList.add("is-visible");
            });
        }
    }

    // Mobile nav toggle
    var toggle = document.querySelector(".nav-toggle");
    var links = document.getElementById("mainNav");
    if (toggle && links) {
        function closeMenu(restoreFocus) {
            links.classList.remove("open");
            toggle.setAttribute("aria-expanded", "false");
            if (restoreFocus) toggle.focus();
        }

        toggle.addEventListener("click", function () {
            var open = links.classList.toggle("open");
            toggle.setAttribute("aria-expanded", open ? "true" : "false");
        });

        document.addEventListener("click", function (e) {
            if (!links.contains(e.target) && !toggle.contains(e.target)) {
                closeMenu(false);
            }
        });

        document.addEventListener("keydown", function (e) {
            if (e.key === "Escape" && links.classList.contains("open")) {
                closeMenu(true);
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
            target.scrollIntoView({ behavior: reduceMotionQuery.matches ? "auto" : "smooth", block: "start" });
        });
    });
})();
