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
	width: 1000
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
	text:"SOFTWARE INTERSECTION"
	color: "#87CEEB"
	font.family  : "seven segment"
	font.pixelSize: 25
	font.bold : true	
	}
	
	
	Text{
	id : file_input_text
	x:10
	y:125
	text:"input line"
	color: "#87CEEB"
	font.family  : "seven segment"
	font.pixelSize: 16
	font.bold : true
	}
	
	Text{
	id : file_input_line
	x:0
	y:50
	text:"input point"
	color: "#87CEEB"
	font.family  : "seven segment"
	font.pixelSize: 16
	font.bold : true
	}
	
	Button{
	 x :0
	 y :75
	 text : "select file"
	 onClicked: file_select.open()
	}
	
	Button{
	 x :0
	 y :150
	 text : "select file"
	 onClicked: file_select1.open()
	}

	TextField{
	id : file_output_text
	x:0
	y:220
	text:""
	color: "black"
	font.family  : "seven segment"
	font.pixelSize: 16
	font.bold : true	
	}
	
	Text{
	id : output_name
	x:50
	y:200
	text:"Nama File"
	color: "#87CEEB"
	font.family  : "seven segment"
	font.pixelSize: 16
	font.bold : true	
	}
	
	Button{
	 x :-10
	 y :280
	 text : "RUN"
	onClicked:{
	 backend.button_run(file_input_text.text, file_input_line.text, file_output_text.text)
	 
	 }
	}

	 FileDialog {
        id: file_select
        title: "Pilih sebuah file"

        onAccepted: {
		 file_input_text.text = String(file_select.fileUrl).replace("file:///", "")
		 console.log("file_input_text")
        }
		
	
	}
	
	
	FileDialog {
        id: file_select1
        title: "Pilih sebuah file"

        onAccepted: {
		 file_input_line.text = String(file_select1.fileUrl).replace("file:///", "")
		 console.log("file_input_line")
        }
		
	
	}
		
		
		
}
	 












