(function () {
    "use strict";

    let toastEl = null;
    let toastTimer = null;

    function getToast() {
        if (toastEl) return toastEl;
        toastEl = document.createElement("div");
        toastEl.className = "kk-toast";
        toastEl.setAttribute("role", "status");
        toastEl.setAttribute("aria-live", "polite");
        document.body.appendChild(toastEl);
        return toastEl;
    }

    function showToast(message) {
        const t = getToast();
        t.textContent = message;
        t.classList.add("kk-show");
        if (toastTimer) clearTimeout(toastTimer);
        toastTimer = setTimeout(function () {
            t.classList.remove("kk-show");
        }, 1500);
    }

    function flashButton(btn) {
        btn.classList.add("kk-copied");
        const original = btn.textContent;
        btn.textContent = "Skopiowano!";
        setTimeout(function () {
            btn.classList.remove("kk-copied");
            btn.textContent = original;
        }, 1500);
    }

    document.addEventListener("click", function (e) {
        const btn = e.target.closest("[data-copy-text]");
        if (!btn) return;
        e.preventDefault();
        const text = btn.dataset.copyText || "";
        if (!navigator.clipboard) {
            showToast("Clipboard niedostępny");
            return;
        }
        navigator.clipboard.writeText(text).then(function () {
            flashButton(btn);
            showToast("Skopiowano!");
        }).catch(function () {
            showToast("Błąd kopiowania");
        });
    });
})();
