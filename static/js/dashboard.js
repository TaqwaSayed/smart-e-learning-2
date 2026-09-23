(function () {
    // --- Sidebar tab switching ---
    const navItems = document.querySelectorAll('.dash-nav-item');
    const panels = document.querySelectorAll('.dash-panel');

    navItems.forEach((item) => {
        item.addEventListener('click', function () {
            navItems.forEach((n) => n.classList.remove('active'));
            panels.forEach((p) => p.classList.remove('active'));
            this.classList.add('active');
            document.getElementById(this.dataset.target).classList.add('active');
        });
    });

    // --- Instant task add (Enter key, no page reload) ---
    const taskInput = document.getElementById('task-input');
    const taskList = document.getElementById('task-list');
    const emptyMsg = document.getElementById('task-empty-msg');

    function getCsrfToken() {
        const match = document.cookie.match(/csrftoken=([^;]+)/);
        return match ? match[1] : '';
    }

    function buildTaskItem(task) {
        const li = document.createElement('li');
        li.className = 'task-item';
        li.dataset.taskId = task.id;
        li.innerHTML = `
            <button type="button" class="task-checkbox"></button>
            <span class="task-text">${task.text}</span>
        `;
        attachToggleHandler(li.querySelector('.task-checkbox'), task.id);
        return li;
    }

    function attachToggleHandler(button, taskId) {
        button.addEventListener('click', function () {
            fetch(`/tasks/${taskId}/toggle/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                    'X-Requested-With': 'fetch',
                },
            })
            .then((r) => r.json())
            .then((data) => {
                const li = button.closest('.task-item');
                const textSpan = li.querySelector('.task-text');
                if (data.is_done) {
                    button.classList.add('checked');
                    button.innerHTML = '<i class="bi bi-check-lg"></i>';
                    textSpan.classList.add('done');
                } else {
                    button.classList.remove('checked');
                    button.innerHTML = '';
                    textSpan.classList.remove('done');
                }
                const pointsEl = document.getElementById('header-points');
                if (pointsEl && typeof data.points === 'number') {
                    pointsEl.textContent = data.points;
                }
            });
        });
    }

    // Wire up checkboxes already rendered server-side on page load.
    document.querySelectorAll('.task-item .task-checkbox').forEach((btn) => {
        const taskId = btn.closest('.task-item').dataset.taskId;
        attachToggleHandler(btn, taskId);
    });

    if (taskInput) {
        taskInput.addEventListener('keydown', function (e) {
            if (e.key !== 'Enter') return;
            const text = taskInput.value.trim();
            if (!text) return;

            fetch(window.DASH_URLS.taskCreate, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': getCsrfToken(),
                    'X-Requested-With': 'fetch',
                },
                body: `text=${encodeURIComponent(text)}`,
            })
            .then((r) => r.json())
            .then((data) => {
                if (data.error) return;
                if (emptyMsg) emptyMsg.style.display = 'none';
                taskList.appendChild(buildTaskItem(data));
                taskInput.value = '';
            });
        });
    }
})();
