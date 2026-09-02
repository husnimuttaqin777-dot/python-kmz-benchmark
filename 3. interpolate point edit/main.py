"""
main_pyqt5.py
-------------
Versi PyQt5 dari penghubung antara UI (main.qml) dan logika interpolasi
(interpolate.py).

Bedanya dengan versi PySide6 cuma di bagian import & beberapa nama method:
- PySide6.QtCore.Slot        -> PyQt5.QtCore.pyqtSlot
- PySide6.QtGui.QGuiApplication -> PyQt5.QtGui.QGuiApplication  (sama)
- PySide6.QtQml.QQmlApplicationEngine -> PyQt5.QtQml.QQmlApplicationEngine (sama)
- app.exec()                 -> app.exec_()   (pakai underscore di PyQt5)

Instalasi (sekali saja):
    pip install PyQt5

Menjalankan:
    python main_pyqt5.py
(pastikan main_pyqt5.py, main.qml, dan interpolate.py ada di folder yang sama)

Kalau mau nama filenya tetap "main.py", tinggal rename file ini.
"""

import os
import sys
import traceback

from PyQt5.QtCore import QObject, QUrl, pyqtSlot
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtQml import QQmlApplicationEngine
import re
import math
import zipfile
import shutil
import os


# ----------------------------------------------------------------------
# 1. BACA KMZ -> LIST TITIK
# ----------------------------------------------------------------------

def read_kmz_points(kmz_path, work_dir="/tmp/kmz_work"):
    """Ekstrak KMZ dan kembalikan (kml_text, list_of_points).

    list_of_points = [(name, lon, lat), ...] urut sesuai urutan Placemark
    di file KML. Hanya Placemark yang punya <name> dan <coordinates>
    yang diambil.
    """
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    os.makedirs(work_dir)

    with zipfile.ZipFile(kmz_path) as z:
        kml_name = next(n for n in z.namelist() if n.endswith(".kml"))
        z.extractall(work_dir)

    kml_path = os.path.join(work_dir, kml_name)
    with open(kml_path, encoding="utf-8") as f:
        kml_text = f.read()

    points = []
    for pm in re.findall(r"<Placemark[^>]*>(.*?)</Placemark>", kml_text, re.S):
        name_m = re.search(r"<name>(.*?)</name>", pm, re.S)
        coord_m = re.search(r"<coordinates>([^<]+)</coordinates>", pm, re.S)
        if not (name_m and coord_m):
            continue
        name = name_m.group(1).strip()
        lon, lat, *_ = [float(v) for v in coord_m.group(1).strip().split(",")]
        points.append((name, lon, lat))

    return kml_text, kml_path, points


# ----------------------------------------------------------------------
# 2. JARAK & INTERPOLASI GEOMETRI
# ----------------------------------------------------------------------

def haversine_m(p1, p2):
    """Jarak permukaan bumi (meter) antara dua titik (lon, lat)."""
    lon1, lat1 = p1
    lon2, lat2 = p2
    R = 6371000  # radius bumi, meter
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def lerp(p1, p2, t):
    """Interpolasi linear sederhana antara dua koordinat (lon, lat).
    Cukup akurat untuk jarak pendek (puluhan-ratusan meter)."""
    return (p1[0] + (p2[0] - p1[0]) * t, p1[1] + (p2[1] - p1[1]) * t)


def interpolate_segment(p1, p2, spacing):
    """Bagi ruas p1->p2 jadi titik-titik baru dengan jarak ~spacing meter.

    Return list titik BARU di antara p1 dan p2 (tidak termasuk p1),
    TERMASUK p2 di titik terakhir (supaya gampang disambung berurutan).
    Kalau jarak p1-p2 <= spacing, tidak ada titik baru -> hanya [p2].
    """
    dist = haversine_m(p1, p2)
    if dist <= spacing:
        return [p2]

    n_segments = max(1, round(dist / spacing))
    return [lerp(p1, p2, i / n_segments) for i in range(1, n_segments + 1)]


# ----------------------------------------------------------------------
# 3. PROSES SELURUH TITIK: SISIPKAN INTERPOLASI DI GAP YANG BESAR
# ----------------------------------------------------------------------

def build_interpolated_sequence(points, spacing, gap_factor=1.5):
    """Jalan sepanjang list `points` (urut). Untuk tiap ruas antar titik
    yang jaraknya > spacing * gap_factor, sisipkan titik interpolasi baru.

    Return list baru: [(is_new, lon, lat), ...] urut, sudah termasuk
    titik-titik asli maupun titik baru, siap dinomori ulang.
    """
    if not points:
        return []

    result = [(False, points[0][1], points[0][2])]  # titik pertama, asli

    for i in range(len(points) - 1):
        p1 = (points[i][1], points[i][2])
        p2 = (points[i + 1][1], points[i + 1][2])
        dist = haversine_m(p1, p2)

        if dist > spacing * gap_factor:
            # perlu sisipan
            new_pts = interpolate_segment(p1, p2, spacing)
            for j, (lon, lat) in enumerate(new_pts):
                is_last = (j == len(new_pts) - 1)
                result.append((not is_last, lon, lat))  # titik terakhir = titik asli p2
        else:
            # jarak sudah wajar, tidak perlu sisipan, langsung titik asli berikutnya
            result.append((False, p2[0], p2[1]))

    return result


# ----------------------------------------------------------------------
# 4. TULIS KML/KMZ BARU
# ----------------------------------------------------------------------

NEW_STYLE_ID = "interp_baru"
NEW_STYLE_BLOCK = f"""\t<Style id="{NEW_STYLE_ID}">
\t\t<IconStyle>
\t\t\t<color>ff0000ff</color>
\t\t\t<scale>0.45</scale>
\t\t\t<Icon>
\t\t\t\t<href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href>
\t\t\t</Icon>
\t\t</IconStyle>
\t</Style>
"""


def build_kml_placemarks(sequence, start_number=1, name_prefix=""):
    """Bikin blok XML Placemark untuk semua titik hasil interpolasi.
    Titik baru dikasih styleUrl merah supaya beda dari titik asli."""
    blocks = []
    for i, (is_new, lon, lat) in enumerate(sequence):
        name = f"{name_prefix}{start_number + i}"
        style = f"\t\t\t<styleUrl>#{NEW_STYLE_ID}</styleUrl>\n" if is_new else ""
        blocks.append(
            f"\t\t<Placemark>\n\t\t\t<name>{name}</name>\n{style}"
            f"\t\t\t<Point>\n\t\t\t\t<coordinates>{lon:.7f},{lat:.7f},0</coordinates>\n"
            f"\t\t\t</Point>\n\t\t</Placemark>\n"
        )
    return "".join(blocks)


def write_kmz(kml_text, placemark_blocks, output_kmz, work_dir="/tmp/kmz_work"):
    """Ganti SEMUA Placemark lama di kml_text dengan placemark_blocks baru,
    sisipkan definisi style titik baru, lalu zip jadi .kmz."""
    # buang semua Placemark lama
    kml_no_pm = re.sub(r"\t*<Placemark[^>]*>.*?</Placemark>\n?", "", kml_text, flags=re.S)

    # sisipkan style baru + placemark baru sebelum </Document> (atau </Folder> kalau ada)
    insert_before = "</Folder>" if "</Folder>" in kml_no_pm else "</Document>"
    idx = kml_no_pm.rfind(insert_before)
    new_kml = kml_no_pm[:idx] + NEW_STYLE_BLOCK + placemark_blocks + kml_no_pm[idx:]

    out_kml_path = os.path.join(work_dir, "doc.kml")
    with open(out_kml_path, "w", encoding="utf-8") as f:
        f.write(new_kml)

    if os.path.exists(output_kmz):
        os.remove(output_kmz)
    with zipfile.ZipFile(output_kmz, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(out_kml_path, arcname="doc.kml")


# ----------------------------------------------------------------------
# 5. FUNGSI UTAMA
# ----------------------------------------------------------------------

def interpolate_kmz(input_kmz, output_kmz, spacing=10.0, gap_factor=1.5,
                     start_number=1, name_prefix=""):
    """Baca input_kmz, sisipkan titik interpolasi di ruas yang jaraknya
    > spacing * gap_factor, tulis hasilnya ke output_kmz.

    Parameters
    ----------
    spacing : jarak target antar titik (meter)
    gap_factor : ruas dianggap "perlu interpolasi" kalau jaraknya
                 lebih dari spacing * gap_factor (default 1.5x)
    start_number : nomor awal penamaan ulang titik di file hasil
    name_prefix : prefix nama titik, mis. "P" -> P1, P2, ...
    """
    kml_text, _, points = read_kmz_points(input_kmz)
    print(f"Titik terbaca dari {input_kmz}: {len(points)}")

    sequence = build_interpolated_sequence(points, spacing, gap_factor)
    n_new = sum(1 for is_new, *_ in sequence if is_new)
    print(f"Titik baru hasil interpolasi: {n_new}")
    print(f"Total titik setelah interpolasi: {len(sequence)}")

    blocks = build_kml_placemarks(sequence, start_number, name_prefix)
    write_kmz(kml_text, blocks, output_kmz)
    print(f"Selesai -> {output_kmz}")




class Backend(QObject):
    """Objek ini yang diekspos ke QML dengan nama 'backend'."""

    # pyqtSlot(tipe_param1, tipe_param2, ..., result=tipe_kembalian)
    # Semua parameter dari QML TextField berupa string, makanya semua str.
    @pyqtSlot(str,str ,str, str, str)
    def button_run(self, input_path,output_path ,spacing_str, gap_factor_str, start_number_str):
        print(input_path,output_path ,spacing_str, gap_factor_str, start_number_str)
        interpolate_kmz(
            input_path, output_path,
            spacing=int(spacing_str),
            gap_factor=float(gap_factor_str),
            start_number=int(start_number_str),
            name_prefix="",
        )


def main():
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()

    backend = Backend()
    # daftarkan objek python ke context QML dengan nama "backend"
    engine.rootContext().setContextProperty("backend", backend)

    here = os.path.dirname(os.path.abspath(__file__))
    qml_path = os.path.join(here, "main.qml")
    engine.load(QUrl.fromLocalFile(qml_path))

    if not engine.rootObjects():
        # gagal load QML (biasanya karena syntax error di .qml)
        sys.exit(-1)

    sys.exit(app.exec_())  # perhatikan: exec_() dengan underscore di PyQt5


if __name__ == "__main__":
    main()
