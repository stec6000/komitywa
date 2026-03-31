(function() {
    "use strict";

    var CONSENT_KEY = "cookie_consent";
    var consent = localStorage.getItem(CONSENT_KEY);

    if (consent !== null) return;

    var banner = document.getElementById("cookie-banner");
    if (!banner) return;

    banner.style.display = "block";

    document.getElementById("cookie-accept").addEventListener("click", function() {
        localStorage.setItem(CONSENT_KEY, "accepted");
        banner.style.display = "none";
    });

    document.getElementById("cookie-reject").addEventListener("click", function() {
        localStorage.setItem(CONSENT_KEY, "rejected");
        banner.style.display = "none";
    });
})();
