/* ═══════════════════════════════════════════════════════════
   TWINSENTRIX — MAIN JAVASCRIPT
   - Canvas particle network (hero background)
   - GSAP + ScrollTrigger animations
   - Animated stat counters
   - Navbar scroll behavior
   - Mobile menu toggle
   - Active nav link tracking
   - Contact form feedback
   ═══════════════════════════════════════════════════════════ */

gsap.registerPlugin(ScrollTrigger);

/* ─── HERO CANVAS — Particle Network ─────────────────────── */
(function initCanvas() {
  const canvas = document.getElementById('heroCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  let W, H, particles;
  const TEAL = 'rgba(0, 168, 198,';
  const PARTICLE_COUNT = 0;
  const MAX_DIST = 140;

  function resize() {
    W = canvas.width  = canvas.offsetWidth;
    H = canvas.height = canvas.offsetHeight;
  }

  function rand(min, max) { return Math.random() * (max - min) + min; }

  function createParticles() {
    particles = Array.from({ length: PARTICLE_COUNT }, () => ({
      x:  rand(0, W),
      y:  rand(0, H),
      vx: rand(-0.3, 0.3),
      vy: rand(-0.3, 0.3),
      r:  rand(1.2, 2.2),
    }));
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);

    // Draw connections
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < MAX_DIST) {
          const alpha = (1 - dist / MAX_DIST) * 0.18;
          ctx.beginPath();
          ctx.strokeStyle = TEAL + alpha + ')';
          ctx.lineWidth = 0.8;
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.stroke();
        }
      }
    }

    // Draw particles
    particles.forEach(p => {
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = TEAL + '0.35)';
      ctx.fill();
    });
  }

  function update() {
    particles.forEach(p => {
      p.x += p.vx;
      p.y += p.vy;
      if (p.x < 0 || p.x > W) p.vx *= -1;
      if (p.y < 0 || p.y > H) p.vy *= -1;
    });
  }

  function loop() {
    update();
    draw();
    requestAnimationFrame(loop);
  }

  window.addEventListener('resize', () => { resize(); createParticles(); });
  resize();
  createParticles();
  loop();
})();


/* ─── NAVBAR SCROLL ───────────────────────────────────────── */
const navbar = document.getElementById('navbar');
window.addEventListener('scroll', () => {
  navbar.classList.toggle('scrolled', window.scrollY > 60);
}, { passive: true });


/* ─── MOBILE MENU ─────────────────────────────────────────── */
const hamburger   = document.getElementById('hamburger');
const mobileMenu  = document.getElementById('mobileMenu');
const mobileClose = document.getElementById('mobileClose');
const mobileLinks = document.querySelectorAll('.mobile-link');

function openMenu() {
  mobileMenu.classList.add('open');
  hamburger.classList.add('open');
  document.body.style.overflow = 'hidden';
}
function closeMenu() {
  mobileMenu.classList.remove('open');
  hamburger.classList.remove('open');
  document.body.style.overflow = '';
}

hamburger.addEventListener('click', () => {
  mobileMenu.classList.contains('open') ? closeMenu() : openMenu();
});
mobileClose.addEventListener('click', closeMenu);
mobileLinks.forEach(l => l.addEventListener('click', closeMenu));


/* ─── HERO ENTRANCE ANIMATIONS ───────────────────────────── */
const heroTL = gsap.timeline({ defaults: { ease: 'power3.out' } });
heroTL
  .to('.hero-label',       { opacity: 1, duration: 0.9, delay: 0.4 })
  .to('.hero-title .word', { opacity: 1, y: 0, duration: 0.85, stagger: 0.18 }, '-=0.4')
  .to('.hero-sub',         { opacity: 1, y: 0, duration: 0.75 }, '-=0.35')
  .to('.hero-ctas',        { opacity: 1, y: 0, duration: 0.65 }, '-=0.3')
  .to('.hero-scroll-hint', { opacity: 1, duration: 0.6 }, '-=0.15');


/* ─── GENERIC SCROLL REVEALS (.reveal) ───────────────────── */
gsap.utils.toArray('.reveal').forEach(el => {
  gsap.to(el, {
    opacity: 1, y: 0,
    duration: 0.85,
    ease: 'power2.out',
    scrollTrigger: {
      trigger: el,
      start: 'top 88%',
      toggleActions: 'play none none none',
    },
  });
});


/* ─── REVEAL LEFT / RIGHT ─────────────────────────────────── */
gsap.utils.toArray('.reveal-left').forEach(el => {
  gsap.to(el, {
    opacity: 1, x: 0,
    duration: 0.95,
    ease: 'power2.out',
    scrollTrigger: { trigger: el, start: 'top 82%', toggleActions: 'play none none none' },
  });
});

gsap.utils.toArray('.reveal-right').forEach(el => {
  gsap.to(el, {
    opacity: 1, x: 0,
    duration: 0.95,
    ease: 'power2.out',
    scrollTrigger: { trigger: el, start: 'top 82%', toggleActions: 'play none none none' },
  });
});


/* ─── STAGGERED CARD GROUPS ───────────────────────────────── */
[
  { grid: '.stats-grid',   cards: '.stat-card'   },
  { grid: '.why-grid',     cards: '.why-card'    },
  { grid: '.market-grid',  cards: '.market-card' },
  { grid: '.team-grid',    cards: '.team-card'   },
].forEach(({ grid, cards }) => {
  const container = document.querySelector(grid);
  if (!container) return;
  const els = container.querySelectorAll(cards);
  gsap.to(els, {
    opacity: 1, y: 0,
    duration: 0.7,
    stagger: 0.1,
    ease: 'power2.out',
    scrollTrigger: {
      trigger: container,
      start: 'top 82%',
      toggleActions: 'play none none none',
    },
  });
});


/* ─── SOLUTION NUMBER PARALLAX ────────────────────────────── */
gsap.utils.toArray('.solution-num').forEach(num => {
  gsap.to(num, {
    yPercent: 25,
    ease: 'none',
    scrollTrigger: {
      trigger: num,
      start: 'top bottom',
      end: 'bottom top',
      scrub: true,
    },
  });
});


/* ─── ANIMATED STAT COUNTERS ─────────────────────────────── */
document.querySelectorAll('.stat-number').forEach(el => {
  const target  = parseFloat(el.dataset.target);
  const suffix  = el.dataset.suffix  || '';
  const prefix  = el.dataset.prefix  || '';
  const decimal = target % 1 !== 0;

  ScrollTrigger.create({
    trigger: el,
    start: 'top 88%',
    once: true,
    onEnter() {
      gsap.to({ val: 0 }, {
        val: target,
        duration: 2.2,
        ease: 'power2.out',
        onUpdate() {
          const v = this.targets()[0].val;
          el.textContent = prefix + (decimal ? v.toFixed(1) : Math.round(v)) + suffix;
        },
      });
    },
  });
});


/* ─── ACTIVE NAV LINK ─────────────────────────────────────── */
const navLinks = document.querySelectorAll('.nav-links a');
const sections = document.querySelectorAll('section[id]');

const sectionObserver = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const id = entry.target.getAttribute('id');
      navLinks.forEach(a => {
        a.classList.toggle('active', a.getAttribute('href') === `#${id}`);
      });
    }
  });
}, { threshold: 0.35 });

sections.forEach(s => sectionObserver.observe(s));


/* ─── SMOOTH SCROLL ───────────────────────────────────────── */
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    const target = document.querySelector(this.getAttribute('href'));
    if (target) {
      e.preventDefault();
      const offset = navbar.offsetHeight;
      const top = target.getBoundingClientRect().top + window.scrollY - offset;
      window.scrollTo({ top, behavior: 'smooth' });
    }
  });
});


/* ─── CONTACT FORM ────────────────────────────────────────── */
const contactForm = document.getElementById('contactForm');
if (contactForm) {
  contactForm.addEventListener('submit', e => {
    e.preventDefault();
    const btn = contactForm.querySelector('button[type="submit"]');
    const orig = btn.textContent;

    btn.textContent  = '✓ Request received — we\'ll be in touch soon!';
    btn.style.background = '#0d6e5e';
    btn.disabled = true;

    gsap.from(btn, { scale: 0.97, duration: 0.3, ease: 'back.out(1.7)' });

    setTimeout(() => {
      btn.textContent  = orig;
      btn.style.background = '';
      btn.disabled = false;
      contactForm.reset();
    }, 5000);
  });
}


/* ─── VISUAL CARD HOVER GLOW ──────────────────────────────── */
document.querySelectorAll('.visual-card').forEach(card => {
  card.addEventListener('mousemove', e => {
    const rect = card.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width  * 100).toFixed(1);
    const y = ((e.clientY - rect.top)  / rect.height * 100).toFixed(1);
    card.style.background = `radial-gradient(circle at ${x}% ${y}%, #132040 0%, #0F1A2E 55%)`;
  });
  card.addEventListener('mouseleave', () => {
    card.style.background = '';
  });
});
