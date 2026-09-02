"""
main.py
========================================================
Entry point aplikasi "software line to dot".

Alur kerja:
1. File ini memuat main.qml sebagai GUI (PyQt5 + QtQuick).
2. Class Backend didaftarkan ke QML dengan nama "backend",
   sesuai yang dipanggil di main.qml:
       backend.button_run(input, output, warna, interval)
3. Saat tombol RUN di GUI ditekan, method Backend.button_run()
   di bawah akan dieksekusi, dan ia memanggil ulang
   fungsi-fungsi yang sudah ada di line_to_dot.py
   (read_kmz_linestring, generate_points, create_kml, dst).

Requirement:
    pip install PyQt5 pyproj
========================================================
"""

import os
import sys

from PyQt5.QtCore import QObject, QUrl, pyqtSlot
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtQml import QQmlApplicationEngine

import line_to_dot as ltd


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Backend(QObject):
    """
    Jembatan antara GUI (main.qml) dan logic Python (line_to_dot.py).
    Nama method & jumlah parameter di sini HARUS cocok dengan
    yang dipanggil dari QML lewat objek "backend".
    """

    @pyqtSlot(str, str, float)
    def button_run(self, input_path, output_name, interval_meter):

        input_path = input_path.strip()
        output_name = output_name.strip()

        # --------------------------------------------------
        # Validasi input dari GUI
        # --------------------------------------------------

        if not input_path:
            print("[ERROR] File input belum dipilih (klik 'select file' dulu).")
            return

        if not os.path.isfile(input_path):
            print(f"[ERROR] File tidak ditemukan: {input_path}")
            return

        if not output_name:
            output_name = "output"

        # Kalau slider masih di posisi 0, pakai default dari line_to_dot.py
        interval = interval_meter if interval_meter > 0 else ltd.INTERVAL_METER

        print("======================================")
        print("Memproses file line_to_dot...")
        print(f"Input          : {input_path}")
        print(f"Interval       : {interval_meter}")


        try:
            # ------------------------------------------------
            # Panggil ulang fungsi-fungsi dari line_to_dot.py
            # ------------------------------------------------

            lines = ltd.read_kmz_linestring(input_path)

            if not lines:
                print("[ERROR] Tidak ditemukan LineString di dalam KMZ.")
                return

            first_lon = lines[0][0][0]
            first_lat = lines[0][0][1]

            transformer_to_utm, transformer_to_wgs84 = ltd.get_utm_transformer(
                first_lon,
                first_lat
            )

            points = ltd.generate_points(
                lines,
                interval,
                transformer_to_utm,
                transformer_to_wgs84
            )

            kml_data = ltd.create_kml(points)

            # Simpan output di folder yang sama dengan file input
            output_dir = os.path.dirname(input_path) or BASE_DIR

            output_kmz_path = os.path.join(output_dir, f"{output_name}.kmz")
            output_csv_path = os.path.join(output_dir, f"{output_name}.csv")

            ltd.save_kmz(kml_data, output_kmz_path)
            ltd.save_csv(points, output_csv_path)

            print(f"Jumlah titik   : {len(points)}")
            print(f"Output KMZ     : {output_kmz_path}")
            print(f"Output CSV     : {output_csv_path}")
            print("SELESAI")
            print("======================================")

        except Exception as e:
            print(f"[ERROR] Gagal memproses file: {e}")


def main():

    app = QGuiApplication(sys.argv)

    engine = QQmlApplicationEngine()

    # Daftarkan backend ke QML dengan nama "backend"
    backend = Backend()
    engine.rootContext().setContextProperty("backend", backend)

    qml_path = os.path.join(BASE_DIR, "main.qml")
    engine.load(QUrl.fromLocalFile(qml_path))

    if not engine.rootObjects():
        print("[ERROR] Gagal memuat main.qml")
        sys.exit(-1)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
