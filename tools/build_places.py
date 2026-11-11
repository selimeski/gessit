"""GeoNames verisinden places/<kıta>.json dosyalarını üretir.

Kullanım: python3 -I tools/build_places.py <indirme_klasörü>
Veri: GeoNames (https://www.geonames.org/), CC BY 4.0.
"""
import io, json, math, re, sys, urllib.request, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE_URL = 'https://download.geonames.org/export/dump/'
TARGETS = {'Şehir': 300, 'Kasaba': 700, 'Köy': 1000}
CELL = {'Şehir': 2.0, 'Kasaba': 1.0, 'Köy': 0.5}
SKIP_CODES = {'PPLX', 'PPLH', 'PPLQ', 'PPLW', 'PPLCH'}
GN_CONT = {'EU': 'europe', 'AS': 'asia', 'AF': 'africa', 'NA': 'namerica', 'SA': 'samerica', 'OC': 'oceania'}


def fetch(folder, name):
    path = folder / name
    if not path.exists():
        print('indiriliyor', name, file=sys.stderr)
        urllib.request.urlretrieve(BASE_URL + name, path)
    return path


def read_continents():
    html = (ROOT / 'index.html').read_text(encoding='utf-8')
    out = {}
    for m in re.finditer(r"^\s*(\w+): \{ name:[^}]*?bbox:\[([^\]]*)\][^}]*?ids:\[([^\]]*)\]", html, re.M):
        out[m[1]] = {'bbox': [float(v) for v in m[2].split(',')], 'ids': {int(v) for v in m[3].split(',')}}
    if len(out) != 6:
        sys.exit(f'index.html içinden CONTINENTS okunamadı: {sorted(out)}')
    return out


def kind(pop):
    return 'Şehir' if pop >= 100000 else 'Kasaba' if pop >= 5000 else 'Köy'


def in_box(p, bbox):
    x0, y0, x1, y1 = bbox
    return x0 <= p['lon'] <= x1 and y0 <= p['lat'] <= y1


def load_places(folder, continents):
    numeric, gn_cont = {}, {}
    for line in fetch(folder, 'countryInfo.txt').read_text(encoding='utf-8').splitlines():
        if line.startswith('#') or not line.strip():
            continue
        f = line.split('\t')
        numeric[f[0]] = int(f[2]) if f[2].isdigit() else None
        gn_cont[f[0]] = GN_CONT.get(f[8])
    by_cont = {k: [] for k in continents}
    with zipfile.ZipFile(fetch(folder, 'cities500.zip')) as z, z.open('cities500.txt') as fh:
        for line in io.TextIOWrapper(fh, encoding='utf-8'):
            f = line.rstrip('\n').split('\t')
            pop = int(f[14] or 0)
            if f[7] in SKIP_CODES or pop < 500:
                continue
            p = {'id': int(f[0]), 'name': f[1], 'lat': float(f[4]), 'lon': float(f[5]),
                 'cc': f[8], 'pop': pop, 'kind': kind(pop)}
            num = numeric.get(f[8])
            keys = [k for k, c in continents.items() if num in c['ids']]
            if not keys and gn_cont.get(f[8]):
                keys = [gn_cont[f[8]]]  # ISO kodu listede olmayan ülkeler (Kosova vb.)
            for k in keys:
                if in_box(p, continents[k]['bbox']):
                    by_cont[k].append(p)
    return by_cont


def spread(cands, size, target):
    cands = sorted(cands, key=lambda p: (-p['pop'], p['id']))
    taken, cells, chosen = set(), set(), []
    for p in cands:
        cell = (math.floor(p['lat'] / size), math.floor(p['lon'] / size))
        if cell not in cells and len(chosen) < target:
            cells.add(cell); taken.add(p['id']); chosen.append(p)
    for p in cands:
        if len(chosen) >= target:
            break
        if p['id'] not in taken:
            taken.add(p['id']); chosen.append(p)
    return chosen


def turkish_names(folder, ids):
    best = {}  # id -> (tercih_edilen_mi, ad)
    with zipfile.ZipFile(fetch(folder, 'alternateNamesV2.zip')) as z, z.open('alternateNamesV2.txt') as fh:
        for line in io.TextIOWrapper(fh, encoding='utf-8'):
            if '\ttr\t' not in line:
                continue
            f = line.rstrip('\n').split('\t')
            if f[2] != 'tr' or int(f[1]) not in ids or '1' in (f[5], f[6], f[7]):
                continue
            gid, pref = int(f[1]), f[4] == '1'
            if gid not in best or (pref and not best[gid][0]):
                best[gid] = (pref, f[3])
    return {gid: name for gid, (_, name) in best.items()}


def select(cands, banned):
    pool = [p for p in cands if p['display'] not in banned]
    return [p for t in TARGETS for p in spread([p for p in pool if p['kind'] == t], CELL[t], TARGETS[t])]


def main():
    folder = Path(sys.argv[1])
    folder.mkdir(parents=True, exist_ok=True)
    continents = read_continents()
    by_cont = load_places(folder, continents)
    city_ids = {p['id'] for ps in by_cont.values() for p in ps if p['kind'] == 'Şehir'}
    tr = turkish_names(folder, city_ids)
    for ps in by_cont.values():
        for p in ps:
            p['display'] = tr.get(p['id'], p['name']) if p['kind'] == 'Şehir' else p['name']
    (ROOT / 'places').mkdir(exist_ok=True)
    for key, cands in by_cont.items():
        # Aynı adı taşıyan yerler tamamen çıkarılır; boşalan yer yeni seçimle doldurulur.
        banned = set()
        while True:
            chosen = select(cands, banned)
            seen, dup = set(), set()
            for p in chosen:
                (dup if p['display'] in seen else seen).add(p['display'])
            if not dup:
                break
            banned |= dup
        counts = {t: sum(p['kind'] == t for p in chosen) for t in TARGETS}
        # Kendi kontroller
        assert all(in_box(p, continents[key]['bbox']) for p in chosen), key
        assert len({p['display'] for p in chosen}) == len(chosen), key
        for t, n in counts.items():
            avail = sum(p['kind'] == t and p['display'] not in banned for p in cands)
            assert 1 <= n <= TARGETS[t] and (n == TARGETS[t] or n == avail), (key, t, n, avail)
        rows = sorted(([p['display'], p['kind'], p['cc'], round(p['lat'], 5), round(p['lon'], 5)] for p in chosen),
                      key=lambda r: (list(TARGETS).index(r[1]), r[0]))
        (ROOT / 'places' / f'{key}.json').write_text(
            json.dumps(rows, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
        print(f"{key}: " + ', '.join(f'{t} {n}' for t, n in counts.items()))


if __name__ == '__main__':
    main()
