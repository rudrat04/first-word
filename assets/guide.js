/* "Feeling lost?" guide: a small labelled button that opens a panel pointing visitors to the right page. */
(function () {
  if (window.__fwGuide) return;
  window.__fwGuide = true;

  var HIDDEN = 'fwg-hidden', SEEN = 'fwg-seen', ROLE = 'fwg-role';
  var FIRST_DELAY = 2000, REPEAT_DELAY = 600, ROTATE_MS = 5500, MAX_SWAPS = 6;
  var PROMPTS = ['Feeling lost?', 'Looking for my resume?', 'Want proof it works?', 'Not sure where to start?'];

  function read(store, key) { try { return store.getItem(key); } catch (e) { return null; } }
  function write(store, key, val) { try { store.setItem(key, val); } catch (e) { /* storage blocked */ } }

  var force = /[?&]guide=1(&|$)/.test(window.location.search);
  if (force) { try { window.localStorage.removeItem(HIDDEN); window.sessionStorage.removeItem(SEEN); } catch (e) { /* storage blocked */ } }
  if (read(window.localStorage, HIDDEN) === '1') return;

  var seen = read(window.sessionStorage, SEEN) === '1';

  var ROLES = {
    owner: {
      label: 'I run a business',
      dot: '#FFD5A0',
      icon: '<svg viewBox="0 0 24 24" fill="none" stroke="#1A1523" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 21V9l8-5 8 5v12M9 21v-7h6v7"/></svg>',
      intro: 'Here is where most business owners go first.',
      items: [
        ['See proof it works', '/case-studies'],
        ['What can you do for me?', '/what-i-do'],
        ['Who is behind this?', '/about#story'],
        ["Let's talk", '#contact']
      ]
    },
    hire: {
      label: "I'm hiring",
      dot: '#C6A3D6',
      icon: '<svg viewBox="0 0 24 24" fill="none" stroke="#1A1523" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2.5"/><circle cx="9" cy="11" r="2"/><path d="M6.5 16c.6-2 4.4-2 5 0M14 10h4M14 14h3"/></svg>',
      intro: 'Here is where most recruiters go first.',
      items: [
        ['See my experience', '/about#experience'],
        ["What I've built", '/case-studies'],
        ['Get my resume', '/assets/Rudra-Trivedi-Resume.pdf', true],
        ['Who I am', '/about#story'],
        ["Let's talk", '#contact']
      ]
    }
  };
  var COLORS = ['#FFD5A0', '#E7A7BE', '#C6A3D6', '#8FA9DA', '#FFF1B8'];

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text) n.textContent = text;
    return n;
  }

  /* ---------- DOM ---------- */
  var root = el('div', 'fwg');
  root.setAttribute('role', 'complementary');
  root.setAttribute('aria-label', 'Site guide');

  var pill = el('button', 'fwg-pill');
  pill.type = 'button';
  pill.setAttribute('aria-expanded', 'false');
  pill.setAttribute('aria-controls', 'fwgPanel');
  pill.setAttribute('aria-label', 'Feeling lost? Open the site guide');
  pill.innerHTML =
    '<span class="fwg-icon" aria-hidden="true"><svg viewBox="0 0 64 64">' +
    '<path d="M32 5L50 55 32 44 14 55Z" fill="#FF5233" stroke="#1A1523" stroke-width="3.2" stroke-linejoin="round"/>' +
    '<path d="M32 5L32 44 14 55Z" fill="#FFFDF9" stroke="#1A1523" stroke-width="3.2" stroke-linejoin="round"/>' +
    '</svg></span>';
  var text = el('span', 'fwg-text', PROMPTS[0]);
  text.setAttribute('aria-hidden', 'true');
  pill.appendChild(text);
  root.appendChild(pill);

  var panel = el('div', 'fwg-panel');
  panel.id = 'fwgPanel';
  panel.setAttribute('role', 'dialog');
  panel.setAttribute('aria-label', 'Find your way around');

  var open = false, hovering = false, swaps = 0, idx = 0, rotateTimer = null;

  /* ---------- rotating prompt ---------- */
  function swapText() {
    if (open || hovering || swaps >= MAX_SWAPS) return;
    swaps++;
    idx = swaps >= MAX_SWAPS ? 0 : (idx + 1) % PROMPTS.length;
    text.classList.add('fade');
    setTimeout(function () { text.textContent = PROMPTS[idx]; text.classList.remove('fade'); }, 250);
  }

  /* ---------- panel ---------- */
  function openContact() {
    if (typeof window.openContactModal === 'function') window.openContactModal();
    else window.location.href = 'mailto:rudra@f1rstword.com';
  }

  function addClose() {
    var close = el('button', 'fwg-close', '✕');
    close.type = 'button';
    close.setAttribute('aria-label', 'Close guide');
    close.addEventListener('click', function () { setOpen(false); });
    panel.appendChild(close);
  }

  function renderRoles() {
    panel.textContent = '';
    addClose();
    panel.appendChild(el('h2', '', 'Feeling lost?'));
    panel.appendChild(el('p', '', "Tell me why you're here and I'll point you to the right place."));
    var list = el('div', 'fwg-list');
    Object.keys(ROLES).forEach(function (key) {
      var r = ROLES[key], b = el('button', 'fwg-btn'), dot = el('span', 'fwg-dot');
      b.type = 'button';
      dot.style.setProperty('--c', r.dot);
      dot.innerHTML = r.icon;
      b.appendChild(dot);
      b.appendChild(el('span', '', r.label));
      b.appendChild(el('span', 'fwg-arr', '→'));
      b.addEventListener('click', function () { write(window.sessionStorage, ROLE, key); renderList(key, true); });
      list.appendChild(b);
    });
    panel.appendChild(list);
    panel.appendChild(hideLink());
  }

  function renderList(key, focus) {
    var r = ROLES[key];
    panel.textContent = '';
    addClose();
    var back = el('button', 'fwg-back', '← Change');
    back.type = 'button';
    back.addEventListener('click', function () { renderRoles(); var f = panel.querySelector('.fwg-btn'); if (f) f.focus(); });
    panel.appendChild(back);
    panel.appendChild(el('h2', '', key === 'hire' ? 'Hiring? Start here.' : 'Business owner? Start here.'));
    panel.appendChild(el('p', '', r.intro));
    var list = el('div', 'fwg-list');
    r.items.forEach(function (it, i) {
      var isContact = it[1] === '#contact';
      var a = el(isContact ? 'button' : 'a', 'fwg-btn'), dot = el('span', 'fwg-dot', String(i + 1));
      if (isContact) a.type = 'button';
      else { a.href = it[1]; if (it[2]) a.setAttribute('download', ''); }
      dot.style.setProperty('--c', COLORS[i % COLORS.length]);
      a.appendChild(dot);
      a.appendChild(el('span', '', it[0]));
      a.appendChild(el('span', 'fwg-arr', '→'));
      a.addEventListener('click', function () { setOpen(false); if (isContact) openContact(); });
      list.appendChild(a);
    });
    panel.appendChild(list);
    panel.appendChild(hideLink());
    if (focus) { var f = panel.querySelector('.fwg-btn'); if (f) f.focus(); }
  }

  function hideLink() {
    var h = el('button', 'fwg-hide', "Don't show this helper again");
    h.type = 'button';
    h.addEventListener('click', function () {
      write(window.localStorage, HIDDEN, '1');
      clearInterval(rotateTimer);
      [root, panel].forEach(function (n) { if (n.parentNode) n.parentNode.removeChild(n); });
    });
    return h;
  }

  function setOpen(next) {
    open = next;
    root.classList.toggle('open', open);
    panel.classList.toggle('open', open);
    pill.setAttribute('aria-expanded', open ? 'true' : 'false');
    if (open) {
      var role = read(window.sessionStorage, ROLE);
      if (role && ROLES[role]) renderList(role, false); else renderRoles();
    } else {
      pill.focus({ preventScroll: true });
    }
  }

  pill.addEventListener('click', function () { setOpen(!open); });
  pill.addEventListener('mouseenter', function () { hovering = true; });
  pill.addEventListener('mouseleave', function () { hovering = false; });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && open) setOpen(false); });
  document.addEventListener('click', function (e) {
    if (open && e.target.isConnected && !root.contains(e.target) && !panel.contains(e.target)) {
      open = false;
      root.classList.remove('open');
      panel.classList.remove('open');
      pill.setAttribute('aria-expanded', 'false');
    }
  });

  /* ---------- start ---------- */
  function start() {
    document.body.appendChild(root);
    document.body.appendChild(panel);
    write(window.sessionStorage, SEEN, '1');
    window.requestAnimationFrame(function () { window.requestAnimationFrame(function () { root.classList.add('on'); }); });
    rotateTimer = setInterval(swapText, ROTATE_MS);
  }

  function schedule() { setTimeout(start, seen ? REPEAT_DELAY : FIRST_DELAY); }
  if (document.readyState !== 'loading') schedule(); else document.addEventListener('DOMContentLoaded', schedule);
})();
