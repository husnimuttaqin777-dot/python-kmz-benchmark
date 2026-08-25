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
	width: 700
	maximumWidth : width
	minimumWidth : width
    height: 400
	maximumHeight : height
	minimumHeight : height
	title:"membuat windows"
	color : "grey"
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
	text:"software dot to line"
	color: "#00FF00"
	font.family  : "Comic Sans MS"
	font.pixelSize: 25
	font.bold : true	
	
	
	}
	
	
	Text{
	id : file_input_text
	x:0
	y:40
	text:"input dir"
	color: "#00FF00"
	font.family  : "Comic Sans MS"
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
	color: "#00FF00"
	font.family  : "Comic Sans MS"
	font.pixelSize: 16
	font.bold : true	
	
	Button{
	 x :0
	 y :50
	 text : "RUN"
	 onClicked:{
	 backend.button_run(file_input_text.text, file_output_text.text, line_color.text)
	 
	 }
	}
	
	
	}
	
	
	Button{
	 x:0
	y:250
	 text : "SELECT COLOR"
	 onClicked:{
	 colorDialog.visible = true
	 }
	}
	
	Text{
	id : line_color
	x:0
	y:300
	text:"#ffff0000"
	color: "#00FF00"
	font.family  : "Comic Sans MS"
	font.pixelSize: 16
	font.bold : true	
	visible : true
	
	
	
	
	
	}
	
	ColorDialog {
        id: colorDialog
        title: "Pilih Warna"
		visible : false
        onAccepted: {
            var kmlColor = colorToKml(colorDialog.color)
        console.log(kmlColor)
			line_color.text  = "#" + kmlColor
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












