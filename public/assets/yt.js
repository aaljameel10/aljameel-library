// Filmed interviews: load the YouTube player only when the visitor presses play.
document.querySelectorAll('[data-yt]').forEach(v => v.querySelector('button').addEventListener('click', () => {
  const f = document.createElement('iframe');
  f.src = 'https://www.youtube-nocookie.com/embed/' + encodeURIComponent(v.dataset.yt) + '?autoplay=1&rel=0';
  f.title = 'لقاء مصوّر';
  f.allow = 'autoplay; encrypted-media; picture-in-picture';
  f.allowFullscreen = true;
  v.replaceChildren(f);
}));
