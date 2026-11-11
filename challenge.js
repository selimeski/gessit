function challengeLink(base, { c, l, s, p, n }) {
  return base + '?' + new URLSearchParams({ c, l, s, p, n });
}

// Linkten gelen değerler kullanıcı girdisi sayılır: geçersiz bir değer varsa null döner.
function parseChallenge(search, continents, levels, maxPoints) {
  const q = new URLSearchParams(search);
  const c = q.get('c'), l = q.get('l'), s = q.get('s'), p = q.get('p');
  if (!Object.hasOwn(continents, c) || !Object.hasOwn(levels, l)) return null;
  if (!/^\d+$/.test(s) || !/^\d+$/.test(p)) return null;
  if (+s > 2147483647 || +p > levels[l].count * maxPoints) return null;
  const n = [...(q.get('n') || '').trim()].slice(0, 20).join('');
  return n ? { c, l, s: +s, p: +p, n } : null;
}

function shuffle(arr, rng) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}

// Her türden counts kadar yer seçer; aynı rng aynı soruları verir.
function pickPlaces(places, counts, rng) {
  const picked = ['Şehir', 'Kasaba', 'Köy'].flatMap(t =>
    shuffle(places.filter(p => p[1] === t), rng).slice(0, counts[t] || 0));
  return shuffle(picked, rng);
}

if (typeof module !== 'undefined') module.exports = { challengeLink, parseChallenge, pickPlaces };
