#test update

import zipfile
import xml.etree.ElementTree as ET
import csv
import math

from pyproj import Transformer


# ============================================================
# SETTINGS
# ============================================================

INPUT_KMZ = "batam.kmz"

OUTPUT_KMZ = "batam dots.kmz"

OUTPUT_CSV = "batam dots.csv"

# JARAK ANTAR TITIK
INTERVAL_METER = 25

PREFIX = "P"


# ============================================================
# DETEKSI UTM ZONE
# ============================================================

def get_utm_transformer(lon, lat):

    zone = int((lon + 180) / 6) + 1

    if lat >= 0:
        epsg = 32600 + zone
    else:
        epsg = 32700 + zone

    transformer_to_utm = Transformer.from_crs(
        "EPSG:4326",
        f"EPSG:{epsg}",
        always_xy=True
    )

    transformer_to_wgs84 = Transformer.from_crs(
        f"EPSG:{epsg}",
        "EPSG:4326",
        always_xy=True
    )

    return transformer_to_utm, transformer_to_wgs84


# ============================================================
# BACA LINESTRING DARI KMZ
# ============================================================

def read_kmz_linestring(input_path):

    with zipfile.ZipFile(input_path, "r") as kmz:

        kml_name = next(
            n for n in kmz.namelist()
            if n.lower().endswith(".kml")
        )

        kml_data = kmz.read(kml_name)

    root = ET.fromstring(kml_data)

    ns = {
        "kml": "http://www.opengis.net/kml/2.2"
    }

    lines = []

    for placemark in root.iter(
        "{http://www.opengis.net/kml/2.2}Placemark"
    ):

        for linestring in placemark.findall(
            ".//kml:LineString",
            ns
        ):

            coords_el = linestring.find(
                "kml:coordinates",
                ns
            )

            if coords_el is None:
                continue

            if not coords_el.text:
                continue

            points = []

            for vertex in coords_el.text.strip().split():

                parts = vertex.split(",")

                lon = float(parts[0])
                lat = float(parts[1])

                alt = (
                    float(parts[2])
                    if len(parts) > 2
                    else 0.0
                )

                points.append(
                    (lon, lat, alt)
                )

            if len(points) >= 2:
                lines.append(points)

    return lines


# ============================================================
# INTERPOLASI DALAM KOORDINAT METER
# ============================================================

def interpolate_xy(
    x1,
    y1,
    alt1,
    x2,
    y2,
    alt2,
    distance
):

    dx = x2 - x1
    dy = y2 - y1

    segment_length = math.sqrt(
        dx * dx +
        dy * dy
    )

    if segment_length == 0:
        return x1, y1, alt1

    ratio = distance / segment_length

    x = x1 + dx * ratio
    y = y1 + dy * ratio

    alt = alt1 + (
        alt2 - alt1
    ) * ratio

    return x, y, alt


# ============================================================
# BUAT TITIK DENGAN INTERVAL TEPAT
# ============================================================

def generate_points(
    lines,
    interval_meter,
    transformer_to_utm,
    transformer_to_wgs84
):

    all_points = []

    counter = 1

    for line_number, line in enumerate(lines, start=1):

        # ----------------------------------------------------
        # Convert seluruh vertex ke UTM
        # ----------------------------------------------------

        utm_points = []

        for lon, lat, alt in line:

            x, y = transformer_to_utm.transform(
                lon,
                lat
            )

            utm_points.append(
                (x, y, alt)
            )

        # ----------------------------------------------------
        # Titik pertama
        # ----------------------------------------------------

        x0, y0, alt0 = utm_points[0]

        lon0, lat0 = transformer_to_wgs84.transform(
            x0,
            y0
        )

        all_points.append({
            "no": counter,
            "label": f"{PREFIX}{counter}",
            "lat": lat0,
            "lon": lon0,
            "alt": alt0,
            "distance_previous": 0.0,
            "distance_total": 0.0,
            "line": line_number
        })

        counter += 1

        # Jarak dari titik terakhir yang sudah dibuat
        distance_since_last_point = 0.0

        # Total jarak sepanjang line
        total_distance = 0.0

        # ----------------------------------------------------
        # LOOP SEGMENT
        # ----------------------------------------------------

        for i in range(len(utm_points) - 1):

            x1, y1, alt1 = utm_points[i]

            x2, y2, alt2 = utm_points[i + 1]

            dx = x2 - x1
            dy = y2 - y1

            segment_length = math.sqrt(
                dx * dx +
                dy * dy
            )

            if segment_length <= 0:
                continue

            segment_position = 0.0

            # ------------------------------------------------
            # Bisa ada lebih dari satu titik dalam satu segment
            # ------------------------------------------------

            while True:

                remaining_to_point = (
                    interval_meter
                    - distance_since_last_point
                )

                remaining_segment = (
                    segment_length -
                    segment_position
                )

                # --------------------------------------------
                # Belum cukup untuk membuat titik
                # --------------------------------------------

                if remaining_segment < remaining_to_point:

                    distance_since_last_point += (
                        remaining_segment
                    )

                    total_distance += (
                        remaining_segment
                    )

                    break

                # --------------------------------------------
                # Buat titik
                # --------------------------------------------

                segment_position += remaining_to_point

                total_distance += remaining_to_point

                distance_since_last_point = 0.0

                x, y, alt = interpolate_xy(
                    x1,
                    y1,
                    alt1,
                    x2,
                    y2,
                    alt2,
                    segment_position
                )

                lon, lat = transformer_to_wgs84.transform(
                    x,
                    y
                )

                all_points.append({
                    "no": counter,
                    "label": f"{PREFIX}{counter}",
                    "lat": lat,
                    "lon": lon,
                    "alt": alt,
                    "distance_previous": interval_meter,
                    "distance_total": total_distance,
                    "line": line_number
                })

                counter += 1

                # --------------------------------------------
                # Kalau sudah sampai ujung segment
                # --------------------------------------------

                if (
                    segment_position >=
                    segment_length - 1e-9
                ):

                    break

            # END WHILE

    return all_points


# ============================================================
# BUAT KML
# ============================================================

def create_kml(points):

    placemarks = ""

    for p in points:

        placemarks += f"""
<Placemark>

    <name>{p["label"]}</name>

    <styleUrl>#pointStyle</styleUrl>

    <Point>

        <coordinates>
            {p["lon"]},{p["lat"]},{p["alt"]}
        </coordinates>

    </Point>

</Placemark>
"""

    return f"""<?xml version="1.0" encoding="UTF-8"?>

<kml xmlns="http://www.opengis.net/kml/2.2">

<Document>

    <name>Shore End Points</name>

    <Style id="pointStyle">

        <IconStyle>

            <scale>1.0</scale>

            <Icon>

                <href>
                    http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png
                </href>

            </Icon>

        </IconStyle>

    </Style>

    {placemarks}

</Document>

</kml>
"""


# ============================================================
# SIMPAN KMZ
# ============================================================

def save_kmz(
    kml_data,
    output_path
):

    with zipfile.ZipFile(
        output_path,
        "w",
        zipfile.ZIP_DEFLATED
    ) as kmz:

        kmz.writestr(
            "doc.kml",
            kml_data
        )


# ============================================================
# SIMPAN CSV
# ============================================================

def save_csv(
    points,
    output_path
):

    with open(
        output_path,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "No",
            "Label",
            "Latitude",
            "Longitude",
            "Altitude",
            "Distance Previous (m)",
            "Distance Total (m)",
            "Line"
        ])

        for p in points:

            writer.writerow([
                p["no"],
                p["label"],
                f'{p["lat"]:.8f}',
                f'{p["lon"]:.8f}',
                f'{p["alt"]:.3f}',
                f'{p["distance_previous"]:.3f}',
                f'{p["distance_total"]:.3f}',
                p["line"]
            ])


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("Membaca KMZ...")

    lines = read_kmz_linestring(
        INPUT_KMZ
    )

    if not lines:
        raise RuntimeError(
            "Tidak ditemukan LineString di dalam KMZ."
        )

    print(
        f"Ditemukan {len(lines)} LineString"
    )

    # --------------------------------------------------------
    # Ambil koordinat pertama untuk menentukan UTM zone
    # --------------------------------------------------------

    first_lon = lines[0][0][0]
    first_lat = lines[0][0][1]

    (
        transformer_to_utm,
        transformer_to_wgs84
    ) = get_utm_transformer(
        first_lon,
        first_lat
    )

    # --------------------------------------------------------
    # Generate titik
    # --------------------------------------------------------

    points = generate_points(
        lines,
        INTERVAL_METER,
        transformer_to_utm,
        transformer_to_wgs84
    )

    # --------------------------------------------------------
    # KML
    # --------------------------------------------------------

    kml = create_kml(
        points
    )

    # --------------------------------------------------------
    # KMZ
    # --------------------------------------------------------

    save_kmz(
        kml,
        OUTPUT_KMZ
    )

    # --------------------------------------------------------
    # CSV
    # --------------------------------------------------------

    save_csv(
        points,
        OUTPUT_CSV
    )

    # --------------------------------------------------------
    # REPORT
    # --------------------------------------------------------

    print()
    print("======================================")
    print("SELESAI")
    print("======================================")

    print(
        f"Interval       : {INTERVAL_METER} meter"
    )

    print(
        f"Jumlah titik   : {len(points)}"
    )

    print(
        f"Output KMZ     : {OUTPUT_KMZ}"
    )

    print(
        f"Output CSV     : {OUTPUT_CSV}"
    )

    print("======================================")