/* Prices in INR or USD. Defaults to INR for visitors on Indian time, USD for everyone else.
   Markup: <span class="price" data-inr="40000" data-usd="1000">₹40,000 / $1,000</span>
   and an empty <div class="cur-toggle-slot"></div> wherever a currency switch should appear.
   Without JavaScript the fallback text (both currencies) stays visible. */
(function () {
  var KEY = 'fw-cur';
  var prices = document.querySelectorAll('.price[data-inr][data-usd]');
  var slots = document.querySelectorAll('.cur-toggle-slot');
  if (!prices.length) return;

  function read() { try { return window.localStorage.getItem(KEY); } catch (e) { return null; } }
  function save(v) { try { window.localStorage.setItem(KEY, v); } catch (e) { /* storage blocked */ } }

  function guess() {
    try {
      var tz = Intl.DateTimeFormat().resolvedOptions().timeZone || '';
      if (tz === 'Asia/Kolkata' || tz === 'Asia/Calcutta') return 'inr';
    } catch (e) { /* old browser */ }
    return 'usd';
  }

  var fmt = {
    inr: function (n) { return '₹' + Number(n).toLocaleString('en-IN'); },
    usd: function (n) { return '$' + Number(n).toLocaleString('en-US'); }
  };

  var buttons = [];

  function apply(cur) {
    prices.forEach(function (p) { p.textContent = fmt[cur](p.getAttribute('data-' + cur)); });
    buttons.forEach(function (b) { b.setAttribute('aria-pressed', b.getAttribute('data-cur') === cur ? 'true' : 'false'); });
  }

  slots.forEach(function (slot) {
    var group = document.createElement('div');
    group.className = 'cur-toggle';
    group.setAttribute('role', 'group');
    group.setAttribute('aria-label', 'Show prices in');
    [['inr', '₹ INR'], ['usd', '$ USD']].forEach(function (c) {
      var b = document.createElement('button');
      b.type = 'button';
      b.setAttribute('data-cur', c[0]);
      b.textContent = c[1];
      b.addEventListener('click', function () { save(c[0]); apply(c[0]); });
      buttons.push(b);
      group.appendChild(b);
    });
    slot.replaceWith(group);
  });

  var stored = read();
  apply(stored === 'inr' || stored === 'usd' ? stored : guess());
})();
