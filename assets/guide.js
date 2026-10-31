/* "Feeling lost?" guide: a paper plane that glides between sections, lands, and points visitors to the right page. */
(function () {
  if (window.__fwGuide) return;
  window.__fwGuide = true;

  var HIDDEN = 'fwg-hidden', SEEN = 'fwg-seen', ROLE = 'fwg-role', SIDE = 'fwg-side';
  var SIZE = 56, FIRST_DELAY = 1800, REPEAT_DELAY = 700;
  var SETTLE = 650, MIN_GAP = 3500, MAX_MOVES = 7, BUBBLE_MS = 6500;

  function read(store, key) { try { return store.getItem(key); } catch (e) { return null; } }
  function write(store, key, val) { try { store.setItem(key, val); } catch (e) { /* storage blocked */ } }

  var force = /[?&]guide=1(&|$)/.test(window.location.search);
  if (force) { try { window.localStorage.removeItem(HIDDEN); window.sessionStorage.removeItem(SEEN); } catch (e) { /* storage blocked */ } }
  if (read(window.localStorage, HIDDEN) === '1') return;

  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var canAnimate = !reduce && typeof Element.prototype.animate === 'function';
  var seen = read(window.sessionStorage, SEEN) === '1';

  var HINTS = {
    hero: { t: 'Feeling lost?', act: 'panel' },
    story: { t: 'Feeling lost?', act: 'panel' },
    about: { t: 'Want the full story?', href: '/about#story' },
    projects: { t: "Here's the proof →", href: '/case-studies' },
    services: { t: 'Not sure which? Ask me.', act: 'contact' },
    beliefs: { t: 'More on what I live by', href: '/about#beliefs' },
    experience: { t: 'Grab my resume', href: '/assets/Rudra-Trivedi-Resume.pdf', dl: true },
    faq: { t: 'Still wondering? Ask me.', act: 'contact' },
    'metrics-section': { t: 'Want results like these?', act: 'contact' },
    'final-cta': { t: 'Say hello.', act: 'contact' }
  };
  var ZONES = 'main section, .hero, .final-cta, .narrative-section, .timeline-section, .metrics-section, .learnings-section';

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
  var CYCLE = [['L', 0], ['R', 0]];

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text) n.textContent = text;
    return n;
  }
  function svgEl(tag) { return document.createElementNS('http://www.w3.org/2000/svg', tag); }

  /* ---------- DOM ---------- */
  var root = el('div', 'fwg');
  root.setAttribute('role', 'complementary');
  root.setAttribute('aria-label', 'Site guide');

  var plane = el('button', 'fwg-plane');
  plane.type = 'button';
  plane.setAttribute('aria-expanded', 'false');
  plane.setAttribute('aria-controls', 'fwgPanel');
  plane.setAttribute('aria-label', 'Feeling lost? Open the site guide');
  plane.innerHTML =
    '<span class="fwg-turn"><span class="fwg-bob"><svg viewBox="0 0 64 64" aria-hidden="true">' +
    '<path d="M32 5L50 55 32 44 14 55Z" fill="#FF5233" stroke="#1A1523" stroke-width="2.6" stroke-linejoin="round"/>' +
    '<path d="M32 5L32 44 14 55Z" fill="#FFFDF9" stroke="#1A1523" stroke-width="2.6" stroke-linejoin="round"/>' +
    '</svg></span></span>';
  var turn = plane.querySelector('.fwg-turn');

  var bubble = el('div', 'fwg-bubble');
  var panel = el('div', 'fwg-panel');
  panel.id = 'fwgPanel';
  panel.setAttribute('role', 'dialog');
  panel.setAttribute('aria-label', 'Find your way around');

  var trail = svgEl('svg');
  trail.setAttribute('class', 'fwg-trail');
  trail.setAttribute('aria-hidden', 'true');
  var trailPath = svgEl('path');
  trail.appendChild(trailPath);

  root.appendChild(plane);
  root.appendChild(bubble);

  /* ---------- state ---------- */
  var cur = { x: 0, y: 0, side: 'L', slot: 0, idx: 0 };
  var flying = false, open = false, moves = 0, lastLand = 0, lastZone = null;
  var bubbleTimer = null, scrollTimer = null, shownAt = 0, sticky = false;

  function viewW() { return document.documentElement.clientWidth; }
  function restAngle(side) { return side === 'L' ? 25 : -25; }

  function perch(side, slot) {
    var w = viewW(), h = window.innerHeight, m = w <= 480 ? 12 : 16;
    return {
      x: side === 'L' ? m : w - SIZE - m,
      y: h - SIZE - m
    };
  }

  function setSide(side) {
    root.classList.toggle('side-l', side === 'L');
    root.classList.toggle('side-r', side === 'R');
    panel.classList.toggle('side-l', side === 'L');
    panel.classList.toggle('side-r', side === 'R');
  }

  function place(side, slot) {
    var p = perch(side, slot);
    cur.x = p.x; cur.y = p.y; cur.side = side; cur.slot = slot;
    root.style.transform = 'translate(' + p.x + 'px,' + p.y + 'px)';
    turn.style.transform = 'rotate(' + restAngle(side) + 'deg)';
    setSide(side);
  }

  /* ---------- flight ---------- */
  function flyTo(side, slot, from, done, fixedDur) {
    var to = perch(side, slot), a = from || cur;
    var dx = to.x - a.x, dy = to.y - a.y, dist = Math.hypot(dx, dy) || 1;
    var dur = fixedDur || Math.max(1500, Math.min(2600, dist * 1.6));
    var bend = Math.min(180, dist * 0.28) * (cur.idx % 2 ? -1 : 1);
    var cx = (a.x + to.x) / 2 + (-dy / dist) * bend;
    var cy = (a.y + to.y) / 2 + (dx / dist) * bend - Math.min(120, dist * 0.15);

    var moveFrames = [], turnFrames = [], N = 8, prev = null, i, t, x, y, tx, ty, ang;
    for (i = 0; i <= N; i++) {
      t = i / N;
      x = (1 - t) * (1 - t) * a.x + 2 * (1 - t) * t * cx + t * t * to.x;
      y = (1 - t) * (1 - t) * a.y + 2 * (1 - t) * t * cy + t * t * to.y;
      tx = 2 * (1 - t) * (cx - a.x) + 2 * t * (to.x - cx);
      ty = 2 * (1 - t) * (cy - a.y) + 2 * t * (to.y - cy);
      ang = Math.atan2(ty, tx) * 180 / Math.PI + 90;
      if (prev !== null) { while (ang - prev > 180) ang -= 360; while (ang - prev < -180) ang += 360; }
      prev = ang;
      moveFrames.push({ transform: 'translate(' + x.toFixed(1) + 'px,' + y.toFixed(1) + 'px)' });
      turnFrames.push({ transform: 'rotate(' + ang.toFixed(1) + 'deg)' });
    }
    var rest = restAngle(side);
    while (rest - prev > 180) rest -= 360;
    while (rest - prev < -180) rest += 360;
    turnFrames.push({ transform: 'rotate(' + rest + 'deg)' });
    moveFrames.push({ transform: 'translate(' + to.x + 'px,' + to.y + 'px)' });
    turnFrames.splice(turnFrames.length - 2, 1);

    drawTrail(a, { x: cx, y: cy }, to, dur);
    flying = true;
    hideBubble();
    root.classList.add('flying');
    var opts = { duration: dur, easing: 'cubic-bezier(0.45,0.05,0.25,1)', fill: 'forwards' };
    var m = root.animate(moveFrames, opts);
    turn.animate(turnFrames, opts);
    m.onfinish = function () {
      place(side, slot);
      root.getAnimations().forEach(function (an) { an.cancel(); });
      turn.getAnimations().forEach(function (an) { an.cancel(); });
      flying = false;
      root.classList.remove('flying');
      cur.idx = CYCLE.findIndex(function (c) { return c[0] === side && c[1] === slot; });
      lastLand = Date.now();
      write(window.sessionStorage, SIDE, side);
      if (done) done();
    };
  }

  function drawTrail(a, c, b, dur) {
    var o = SIZE / 2;
    trailPath.setAttribute('d', 'M' + (a.x + o) + ' ' + (a.y + o) + ' Q' + (c.x + o) + ' ' + (c.y + o) + ' ' + (b.x + o) + ' ' + (b.y + o));
    trailPath.animate([{ opacity: 0 }, { opacity: 0.85, offset: 0.2 }, { opacity: 0.85, offset: 0.7 }, { opacity: 0 }], { duration: dur + 900, easing: 'ease-out' });
  }

  /* ---------- hints ---------- */
  function hintFor(node) {
    var key = null, i;
    if (node.id && HINTS[node.id]) key = node.id;
    else for (i = 0; i < node.classList.length; i++) if (HINTS[node.classList[i]]) { key = node.classList[i]; break; }
    if (!key) return null;
    var h = HINTS[key];
    if (h.href && h.href.split('#')[0] === window.location.pathname) return null;
    return h;
  }

  function openContact() {
    if (typeof window.openContactModal === 'function') window.openContactModal();
    else window.location.href = 'mailto:rudra@f1rstword.com';
  }

  function showBubble(h, keep) {
    if (!h || open) return;
    sticky = !!keep;
    clearTimeout(bubbleTimer);
    bubble.textContent = '';
    var ctl;
    if (h.href) {
      ctl = el('a', 'fwg-bubble-btn', h.t);
      ctl.href = h.href;
      if (h.dl) ctl.setAttribute('download', '');
    } else {
      ctl = el('button', 'fwg-bubble-btn', h.t);
      ctl.type = 'button';
      ctl.addEventListener('click', function () {
        hideBubble();
        if (h.act === 'contact') openContact(); else setOpen(true);
      });
    }
    bubble.appendChild(ctl);
    bubble.classList.add('show');
    shownAt = window.pageYOffset;
    bubbleTimer = setTimeout(hideBubble, BUBBLE_MS);
  }
  function hideBubble() { clearTimeout(bubbleTimer); bubble.classList.remove('show'); }

  /* ---------- roaming ---------- */
  function zoneAtCenter() {
    var list = document.querySelectorAll(ZONES), mid = window.innerHeight / 2, i, r;
    for (i = 0; i < list.length; i++) {
      r = list[i].getBoundingClientRect();
      if (r.top <= mid && r.bottom >= mid) return list[i];
    }
    return null;
  }

  function modalOpen() {
    var m = document.getElementById('contactModal');
    return !!(m && m.classList.contains('open'));
  }

  function evaluate() {
    if (!root.isConnected || !canAnimate || flying || open || modalOpen()) return;
    if (moves >= MAX_MOVES || Date.now() - lastLand < MIN_GAP) return;
    var zone = zoneAtCenter();
    if (!zone || zone === lastZone) return;
    var h = hintFor(zone);
    if (!h) return;
    lastZone = zone;
    moves++;
    var next = CYCLE[(cur.idx + 1) % CYCLE.length];
    flyTo(next[0], next[1], null, function () { setTimeout(function () { showBubble(h); }, 400); });
  }

  /* ---------- panel ---------- */
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
      [root, panel, trail].forEach(function (n) { if (n.parentNode) n.parentNode.removeChild(n); });
    });
    return h;
  }

  function setOpen(next) {
    open = next;
    root.classList.toggle('open', open);
    panel.classList.toggle('open', open);
    plane.setAttribute('aria-expanded', open ? 'true' : 'false');
    if (open) {
      hideBubble();
      var role = read(window.sessionStorage, ROLE);
      if (role && ROLES[role]) renderList(role, false); else renderRoles();
    } else {
      plane.focus({ preventScroll: true });
    }
  }

  plane.addEventListener('click', function () { setOpen(!open); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && open) setOpen(false); });
  document.addEventListener('click', function (e) {
    if (open && e.target.isConnected && !root.contains(e.target) && !panel.contains(e.target)) {
      open = false;
      root.classList.remove('open');
      panel.classList.remove('open');
      plane.setAttribute('aria-expanded', 'false');
    }
  });
  window.addEventListener('scroll', function () {
    if (!sticky && bubble.classList.contains('show') && Math.abs(window.pageYOffset - shownAt) > 60) hideBubble();
    clearTimeout(scrollTimer);
    scrollTimer = setTimeout(evaluate, SETTLE);
  }, { passive: true });
  window.addEventListener('resize', function () { if (root.isConnected && !flying) place(cur.side, cur.slot); });

  /* ---------- start ---------- */
  function start() {
    document.body.appendChild(trail);
    document.body.appendChild(root);
    document.body.appendChild(panel);
    write(window.sessionStorage, SEEN, '1');
    var side = seen && read(window.sessionStorage, SIDE) === 'R' ? 'R' : 'L';
    cur.idx = side === 'R' ? 1 : 0;
    place(side, 0);
    root.classList.add('on');
    if (!seen && canAnimate) {
      var from = { x: -90, y: Math.round(window.innerHeight * 0.2) };
      root.style.transform = 'translate(' + from.x + 'px,' + from.y + 'px)';
      flyTo(side, 0, from, function () { setTimeout(function () { showBubble(HINTS.hero, true); }, 300); });
    } else if (!seen) {
      setTimeout(function () { showBubble(HINTS.hero, true); }, 600);
    } else if (canAnimate) {
      var p = perch(side, 0);
      var back = { x: side === 'L' ? -80 : viewW() + 24, y: p.y + 70 };
      root.style.transform = 'translate(' + back.x + 'px,' + back.y + 'px)';
      flyTo(side, 0, back, null, 1100);
    }
  }

  function schedule() { setTimeout(start, seen ? REPEAT_DELAY : FIRST_DELAY); }
  if (document.readyState !== 'loading') schedule(); else document.addEventListener('DOMContentLoaded', schedule);
})();
