import zipfile
import xml.etree.ElementTree as ET


def kmz_line_to_points(input_path, output_path, prefix="P"):
    """Read all LineStrings in a KMZ and split their vertices into
    individual Point placemarks, saved into a new KMZ."""
    with zipfile.ZipFile(input_path, 'r') as kmz:
        kml_name = next(n for n in kmz.namelist() if n.endswith('.kml'))
        kml_data = kmz.read(kml_name)

    root = ET.fromstring(kml_data)
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}

    all_points = []  # list of (label, lon, lat, alt)
    counter = 1

    for placemark in root.iter('{http://www.opengis.net/kml/2.2}Placemark'):
        for linestring in placemark.findall('.//kml:LineString', ns):
            coords_el = linestring.find('kml:coordinates', ns)
            if coords_el is None or not coords_el.text:
                continue
            for vertex in coords_el.text.strip().split():
                parts = vertex.split(',')
                lon, lat = float(parts[0]), float(parts[1])
                alt = float(parts[2]) if len(parts) > 2 else 0.0
                label = f"{prefix}{counter}"
                all_points.append((label, lon, lat, alt))
                counter += 1

    # Build KML with one Placemark per point
    placemarks_xml = ''
    for label, lon, lat, alt in all_points:
        placemarks_xml += f'''<Placemark>
  <name>{label}</name>
  <Point>
    <coordinates>{lon},{lat},{alt}</coordinates>
  </Point>
</Placemark>
'''

    kml_out = f'''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
<name>Points from Lines</name>
<Style id="pointStyle">
  <IconStyle>
    <scale>1.0</scale>
    <Icon>
      <href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href>
    </Icon>
  </IconStyle>
</Style>
{placemarks_xml}</Document>
</kml>'''

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as kmz:
        kmz.writestr('doc.kml', kml_out)

    print(f"Extracted {len(all_points)} points from line(s) -> {output_path}")
    return all_points


if __name__ == '__main__':
    kmz_line_to_points(
        'PKKPRL Dumai Rupat line.kmz',
        'perhitungan posisi shore end dots.kmz',
        prefix='P'
    )