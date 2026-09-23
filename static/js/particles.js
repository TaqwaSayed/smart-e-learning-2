/*
 * Animated "constellation" background: soft glowing green dots that drift
 * slowly and connect with faint lines when they're close to each other.
 * Runs on a full-screen <canvas id="particles-bg"> injected in base.html.
 * Pure canvas + JS, no external libraries, so it works inside the site's
 * existing CSP/library rules.
 */
(function () {
    const canvas = document.getElementById('particles-bg');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const GLOW_COLOR = '61, 220, 132';  // soft emerald green (r, g, b)
    const PARTICLE_COUNT = 70;
    const MAX_LINK_DISTANCE = 130;
    const SPEED = 0.25;

    let particles = [];
    let width, height;

    function resize() {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
    }

    function makeParticle() {
        return {
            x: Math.random() * width,
            y: Math.random() * height,
            vx: (Math.random() - 0.5) * SPEED,
            vy: (Math.random() - 0.5) * SPEED,
            r: Math.random() * 1.8 + 0.8,
        };
    }

    function init() {
        resize();
        particles = Array.from({ length: PARTICLE_COUNT }, makeParticle);
    }

    function step() {
        ctx.clearRect(0, 0, width, height);

        // Update + draw particles (glowing dots)
        particles.forEach((p) => {
            p.x += p.vx;
            p.y += p.vy;
            if (p.x < 0 || p.x > width) p.vx *= -1;
            if (p.y < 0 || p.y > height) p.vy *= -1;

            ctx.beginPath();
            ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(${GLOW_COLOR}, 0.85)`;
            ctx.shadowColor = `rgba(${GLOW_COLOR}, 0.9)`;
            ctx.shadowBlur = 8;
            ctx.fill();
        });
        ctx.shadowBlur = 0;

        // Connect nearby particles with faint lines
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < MAX_LINK_DISTANCE) {
                    const opacity = 0.18 * (1 - dist / MAX_LINK_DISTANCE);
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.strokeStyle = `rgba(${GLOW_COLOR}, ${opacity})`;
                    ctx.lineWidth = 1;
                    ctx.stroke();
                }
            }
        }

        requestAnimationFrame(step);
    }

    window.addEventListener('resize', resize);
    init();
    requestAnimationFrame(step);
})();
