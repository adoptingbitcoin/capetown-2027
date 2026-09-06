/* ------------------------------------------------------------------
 * Ticket schedule: countdown + prices in one place.
 *
 * Each phase runs until its deadline. The countdown ticks down to the
 * deadline of the phase that is currently live, and the ticket cards
 * (title + rand price + sats equivalent) show that same phase's values.
 * When a deadline passes, the next phase takes over automatically --
 * no deploy needed.
 *
 * Deadlines are anchored to South African Standard Time (SAST, UTC+2,
 * no DST) so the countdown is identical regardless of the visitor's
 * local timezone.
 *
 * >>> EDIT PRICES AND TITLES HERE AND NOWHERE ELSE. <<<
 * Prices are in rand and mirror the Pretix product list. The markup is
 * rewritten from these numbers, so the values hard-coded in the HTML are
 * only a first paint.
 * ------------------------------------------------------------------ */

const TICKET_PHASES = [
  {
    deadline: '2026-07-31T23:59:59+02:00',
    tiers: {
      local: { title: 'Earlybird Local',              price: 1000 },
      intl:  { title: 'Earlybird International',      price: 2700 },
      vip:   { title: 'Earlybird VIP',                price: 8000 }
    }
  },
  {
    deadline: '2026-08-31T23:59:59+02:00',
    tiers: {
      local: { title: 'Local',                        price: 1500 },
      intl:  { title: 'International (Lank Early)',   price: 2900 },
      vip:   { title: 'VIP',                          price: 10000 }
    }
  },
  {
    deadline: '2026-09-30T23:59:59+02:00',
    tiers: {
      local: { title: 'Local',                        price: 1500 },
      intl:  { title: 'International (Kak Early)',    price: 3300 },
      vip:   { title: 'VIP',                          price: 10000 }
    }
  },
  {
    deadline: '2026-10-31T23:59:59+02:00',
    tiers: {
      local: { title: 'Local',                        price: 1500 },
      intl:  { title: 'International (Lekker Early)', price: 3900 },
      vip:   { title: 'VIP',                          price: 10000 }
    }
  },
  {
    deadline: '2026-11-30T23:59:59+02:00',
    tiers: {
      local: { title: 'Local',                        price: 1500 },
      intl:  { title: 'International (Kief Early)',   price: 4700 },
      vip:   { title: 'VIP',                          price: 10000 }
    }
  },
  {
    deadline: '2026-12-31T23:59:59+02:00',
    tiers: {
      local: { title: 'Local',                        price: 1500 },
      intl:  { title: 'International (Now Now)',      price: 5700 },
      vip:   { title: 'VIP',                          price: 10000 }
    }
  },
  {
    deadline: '2027-01-31T23:59:59+02:00',
    tiers: {
      local: { title: 'Local',                        price: 1500 },
      intl:  { title: 'International (Just Now)',     price: 6700 },
      vip:   { title: 'VIP',                          price: 10000 }
    }
  },
  {
    deadline: '2027-02-27T23:59:59+02:00',
    tiers: {
      local: { title: 'Local',                        price: 1500 },
      intl:  { title: 'International (Ag Man)',       price: 7700 },
      vip:   { title: 'VIP',                          price: 10000 }
    }
  }
];

/* Fallback tier order, used only for ticket cards that predate the
   data-tier attribute (first card = local, second = intl, third = vip). */
const TIER_ORDER = ['local', 'intl', 'vip'];

(function () {
  'use strict';

  const phases = TICKET_PHASES.map(p => ({
    time: new Date(p.deadline).getTime(),
    tiers: p.tiers
  })).sort((a, b) => a.time - b.time);

  let phaseIndex = -1;      // index of the phase currently on sale
  let satsPerZar = null;    // latest rate from the BTC feed

  function currentPhase() {
    const now = Date.now();
    const i = phases.findIndex(p => p.time > now);
    return i === -1 ? phases.length - 1 : i;   // past the last deadline: hold the final prices
  }

  /* ---------------- prices ---------------- */

  // 1234.5 -> { rands: '1 234', cents: '50' }
  function splitPrice(price) {
    const cents = Math.round((price % 1) * 100);
    const rands = Math.floor(price)
      .toString()
      .replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
    return { rands, cents: cents.toString().padStart(2, '0') };
  }

  function tierOf(card, index) {
    return card.getAttribute('data-tier') || TIER_ORDER[index] || null;
  }

  function renderPrices() {
    const tiers = phases[phaseIndex].tiers;

    document.querySelectorAll('.ticket-price').forEach((priceEl, index) => {
      const key = tierOf(priceEl, index);
      const tier = key && tiers[key];
      if (!tier) return;

      const { rands, cents } = splitPrice(tier.price);
      priceEl.innerHTML =
        'R' + rands + '<span class="price-decimal">,' + cents + '</span>';
      priceEl.dataset.priceZar = tier.price;

      // The title lives in the same .tickets-texts block as the price.
      const card = priceEl.closest('.tickets-texts') || priceEl.parentNode;
      const titleEl = card && card.querySelector('.ticket-title');
      if (titleEl && tier.title) titleEl.innerText = tier.title;
    });

    renderSats();
  }

  /* ---------------- sats ---------------- */

  function renderSats() {
    if (!satsPerZar) return;

    document.querySelectorAll('.ticket-price').forEach(priceEl => {
      // Prefer the number we set ourselves; fall back to parsing the markup
      // (keeping the decimal point so cents are not read as extra digits).
      const priceValue =
        parseFloat(priceEl.dataset.priceZar) ||
        parseFloat(priceEl.innerText.replace(/[^0-9.]/g, '')) ||
        0;

      // Round up to the nearest 100 sats
      const satsAmount = Math.ceil((priceValue * satsPerZar) / 100) * 100;
      const label = '~' + satsAmount.toLocaleString() + ' sats';

      const sibling = priceEl.nextElementSibling;
      if (sibling && sibling.classList.contains('ticket-price-sats')) {
        sibling.innerText = label;
      } else {
        const satsEl = document.createElement('span');
        satsEl.className = 'ticket-price-sats';
        satsEl.innerText = label;
        priceEl.parentNode.insertBefore(satsEl, priceEl.nextSibling);
      }
    });
  }

  async function fetchBitcoinPrice() {
    const priceEl = document.getElementById('btc-price');
    try {
      const response = await fetch(
        'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=zar'
      );
      const data = await response.json();
      if (!data.bitcoin || !data.bitcoin.zar) throw new Error('Invalid API response');

      const btcPriceZar = parseFloat(data.bitcoin.zar);
      // 1 BTC = 100,000,000 sats
      satsPerZar = Math.round(100000000 / btcPriceZar);

      if (priceEl) priceEl.innerText = satsPerZar.toLocaleString();
      renderSats();
    } catch (error) {
      console.error('(offline) ', error);
      if (priceEl) priceEl.innerText = 'Error fetching price';
    }
  }

  /* ---------------- countdown ---------------- */

  function startCountdown() {
    const daysEl = document.querySelector('#js-timer-days');
    const hoursEl = document.querySelector('#js-timer-hours');
    const minutesEl = document.querySelector('#js-timer-minutes');
    const secondsEl = document.querySelector('#js-timer-seconds');
    if (!daysEl || !hoursEl || !minutesEl || !secondsEl) return;

    const pad = n => n.toString().padStart(2, '0');

    function tick() {
      const now = Date.now();
      const deadline = phases[phaseIndex].time;
      const distance = deadline - now;

      if (distance <= 0) {
        // Phase is over: roll onto the next one (prices and titles included).
        const next = currentPhase();
        if (next !== phaseIndex) {
          phaseIndex = next;
          renderPrices();
        }
        if (phases[phaseIndex].time <= now) {
          // Nothing left on the calendar -- stop at zero.
          daysEl.innerText = hoursEl.innerText = '00';
          minutesEl.innerText = secondsEl.innerText = '00';
        }
        return;
      }

      daysEl.innerText = pad(Math.floor(distance / (1000 * 60 * 60 * 24)));
      hoursEl.innerText = pad(Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)));
      minutesEl.innerText = pad(Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60)));
      secondsEl.innerText = pad(Math.floor((distance % (1000 * 60)) / 1000));
    }

    tick();                  // paint immediately, don't wait a second
    setInterval(tick, 1000);
  }

  /* ---------------- boot ---------------- */

  function init() {
    phaseIndex = currentPhase();
    renderPrices();
    startCountdown();
    fetchBitcoinPrice();
    setInterval(fetchBitcoinPrice, 60000);   // refresh the rate every 60 seconds
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
