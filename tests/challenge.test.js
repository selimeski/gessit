const test = require('node:test');
const assert = require('node:assert/strict');
const { challengeLink, parseChallenge, pickPlaces } = require('../challenge.js');

const continents = { europe: {}, asia: {} };
const levels = { kolay: { count: 3 }, zor: { count: 7 } };
const parse = (q) => parseChallenge(q, continents, levels, 1000);

test('geçerli link okunur', () => {
  assert.deepEqual(parse('?c=europe&l=zor&s=48213&p=1840&n=Selim'),
    { c: 'europe', l: 'zor', s: 48213, p: 1840, n: 'Selim' });
});

test('Türkçe isim korunur', () => {
  const link = challengeLink('https://x.io/gessit/', { c: 'asia', l: 'kolay', s: 7, p: 0, n: 'Şükrü Öz' });
  assert.equal(parse(new URL(link).search).n, 'Şükrü Öz');
});

test('p=0 geçerlidir', () => {
  assert.equal(parse('?c=asia&l=kolay&s=1&p=0&n=A').p, 0);
});

test('geçersiz değerler reddedilir', () => {
  for (const q of ['', '?c=europe', '?c=mars&l=zor&s=1&p=1&n=A', '?c=europe&l=x&s=1&p=1&n=A',
    '?c=constructor&l=zor&s=1&p=1&n=A', '?c=europe&l=__proto__&s=1&p=1&n=A',
    '?c=europe&l=zor&s=-1&p=1&n=A', '?c=europe&l=zor&s=1e5&p=1&n=A', '?c=europe&l=zor&s=2147483648&p=1&n=A',
    '?c=europe&l=zor&s=1&p=1.5&n=A', '?c=europe&l=kolay&s=1&p=3001&n=A',
    '?c=europe&l=zor&s=1&p=1&n=', '?c=europe&l=zor&s=1&p=1&n=%20%20']) {
    assert.equal(parse(q), null, q);
  }
});

test('uzun isim 20 karaktere kesilir, emoji bölünmez', () => {
  assert.equal(parse('?c=asia&l=kolay&s=1&p=1&n=' + 'a'.repeat(25)).n, 'a'.repeat(20));
  const emoji = '😀'.repeat(25);
  assert.equal(parse('?c=asia&l=kolay&s=1&p=1&n=' + encodeURIComponent(emoji)).n, '😀'.repeat(20));
});

// mulberry32: testler için küçük, tohumlu rastgele sayı üreteci
const rngFrom = (a) => () => {
  a = (a + 0x6D2B79F5) | 0;
  let t = Math.imul(a ^ (a >>> 15), 1 | a);
  t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
};
const sample = ['Şehir', 'Kasaba', 'Köy'].flatMap(t =>
  Array.from({ length: 10 }, (_, i) => [t + i, t, 'X', i, i]));

test('pickPlaces tür sayılarına uyar', () => {
  const r = pickPlaces(sample, { 'Şehir': 1, 'Kasaba': 3, 'Köy': 3 }, rngFrom(1));
  assert.equal(r.length, 7);
  assert.equal(r.filter(p => p[1] === 'Şehir').length, 1);
  assert.equal(r.filter(p => p[1] === 'Kasaba').length, 3);
  assert.equal(new Set(r.map(p => p[0])).size, 7);
});

test('pickPlaces aynı tohumla aynı sonucu verir', () => {
  const c = { 'Şehir': 1, 'Kasaba': 2, 'Köy': 2 };
  assert.deepEqual(pickPlaces(sample, c, rngFrom(9)), pickPlaces(sample, c, rngFrom(9)));
});

test('pickPlaces türde yeterli yer yoksa olanı verir', () => {
  const few = sample.filter(p => p[1] !== 'Şehir').concat([['Tek', 'Şehir', 'X', 0, 0]]);
  const r = pickPlaces(few, { 'Şehir': 2, 'Kasaba': 1, 'Köy': 1 }, rngFrom(3));
  assert.equal(r.filter(p => p[1] === 'Şehir').length, 1);
});

test('pickPlaces girdiyi değiştirmez', () => {
  const copy = JSON.stringify(sample);
  pickPlaces(sample, { 'Şehir': 1, 'Kasaba': 1, 'Köy': 1 }, rngFrom(2));
  assert.equal(JSON.stringify(sample), copy);
});
