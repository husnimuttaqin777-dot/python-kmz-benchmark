"""
Skrip untuk mewarnai jalur kabel (garis) berdasarkan kedalaman yang diambil
dari peta kontur, lalu menyimpannya sebagai file .kmz baru.

Cara pakai:
    python pewarnaan_kabel.py

atau import dan panggil langsung:
    from pewarnaan_kabel import process
    process("JALUR_KABEL_DUMAI.kmz", "dumai_kontur_baru.kmz", "hasil.kmz")

Ketergantungan (install sekali):
    pip install scipy numpy simplekml --break-system-packages
"""

import os
import shutil
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter

import numpy as np
from scipy.interpolate import griddata, NearestNDInterpolator
import simplekml

NS = {"kml": "http://www.opengis.net/kml/2.2"}

# ---------------------------------------------------------------------------
# Batas kedalaman (meter) & warna -> UBAH DI SINI kalau perlu
# ---------------------------------------------------------------------------
BATAS_KEDALAMAN = [10.0, 15.0]   # pemisah kelas: 0-10 | 10-15 | 15-keatas

WARNA_KML = {
    # format KML: aabbggrr (alpha, biru, hijau, merah)
    "hijau":  "ff00c853",
    "kuning": "ff00d7ff",
    "merah":  "ff2020e6",
}

LABEL_KELAS = {
    "hijau":  "0 - 10 m (Hijau)",
    "kuning": "10 - 15 m (Kuning)",
    "merah":  "15 - 28 m (Merah)",
}


# ---------------------------------------------------------------------------
# Util: baca file .kml ATAU .kmz (kmz akan diekstrak dulu ke folder sementara)
# ---------------------------------------------------------------------------
def _load_kml_root(path):
    """Mengembalikan root ElementTree dari file .kml atau .kmz."""
    if path.lower().endswith(".kmz"):
        with tempfile.TemporaryDirectory() as tmp:
            with zipfile.ZipFile(path, "r") as z:
                kml_names = [n for n in z.namelist() if n.lower().endswith(".kml")]
                if not kml_names:
                    raise ValueError(f"Tidak ada file .kml di dalam {path}")
                z.extract(kml_names[0], tmp)
                tree = ET.parse(os.path.join(tmp, kml_names[0]))
                return tree.getroot()
    else:
        tree = ET.parse(path)
        return tree.getroot()


# ---------------------------------------------------------------------------
# 1. Ambil semua titik kontur beserta kedalamannya
#    (nama tiap Placemark kontur dianggap sebagai nilai kedalaman, contoh: -13)
# ---------------------------------------------------------------------------
def _baca_titik_kontur(input_contour):
    root = _load_kml_root(input_contour)
    titik = []
    for pm in root.iter("{http://www.opengis.net/kml/2.2}Placemark"):
        name_el = pm.find("kml:name", NS)
        ls = pm.find(".//kml:LineString/kml:coordinates", NS)
        if name_el is None or ls is None or not name_el.text:
            continue
        try:
            kedalaman = abs(float(name_el.text.strip()))
        except ValueError:
            continue
        for c in ls.text.strip().split():
            lon, lat, *_ = c.split(",")
            titik.append((float(lon), float(lat), kedalaman))

    if not titik:
        raise ValueError(
            "Tidak ditemukan titik kontur dengan nama berupa angka kedalaman. "
            "Pastikan setiap garis kontur punya <name> berisi nilai kedalaman."
        )
    return np.array(titik)


# ---------------------------------------------------------------------------
# 2. Ambil semua titik garis kabel, urut sesuai urutan aslinya
# ---------------------------------------------------------------------------
def _baca_titik_kabel(input_line):
    root = _load_kml_root(input_line)
    titik = []
    for pm in root.iter("{http://www.opengis.net/kml/2.2}Placemark"):
        ls = pm.find(".//kml:LineString/kml:coordinates", NS)
        if ls is None:
            continue
        for c in ls.text.strip().split():
            parts = c.split(",")
            lon, lat = float(parts[0]), float(parts[1])
            alt = float(parts[2]) if len(parts) > 2 else 0.0
            titik.append((lon, lat, alt))

    if not titik:
        raise ValueError("Tidak ditemukan garis (LineString) pada file jalur kabel.")
    return np.array(titik)


# ---------------------------------------------------------------------------
# 3. Kelaskan kedalaman -> nama warna
# ---------------------------------------------------------------------------
def _klasifikasi(depth):
    b1, b2 = BATAS_KEDALAMAN
    if depth <= b1:
        return "hijau"
    elif depth <= b2:
        return "kuning"
    else:
        return "merah"


# ---------------------------------------------------------------------------
# 4. Fungsi utama
# ---------------------------------------------------------------------------
def process(input_line, input_contour, output_file):
    """
    Mewarnai garis kabel (input_line) berdasarkan kedalaman yang
    diinterpolasi dari garis kontur (input_contour), lalu menyimpan
    hasilnya sebagai file .kmz (output_file).

    Parameters
    ----------
    input_line : str
        Path file .kmz/.kml berisi garis jalur kabel.
    input_contour : str
        Path file .kmz/.kml berisi garis-garis kontur kedalaman
        (nama tiap garis = nilai kedalaman, misal "-13").
    output_file : str
        Path file .kmz hasil (akan dibuat/ditimpa).
    """
    print(f"[1/5] Membaca kontur dari: {input_contour}")
    kontur_pts = _baca_titik_kontur(input_contour)
    xy_kontur = kontur_pts[:, :2]
    z_kontur = kontur_pts[:, 2]
    print(f"      -> {len(kontur_pts)} titik kontur, kedalaman {z_kontur.min():.1f} - {z_kontur.max():.1f} m")

    print(f"[2/5] Membaca jalur kabel dari: {input_line}")
    kabel_pts = _baca_titik_kabel(input_line)
    xy_kabel = kabel_pts[:, :2]
    print(f"      -> {len(kabel_pts)} titik kabel")

    print("[3/5] Menginterpolasi kedalaman di sepanjang jalur kabel...")
    depth_linear = griddata(xy_kontur, z_kontur, xy_kabel, method="linear")
    nn = NearestNDInterpolator(xy_kontur, z_kontur)
    depth_nn = nn(xy_kabel)
    depth = np.where(np.isnan(depth_linear), depth_nn, depth_linear)
    print(f"      -> kedalaman kabel: {depth.min():.1f} - {depth.max():.1f} m")

    print("[4/5] Memotong garis di titik perbatasan kelas kedalaman & mewarnai...")
    refined = []  # setiap elemen: [lon, lat, alt, depth]
    n = len(kabel_pts)
    for i in range(n):
        lon, lat, alt = kabel_pts[i]
        refined.append([lon, lat, alt, depth[i]])
        if i < n - 1:
            lon1, lat1, alt1 = kabel_pts[i + 1]
            d0, d1 = depth[i], depth[i + 1]
            crossings = []
            for b in BATAS_KEDALAMAN:
                lo, hi = min(d0, d1), max(d0, d1)
                if lo < b < hi:
                    t = (b - d0) / (d1 - d0)
                    crossings.append((t, b))
            crossings.sort(key=lambda x: x[0])
            for t, b in crossings:
                refined.append([
                    lon + t * (lon1 - lon),
                    lat + t * (lat1 - lat),
                    alt + t * (alt1 - alt),
                    b,
                ])

    kelas = [_klasifikasi(r[3]) for r in refined]

    # kelompokkan jadi segmen dengan kelas yang sama (berurutan)
    segmen = []
    kelas_sekarang = kelas[0]
    titik_sekarang = [refined[0][:3]]
    for i in range(1, len(refined)):
        titik_sekarang.append(refined[i][:3])
        if kelas[i] != kelas_sekarang:
            segmen.append((kelas_sekarang, titik_sekarang))
            titik_sekarang = [refined[i][:3]]  # sambung dari titik yang sama
            kelas_sekarang = kelas[i]
    segmen.append((kelas_sekarang, titik_sekarang))

    ringkasan = Counter(s[0] for s in segmen)
    print(f"      -> {len(segmen)} segmen: {dict(ringkasan)}")

    print(f"[5/5] Menyimpan hasil ke: {output_file}")
    kml = simplekml.Kml(name=os.path.basename(output_file))

    style_per_kelas = {}
    for kelas_nama, warna in WARNA_KML.items():
        st = simplekml.Style()
        st.linestyle.color = warna
        st.linestyle.width = 4
        style_per_kelas[kelas_nama] = st

    folder = kml.newfolder(name="Jalur Kabel per Kedalaman")
    for kelas_nama, titik_list in segmen:
        coords = [(p[0], p[1], p[2]) for p in titik_list]
        line = folder.newlinestring(name=LABEL_KELAS[kelas_nama], coords=coords)
        line.style = style_per_kelas[kelas_nama]
        line.altitudemode = simplekml.AltitudeMode.clamptoground
        line.tessellate = 1

    # simpan sebagai .kml sementara lalu bungkus jadi .kmz
    if not output_file.lower().endswith(".kmz"):
        output_file = output_file + ".kmz"

    with tempfile.TemporaryDirectory() as tmp:
        kml_path = os.path.join(tmp, "doc.kml")
        kml.save(kml_path)
        with zipfile.ZipFile(output_file, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(kml_path, arcname="doc.kml")

    print("Selesai.")
    return output_file


if __name__ == "__main__":
    # -------------------------------------------------------------
    # UBAH 3 BARIS INI SESUAI NAMA FILE KAMU
    # -------------------------------------------------------------
    input_line = "JALUR KABEL DUMAI.kmz"
    input_contour = "dumai kontur baru.kmz"
    output_file = "JALUR_KABEL_DUMAI_by_kedalaman.kmz"

    process(input_line, input_contour, output_file)
