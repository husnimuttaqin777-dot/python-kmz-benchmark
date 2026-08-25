######  PROGRAM MEMANGGIL WINDOWS PYQT5 ##########################

####### memanggil library PyQt5 ##################################
#----------------------------------------------------------------#
from PyQt5.QtCore import * 
from PyQt5.QtGui import * 
from PyQt5.QtQml import * 
from PyQt5.QtWidgets import *
from PyQt5.QtQuick import *  
import sys
#----------------------------------------------------------------#


##################################################################
#----------------deklarasi variabel------------------------------#
analog = 60
input1_color = "#df1c39"
input2_color = "#df1c39"


import zipfile
import xml.etree.ElementTree as ET

def kmz_points_to_line(input_path, output_path,color ,line_name="Tracking Line"):
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
    <color>{color}</color>
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



########## mengisi class table dengan instruksi pyqt5#############
#----------------------------------------------------------------#
class table(QObject):    
    def __init__(self, parent = None):
        super().__init__(parent)
        self.app = QApplication(sys.argv)
        self.engine = QQmlApplicationEngine(self)
        self.engine.rootContext().setContextProperty("backend", self)    
        self.engine.load(QUrl("main.qml"))
        sys.exit(self.app.exec_())
    
    
    
    #####################TOMBOL QML KE PYTHON###################
    
    @pyqtSlot(str, str, str)
    def button_run(self, input_file,output_file, color):
        print("input", input_file)
        print("output", output_file)
        
        kmz_points_to_line(str(input_file), str(output_file),color ,line_name='none')
        
        print("berhasil")
        
        
        
    '''
    
        
    
    
    
    @pyqtSlot(result=str)
    def get_input2_color(self):  return input2_color
    '''
#----------------------------------------------------------------#

########## memanggil class table di mainloop######################
#----------------------------------------------------------------#    
if __name__ == "__main__":
    main = table()
    
    
#----------------------------------------------------------------#