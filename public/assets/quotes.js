// Home-page excerpt strip: one excerpt at a time, advancing every few seconds.
const root = document.querySelector('.qs');
if (root) {
  const slides = [...root.querySelectorAll('.qs-slide')];
  const num = root.querySelector('.qs-n');
  const pauseBtn = root.querySelector('.qs-pause');
  const ar = n => String(n).replace(/\d/g, d => '٠١٢٣٤٥٦٧٨٩'[d]);
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  let i = 0, timer = null, paused = reduced, hover = false;

  const show = k => {
    slides[i].hidden = true;
    i = (k + slides.length) % slides.length;
    slides[i].hidden = false;
    num.textContent = ar(i + 1);
  };
  const stop = () => { clearInterval(timer); timer = null; };
  const start = () => { stop(); if (!paused && !hover && slides.length > 1) timer = setInterval(() => show(i + 1), 9000); };
  const setPaused = p => {
    paused = p;
    pauseBtn.innerHTML = p ? '&#9654;' : '&#10073;&#10073;';
    pauseBtn.setAttribute('aria-label', p ? 'تشغيل التمرير' : 'إيقاف التمرير');
    start();
  };

  root.classList.add('qs-on');
  root.querySelector('.qs-next').addEventListener('click', () => { show(i + 1); start(); });
  root.querySelector('.qs-prev').addEventListener('click', () => { show(i - 1); start(); });
  pauseBtn.addEventListener('click', () => setPaused(!paused));
  root.addEventListener('mouseenter', () => { hover = true; stop(); });
  root.addEventListener('mouseleave', () => { hover = false; start(); });
  root.addEventListener('focusin', () => { hover = true; stop(); });
  root.addEventListener('focusout', () => { hover = false; start(); });
  document.addEventListener('visibilitychange', () => document.hidden ? stop() : start());
  setPaused(paused);
}
