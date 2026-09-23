(function () {
    const fab = document.getElementById('ai-fab');
    const panel = document.getElementById('ai-chat-panel');
    const closeBtn = document.getElementById('ai-chat-close');
    const form = document.getElementById('ai-chat-form');
    const input = document.getElementById('ai-chat-input');
    const messages = document.getElementById('ai-chat-messages');
    const typing = document.getElementById('ai-chat-typing');
    const navLink = document.getElementById('ai-tutor-nav-link');

    if (!fab || !panel || !form) return;

    let sessionId = null;
    let open = false;

    function setOpen(next) {
        open = next;
        panel.classList.toggle('open', open);
        fab.classList.toggle('active', open);
        if (open) {
            input.focus();
            messages.scrollTop = messages.scrollHeight;
        }
    }

    fab.addEventListener('click', () => setOpen(!open));
    closeBtn.addEventListener('click', () => setOpen(false));

    // The old full-page "AI Tutor" nav link now opens the same floating
    // panel instead of navigating away — it still has a real href to
    // /chat/, so it degrades gracefully if JS is disabled.
    if (navLink) {
        navLink.addEventListener('click', (e) => {
            e.preventDefault();
            setOpen(true);
        });
    }

    function appendMessage(text, sender) {
        const row = document.createElement('div');
        row.className = 'ai-msg ' + (sender === 'USER' ? 'ai-msg-user' : 'ai-msg-bot');
        const avatar = document.createElement('span');
        avatar.className = 'ai-msg-avatar';
        avatar.textContent = sender === 'USER' ? '🧑‍🎓' : '🤖';
        const bubble = document.createElement('span');
        bubble.className = 'ai-msg-bubble';
        bubble.textContent = text;
        row.appendChild(avatar);
        row.appendChild(bubble);
        messages.appendChild(row);
        messages.scrollTop = messages.scrollHeight;
    }

    form.addEventListener('submit', function (e) {
        e.preventDefault();
        const message = input.value.trim();
        if (!message) return;

        appendMessage(message, 'USER');
        input.value = '';
        typing.style.display = 'flex';
        messages.scrollTop = messages.scrollHeight;

        fetch(window.AI_TUTOR.sendUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.AI_TUTOR.csrfToken,
            },
            body: JSON.stringify({ message, session_id: sessionId }),
        })
        .then((r) => r.json())
        .then((data) => {
            sessionId = data.session_id;
            typing.style.display = 'none';
            appendMessage(data.reply, 'AI');
        })
        .catch(() => {
            typing.style.display = 'none';
            appendMessage("Sorry, something went wrong. Please try again.", 'AI');
        });
    });
})();
