"""
main.py
-------
Launcher untuk main.qml ("software line to dot").

Alur:
  1. QML memanggil backend.button_run(input_path, output_name, interval_m)
     saat tombol RUN diklik.
  2. Python (Backend) membaca garis (LineString) dari file KMZ input,
     lalu membuat titik-titik di sepanjang garis tersebut dengan jarak
     antar-titik = interval_m (meter, dari slider "Interval Jarak").
  3. Titik-titik itu disimpan sebagai file KMZ baru (nama sesuai
     "Nama File" yang diketik user), plus tabel CSV pendukung.

Cara pakai:
  pip install PyQt5
  python3 main.py

Catatan:
  - main.qml pakai modul QtQuick.Extras 1.4, yang sudah lama tidak
    dikembangkan Qt. Kalau muncul error "module QtQuick.Extras is not
    installed", perlu paket tambahan `PyQt5-QtQuick-Extras` (kalau ada
    di wheel), atau modul itu bisa dihapus dari main.qml karena di sini
    tidak dipakai secara fungsional (hanya di-import).
"""

import sys
import os
import re
import math
import zipfile
import shutil
import csv

from PyQt5.QtCore import QObject, pyqtSlot, QUrl
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtQml import QQmlApplicationEngine


# ----------------------------------------------------------------------
# Helper KMZ / geometri (diadaptasi dari intersection.py)
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


def read_lines_kmz(kmz_path, work_dir="/tmp/line2dot_garis_work"):
    """Baca semua Placemark ber-geometri <LineString> dari file KMZ.
    Return list of polylines, tiap polyline = list [(lon, lat), ...]."""
    kml_text = _extract_kml(kmz_path, work_dir)
    lines = []
    for pm in re.findall(r"<Placemark[^>]*>(.*?)</Placemark>", kml_text, re.S):
        coord_m = re.search(
            r"<LineString[^>]*>.*?<coordinates>([^<]+)</coordinates>.*?</LineString>",
            pm, re.S,
        )
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


def haversine_m(p1, p2):
    lon1, lat1 = p1
    lon2, lat2 = p2
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _deg_to_local(lon, lat, ref_lon, ref_lat):
    x = (lon - ref_lon) * 111320 * math.cos(math.radians(ref_lat))
    y = (lat - ref_lat) * 110540
    return x, y


def _local_to_deg(x, y, ref_lon, ref_lat):
    lon = x / (111320 * math.cos(math.radians(ref_lat))) + ref_lon
    lat = y / 110540 + ref_lat
    return lon, lat


def points_along_polyline(local_verts, interval_m):
    """Sampling titik tiap `interval_m` meter di sepanjang satu polyline
    (koordinat lokal meter). Titik awal polyline selalu ikut disertakan."""
    if len(local_verts) < 2:
        return list(local_verts)

    pts = [local_verts[0]]
    remaining = interval_m
    for i in range(len(local_verts) - 1):
        ax, ay = local_verts[i]
        bx, by = local_verts[i + 1]
        seg_len = math.hypot(bx - ax, by - ay)
        if seg_len == 0:
            continue
        pos = 0.0
        while remaining <= seg_len - pos:
            pos += remaining
            t = pos / seg_len
            px = ax + t * (bx - ax)
            py = ay + t * (by - ay)
            pts.append((px, py))
            remaining = interval_m
        remaining -= (seg_len - pos)
    return pts


def generate_dots_from_lines(polylines, interval_m):
    """Return list of (lon, lat) titik hasil sampling seluruh polyline."""
    all_verts = [v for line in polylines for v in line]
    ref_lon = sum(v[0] for v in all_verts) / len(all_verts)
    ref_lat = sum(v[1] for v in all_verts) / len(all_verts)

    all_points_deg = []
    for verts in polylines:
        local_verts = [_deg_to_local(lo, la, ref_lon, ref_lat) for lo, la in verts]
        local_pts = points_along_polyline(local_verts, interval_m)
        for lx, ly in local_pts:
            all_points_deg.append(_local_to_deg(lx, ly, ref_lon, ref_lat))
    return all_points_deg


# ----------------------------------------------------------------------
# Tulis KMZ hasil (titik-titik)
# ----------------------------------------------------------------------

POINT_STYLE_ID = "titik_hasil"

STYLE_BLOCK = f"""\t<Style id="{POINT_STYLE_ID}">
\t\t<IconStyle>
\t\t\t<color>ff00a5ff</color>
\t\t\t<scale>0.6</scale>
\t\t\t<Icon>
\t\t\t\t<href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href>
\t\t\t</Icon>
\t\t</IconStyle>
\t</Style>
"""


def build_dot_kml(points):
    placemarks = []
    for i, (lon, lat) in enumerate(points, start=1):
        placemarks.append(
            f'\t\t<Placemark>\n\t\t\t<name>Titik {i}</name>\n'
            f'\t\t\t<styleUrl>#{POINT_STYLE_ID}</styleUrl>\n'
            f'\t\t\t<Point>\n\t\t\t\t<coordinates>{lon:.7f},{lat:.7f},0</coordinates>\n'
            f'\t\t\t</Point>\n\t\t</Placemark>\n'
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<kml xmlns="http://www.opengis.net/kml/2.2">\n<Document>\n'
        '\t<name>Line to Dot</name>\n'
        + STYLE_BLOCK
        + "".join(placemarks)
        + "</Document>\n</kml>\n"
    )


def write_kmz_from_kml(kml_text, output_kmz, work_dir="/tmp/line2dot_out"):
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


def write_csv(points, output_csv):
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["No", "Nama Titik", "Latitude", "Longitude", "Jarak Kumulatif (m)"])
        cum = 0.0
        for i, (lon, lat) in enumerate(points, start=1):
            if i > 1:
                cum += haversine_m(points[i - 2], points[i - 1])
            writer.writerow([i, f"Titik {i}", f"{lat:.7f}", f"{lon:.7f}", f"{cum:.3f}"])


# ----------------------------------------------------------------------
# Backend yang dipanggil dari QML
# ----------------------------------------------------------------------

class Backend(QObject):

    @pyqtSlot(str, str, float)
    def button_run(self, input_path, output_name, interval_m):
        try:
            input_path = input_path.strip()
            output_name = output_name.strip() or "hasil_line_to_dot"
            if interval_m <= 0:
                interval_m = 10.0  # default kalau slider di posisi 0

            if not os.path.isfile(input_path):
                print(f"[ERROR] File input tidak ditemukan: {input_path}")
                return

            polylines = read_lines_kmz(input_path)
            if not polylines:
                print("[ERROR] Tidak ada LineString ditemukan di file KMZ input.")
                return

            points = generate_dots_from_lines(polylines, interval_m)

            out_dir = os.path.dirname(input_path) or "."
            output_kmz = os.path.join(out_dir, f"{output_name}.kmz")
            output_csv = os.path.join(out_dir, f"{output_name}.csv")

            kml_text = build_dot_kml(points)
            write_kmz_from_kml(kml_text, output_kmz)
            write_csv(points, output_csv)

            print(f"[OK] {len(points)} titik dibuat (interval {interval_m} m)")
            print(f"[OK] KMZ -> {output_kmz}")
            print(f"[OK] CSV -> {output_csv}")

        except Exception as e:
            print(f"[ERROR] Gagal memproses: {e}")


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------

def main():
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()

    backend = Backend()
    engine.rootContext().setContextProperty("backend", backend)

    qml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.qml")
    engine.load(QUrl.fromLocalFile(qml_path))

    if not engine.rootObjects():
        sys.exit("Gagal memuat main.qml")

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
  