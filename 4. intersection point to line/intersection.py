"""
intersect_kmz.py
------------------
Cari garis intersection (proyeksi tegak lurus) dari titik-titik ke garis
referensi, keduanya dari file KMZ. Hasil:
  1. File KMZ berisi garis intersection (titik -> titik terdekat di garis)
  2. Tabel CSV: No, Nama Titik, Jarak (meter)

Input:
  - titik.kmz  -> berisi Placemark bertipe Point (titik-titik yang mau diukur)
  - garis.kmz  -> berisi Placemark bertipe LineString (garis referensi,
                  misalnya as jalan / pipa / batas)

Cara pakai:
  1. Ubah TITIK_KMZ, GARIS_KMZ, OUTPUT_KMZ, OUTPUT_CSV di bagian KONFIGURASI
     di bawah sesuai nama/lokasi file kamu.
  2. Jalankan:  python3 intersect_kmz.py
"""

import re
import math
import zipfile
import csv
import shutil
import os


# ----------------------------------------------------------------------
# 1. BACA KMZ -> TITIK & GARIS
# ----------------------------------------------------------------------

def _extract_kml(kmz_path, work_dir):
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    os.makedirs(work_dir)
    with zipfile.ZipFile(kmz_path) as z:
        kml_name = next(n for n in z.namelist() if n.endswith(".kml"))
        z.extractall(work_dir)
    with open(os.path.join(work_dir, kml_name), encoding="utf-8") as f:
        return f.read()


def read_points_kmz(kmz_path, work_dir="/tmp/titik_work"):
    """Baca semua Placemark ber-geometri <Point> dari file KMZ titik.
    Return list [(name, lon, lat), ...]."""
    kml_text = _extract_kml(kmz_path, work_dir)
    points = []
    for pm in re.findall(r"<Placemark[^>]*>(.*?)</Placemark>", kml_text, re.S):
        name_m = re.search(r"<name>(.*?)</name>", pm, re.S)
        point_m = re.search(r"<Point[^>]*>.*?<coordinates>([^<]+)</coordinates>.*?</Point>", pm, re.S)
        if not (name_m and point_m):
            continue
        name = name_m.group(1).strip()
        lon, lat, *_ = [float(v) for v in point_m.group(1).strip().split(",")]
        points.append((name, lon, lat))
    return points


def read_lines_kmz(kmz_path, work_dir="/tmp/garis_work"):
    """Baca semua Placemark ber-geometri <LineString> dari file KMZ garis.
    Return list of polylines, tiap polyline = list [(lon, lat), ...] vertex berurutan.
    Kalau ada beberapa LineString, semua digabung jadi satu list segmen global."""
    kml_text = _extract_kml(kmz_path, work_dir)
    lines = []
    for pm in re.findall(r"<Placemark[^>]*>(.*?)</Placemark>", kml_text, re.S):
        coord_m = re.search(r"<LineString[^>]*>.*?<coordinates>([^<]+)</coordinates>.*?</LineString>", pm, re.S)
        if not coord_m:
            continue
        raw = coord_m.group(1).strip()
        verts = []
        for tok in raw.split():
            lon, lat, *_ = [float(v) for v in tok.split(",")]
            verts.append((lon, lat))
        if len(verts) >= 2:
            lines.append(verts)
    return lines


# ----------------------------------------------------------------------
# 2. GEOMETRI: PROYEKSI TITIK KE GARIS (LOKAL PLANAR) + JARAK GEODESIK
# ----------------------------------------------------------------------

def haversine_m(p1, p2):
    """Jarak permukaan bumi (meter) antara dua titik (lon, lat)."""
    lon1, lat1 = p1
    lon2, lat2 = p2
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _deg_to_local(lon, lat, ref_lon, ref_lat):
    """Konversi lon/lat (derajat) ke koordinat lokal meter (proyeksi
    equirectangular sederhana, cukup akurat untuk area lokal beberapa km)."""
    x = (lon - ref_lon) * 111320 * math.cos(math.radians(ref_lat))
    y = (lat - ref_lat) * 110540
    return x, y


def _local_to_deg(x, y, ref_lon, ref_lat):
    lon = x / (111320 * math.cos(math.radians(ref_lat))) + ref_lon
    lat = y / 110540 + ref_lat
    return lon, lat


def _closest_point_on_segment(p, a, b):
    """p, a, b dalam koordinat lokal (x, y). Return (titik_terdekat, t)."""
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return a, 0.0
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    return (ax + t * dx, ay + t * dy), t


def closest_point_on_polylines(point, polylines, ref_lon, ref_lat):
    """Cari titik terdekat di kumpulan polyline (semua garis dari garis.kmz)
    terhadap `point` (lon, lat). Return (lon, lat) titik proyeksi terdekat."""
    px, py = _deg_to_local(point[0], point[1], ref_lon, ref_lat)
    best = None
    best_dist2 = None
    for verts in polylines:
        local_verts = [_deg_to_local(lo, la, ref_lon, ref_lat) for lo, la in verts]
        for i in range(len(local_verts) - 1):
            cp, _t = _closest_point_on_segment((px, py), local_verts[i], local_verts[i + 1])
            dist2 = (cp[0] - px) ** 2 + (cp[1] - py) ** 2
            if best_dist2 is None or dist2 < best_dist2:
                best_dist2 = dist2
                best = cp
    lon, lat = _local_to_deg(best[0], best[1], ref_lon, ref_lat)
    return (lon, lat)


# ----------------------------------------------------------------------
# 3. TULIS KMZ HASIL (GARIS INTERSECTION)
# ----------------------------------------------------------------------

LINE_STYLE_ID = "garis_intersection"
POINT_STYLE_ID = "titik_proyeksi"

STYLE_BLOCK = f"""\t<Style id="{LINE_STYLE_ID}">
\t\t<LineStyle>
\t\t\t<color>ff0000ff</color>
\t\t\t<width>2</width>
\t\t</LineStyle>
\t</Style>
\t<Style id="{POINT_STYLE_ID}">
\t\t<IconStyle>
\t\t\t<color>ff00a5ff</color>
\t\t\t<scale>0.5</scale>
\t\t\t<Icon>
\t\t\t\t<href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href>
\t\t\t</Icon>
\t\t</IconStyle>
\t</Style>
"""


def build_result_kml(results):
    """results: list of dict {name, point(lon,lat), proj(lon,lat), dist}
    Return teks KML lengkap (siap dizip jadi kmz)."""
    placemarks = []
    for r in results:
        (plon, plat), (jlon, jlat) = r["point"], r["proj"]
        # garis intersection: titik asli -> titik proyeksi di garis
        placemarks.append(
            f'\t\t<Placemark>\n\t\t\t<name>Intersection {r["name"]}</name>\n'
            f'\t\t\t<description>Jarak: {r["dist"]:.3f} m</description>\n'
            f'\t\t\t<styleUrl>#{LINE_STYLE_ID}</styleUrl>\n'
            f'\t\t\t<LineString>\n\t\t\t\t<coordinates>{plon:.7f},{plat:.7f},0 {jlon:.7f},{jlat:.7f},0</coordinates>\n'
            f'\t\t\t</LineString>\n\t\t</Placemark>\n'
        )
        # titik proyeksi di garis (opsional, memudahkan cek visual)
        placemarks.append(
            f'\t\t<Placemark>\n\t\t\t<name>Proyeksi {r["name"]}</name>\n'
            f'\t\t\t<styleUrl>#{POINT_STYLE_ID}</styleUrl>\n'
            f'\t\t\t<Point>\n\t\t\t\t<coordinates>{jlon:.7f},{jlat:.7f},0</coordinates>\n'
            f'\t\t\t</Point>\n\t\t</Placemark>\n'
        )

    kml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<kml xmlns="http://www.opengis.net/kml/2.2">\n<Document>\n'
        '\t<name>Garis Intersection</name>\n'
        + STYLE_BLOCK
        + "".join(placemarks)
        + "</Document>\n</kml>\n"
    )
    return kml


def write_kmz_from_kml(kml_text, output_kmz, work_dir="/tmp/intersect_out"):
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    os.makedirs(work_dir)
    kml_path = os.path.join(work_dir, "doc.kml")
    with open(kml_path, "w", encoding="utf-8") as f:
        f.write(kml_text)
    if os.path.exists(output_kmz):
        os.remove(output_kmz)
    with zipfile.ZipFile(output_kmz, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(kml_path, arcname="doc.kml")


# ----------------------------------------------------------------------
# 4. TULIS TABEL CSV
# ----------------------------------------------------------------------

def write_csv(results, output_csv):
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["No", "Nama Titik", "Jarak (m)"])
        for i, r in enumerate(results, start=1):
            writer.writerow([i, r["name"], f'{r["dist"]:.3f}'])


# ----------------------------------------------------------------------
# 5. FUNGSI UTAMA
# ----------------------------------------------------------------------

def intersect_kmz(titik_kmz, garis_kmz, output_kmz, output_csv):
    points = read_points_kmz(titik_kmz)
    polylines = read_lines_kmz(garis_kmz)
    print(f"Titik terbaca dari {titik_kmz}: {len(points)}")
    print(f"Garis (LineString) terbaca dari {garis_kmz}: {len(polylines)}")

    if not points:
        raise ValueError("Tidak ada Placemark bertipe Point ditemukan di titik.kmz")
    if not polylines:
        raise ValueError("Tidak ada Placemark bertipe LineString ditemukan di garis.kmz")

    # titik referensi untuk proyeksi planar lokal (rata-rata semua vertex garis)
    all_verts = [v for line in polylines for v in line]
    ref_lon = sum(v[0] for v in all_verts) / len(all_verts)
    ref_lat = sum(v[1] for v in all_verts) / len(all_verts)

    results = []
    for name, lon, lat in points:
        proj_lon, proj_lat = closest_point_on_polylines((lon, lat), polylines, ref_lon, ref_lat)
        dist = haversine_m((lon, lat), (proj_lon, proj_lat))
        results.append({
            "name": name,
            "point": (lon, lat),
            "proj": (proj_lon, proj_lat),
            "dist": dist,
        })

    kml_text = build_result_kml(results)
    write_kmz_from_kml(kml_text, output_kmz)
    write_csv(results, output_csv)

    print(f"Garis intersection -> {output_kmz}")
    print(f"Tabel jarak        -> {output_csv}")
    print()
    print(f"{'No':<4}{'Nama Titik':<15}{'Jarak (m)':>10}")
    for i, r in enumerate(results, start=1):
        print(f"{i:<4}{r['name']:<15}{r['dist']:>10.3f}")

    return results


# ----------------------------------------------------------------------
# KONFIGURASI (HARD CODE) — ubah bagian ini sesuai kebutuhan
# ----------------------------------------------------------------------

TITIK_KMZ = "titik interpolasi.kmz"                          # file KMZ berisi titik-titik
GARIS_KMZ = "PKKPRL Dumai Rupat Line.kmz"                          # file KMZ berisi garis referensi
OUTPUT_KMZ = "garis_intersection.kmz"            # output: garis intersection
OUTPUT_CSV = "tabel_jarak_intersection.csv"      # output: tabel no & jarak

if __name__ == "__main__":
    intersect_kmz(TITIK_KMZ, GARIS_KMZ, OUTPUT_KMZ, OUTPUT_CSV)