import QtQuick 2.12
import QtQuick.Window 2.13
import QtQuick.Controls 2.0
import QtQuick.Controls.Styles 1.4
import QtQuick.Extras 1.4
import QtQuick.Extras.Private 1.0
import QtQuick.Dialogs 1.3


Window {
	flags: Qt.Dialog
	id : root
	width: 350
	maximumWidth : width
	minimumWidth : width
    height: 350
	maximumHeight : height
	minimumHeight : height
	title:"membuat windows"
	color : "#0B0B45"
    visible: true
	
	function colorToKml(color) {
		var r = Math.round(color.r * 255)
		var g = Math.round(color.g * 255)
		var b = Math.round(color.b * 255)
		var a = Math.round(color.a * 255)

		function hex(v) {
			return v.toString(16).padStart(2, "0")
		}

		return hex(a) + hex(b) + hex(g) + hex(r)
	}
    
	
	Text{
	id : text1
	x:0
	y:0
	text:"software line to dot"
	color: "#87CEEB"
	font.family  : "seven segment"
	font.pixelSize: 25
	font.bold : true	
	
	
	}
	
	
	Text{
	id : file_input_text
	x:0
	y:40
	text:"input dir"
	color: "#87CEEB"
	font.family  : "seven segment"
	font.pixelSize: 16
	font.bold : true	
	
	Button{
	 x :0
	 y :30
	 text : "select file"
	 onClicked: file_select.open()
	}
	
	
	}
	
	
	TextField{
	id : file_output_text
	x:0
	y:150
	text:""
	color: "black"
	font.family  : "seven segment"
	font.pixelSize: 16
	font.bold : true	
	
	Text{
	id : named_file
	x:0
	y:-30
	text:"Nama File"
	color: "#87CEEB"
	font.family  : "seven segment"
	font.pixelSize: 16
	font.bold : true	
	}
	
	Text{
	id : file_nominal
	x:0
	y:45
	text:"Interval Jarak"
	color: "#87CEEB"
	font.family  : "seven segment"
	font.pixelSize: 16
	font.bold : true	
	
	
	
	Button{
	 x :-10
	 y :80
	 text : "RUN"
	 onClicked:{
	 backend.button_run(file_input_text.text, file_output_text.text, slider1.value)
	 
	 }
	}
	}
	
	}
	
	Button{
	 x:10
	y:200
	visible : false
	 text : "SELECT COLOR"
	 onClicked:{
	 colorDialog.visible = true
	 }
	}
	
	Slider {
		id: slider1
		x:-10
		y:220
		height: 20
		width: 250
		value: 0
		from:0
		to: 300
		stepSize: 10
		orientation: Qt.Horizontal
		onValueChanged: {
		}
		
		Text{
			id : interval_jarak
			x:20
			y:30
			text:slider1.value
			color: "#87CEEB"
			font.family  : "seven segment"
			font.pixelSize: 16
			font.bold : true	
			
			
			}
}


	
	
	
	
	 FileDialog {
        id: file_select
        title: "Pilih sebuah file"

        onAccepted: {
		 file_input_text.text = String(file_select.fileUrl).replace("file:///", "")
        }
    }
}












