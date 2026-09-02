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
	text:"SOFTWARE INTERPOLATE"
	color: "#87CEEB"
	font.family  : "seven segment"
	font.pixelSize: 25
	font.bold : true	
	}
	
	
	Text{
	id : file_input_text
	x:10
	y:35
	text:"input file"
	color: "#87CEEB"
	font.family  : "seven segment"
	font.pixelSize: 16
	font.bold : true
	}
	
	Button{
	 x :0
	 y :60
	 text : "select file"
	 onClicked: file_select.open()
	}

	TextField {
    id: spacing
    x: 0
    y: 150
    text: ""
    color: "black"
    font.family: "seven segment"
    font.pixelSize: 16
    font.bold: true

    validator: DoubleValidator {
        bottom: 0
        top: 9999999
        decimals: 3              // jumlah digit di belakang koma yang diizinkan
        notation: DoubleValidator.StandardNotation
    }


    placeholderText: "SPACING (Meter)"
}

TextField {
    id: gap_factor
    x: 0
    y: 190
    text: ""
    color: "black"
    font.family: "seven segment"
    font.pixelSize: 16
    font.bold: true

   validator: DoubleValidator {
        bottom: 0
        top: 9999999
        decimals: 3              // jumlah digit di belakang koma yang diizinkan
        notation: DoubleValidator.StandardNotation
    }

    placeholderText: "GAP FACTOR"
}

TextField {
    id: start_number
    x: 0
    y: 230
    text: ""
    color: "black"
    font.family: "seven segment"
    font.pixelSize: 16
    font.bold: true

   validator: DoubleValidator {
        bottom: 0
        top: 9999999
        decimals: 3              // jumlah digit di belakang koma yang diizinkan
        notation: DoubleValidator.StandardNotation
    }


    placeholderText: "START NUMBER"
}

TextField {
    id: output_text
    x: 250
    y: 190
    text: ""
    color: "black"
    font.family: "seven segment"
    font.pixelSize: 16
    font.bold: true
	placeholderText: "Output File"
	}
	
	Text{
	id : output_name
	x:50
	y:125
	text:"Input Variabel"
	color: "#87CEEB"
	font.family  : "seven segment"
	font.pixelSize: 16
	font.bold : true	
	}
	
	Text{
	id : output_file
	x:300
	y:155
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
	 backend.button_run(file_input_text.text,output_text.text ,spacing.text, gap_factor.text, start_number.text)
	 
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
	
	

		
}
	 












