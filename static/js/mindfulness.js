(function () {
    const POMODORO_MS = 25 * 60 * 1000;

    function showMindfulnessPopup(phase) {
        fetch(`/mindfulness/popup/?phase=${phase}`)
            .then((r) => r.json())
            .then((data) => {
                const overlay = document.getElementById('mindfulness-overlay');
                if (!overlay) return;

                const img = document.getElementById('mindfulness-image');
                const textEl = document.getElementById('mindfulness-text');
                const sourceEl = document.getElementById('mindfulness-source');

                if (data.image_url) {
                    img.src = data.image_url;
                    img.style.display = 'block';
                } else {
                    img.style.display = 'none';
                    img.removeAttribute('src');
                }

                textEl.textContent = data.text || '';
                textEl.style.display = data.text ? 'block' : 'none';
                sourceEl.textContent = data.source || '';
                sourceEl.style.display = data.source ? 'block' : 'none';

                overlay.classList.add('show');
            })
            .catch((err) => console.error('mindfulness fetch failed', err));
    }

    function closeMindfulnessPopup() {
        const overlay = document.getElementById('mindfulness-overlay');
        if (overlay) overlay.classList.remove('show');
    }

    document.addEventListener('DOMContentLoaded', function () {
        const closeBtn = document.getElementById('mindfulness-close');
        if (closeBtn) closeBtn.addEventListener('click', closeMindfulnessPopup);

        if (document.body.dataset.pomodoro === 'on') {
            setInterval(() => showMindfulnessPopup('BREAK'), POMODORO_MS);
        }
    });

    window.showMindfulnessPopup = showMindfulnessPopup;
})();