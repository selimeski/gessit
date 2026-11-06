const test = require('node:test');
const assert = require('node:assert/strict');
const { challengeLink, parseChallenge } = require('../challenge.js');

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
