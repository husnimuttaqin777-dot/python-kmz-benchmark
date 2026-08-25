import zipfile
import xml.etree.ElementTree as ET

def kmz_points_to_line(input_path, output_path, line_name="Tracking Line"):
    with zipfile.ZipFile(input_path, 'r') as kmz:
        kml_name = next(n for n in kmz.namelist() if n.endswith('.kml'))
        kml_data = kmz.read(kml_name)

    root = ET.fromstring(kml_data)
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}

    points = []
    for placemark in root.iter('{http://www.opengis.net/kml/2.2}Placemark'):
        pt = placemark.find('kml:Point', ns)
        if pt is None:
            continue
        name_el = placemark.find('kml:name', ns)
        try:
            order = int(name_el.text.strip())
        except (AttributeError, ValueError):
            order = len(points)  # fallback: keep document order
        coords_el = pt.find('kml:coordinates', ns)
        if coords_el is not None and coords_el.text:
            lon, lat, *rest = coords_el.text.strip().split(',')
            alt = rest[0] if rest else '0'
            points.append((order, float(lon), float(lat), float(alt)))

    points.sort(key=lambda p: p[0])
    coord_str = ' '.join(f"{lon},{lat},{alt}" for _, lon, lat, alt in points)

    kml_out = f'''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
<name>{line_name}</name>
<Style id="lineStyle">
  <LineStyle>
    <color>ff0000ff</color>
    <width>3</width>
  </LineStyle>
</Style>
<Placemark>
  <name>{line_name}</name>
  <styleUrl>#lineStyle</styleUrl>
  <LineString>
    <tessellate>1</tessellate>
    <coordinates>{coord_str}</coordinates>
  </LineString>
</Placemark>
</Document>
</kml>'''

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as kmz:
        kmz.writestr('doc.kml', kml_out)

    print(f"Converted {len(points)} points into 1 line -> {output_path}")


if __name__ == '__main__':
    kmz_points_to_line(
        'Titik Interpolasi raw.kmz',
        'Titik Interpolasi raw line.kmz',
        line_name='Titik Interpolasi raw'
    )