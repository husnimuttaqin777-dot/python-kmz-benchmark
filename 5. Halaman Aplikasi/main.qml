import QtQuick 2.12
import QtQuick.Window 2.13
import QtQuick.Controls 2.0
import QtQuick.Controls.Styles 1.4
import QtQuick.Extras 1.4
import QtQuick.Extras.Private 1.0



Window {
	id : root
	width: 400
	//maximumWidth : 1280
	//minimumWidth : width
    height: 400
	//maximumHeight : 800
	//minimumHeight : height
	title:"membuat windows"
	color : "red"
    visible: true
    //flags: Qt.WindowMaximized //Qt.Dialog
	
	
	Rectangle{
		id : button_layout
		width : (parent.width/4) -10
		height : (parent.height) -10
		color : "red"
		border.color : "pink"
		border.width : 4
		
		
		Button{
			id : button_page1
			width : parent.width - 10
			height : (parent.height/4) -8
			text : "1"
			anchors.horizontalCenter: parent.horizontalCenter
			checkable : true
			checked : true
			onClicked:{
				
				button_page2.checked = false
				button_page3.checked = false
				button_page4.checked = false
			}
			
		}
		
		
		Button{
			y : parent.height/4
			id : button_page2
			width : parent.width - 10
			height : (parent.height/4) -8
			text : "2"
			anchors.horizontalCenter: parent.horizontalCenter
			checkable : true
			
			onClicked:{
				
				button_page1.checked = false
				button_page3.checked = false
				button_page4.checked = false
			}
		}
		
		Button{
			y : 2*(parent.height/4)
			id : button_page3
			width : parent.width - 10
			height : (parent.height/4) -8
			text : "3"
			anchors.horizontalCenter: parent.horizontalCenter
			checkable : true
			
			onClicked:{
				
				button_page1.checked = false
				button_page2.checked = false
				button_page4.checked = false
			}
		}
		
		Button{
			y : 3*(parent.height/4)
			id : button_page4
			width : parent.width - 10
			height : (parent.height/4) -8
			text : "4"
			anchors.horizontalCenter: parent.horizontalCenter
			checkable : true
			onClicked:{
				
				button_page1.checked = false
				button_page2.checked = false
				button_page3.checked = false
			}
		}
		
		}
		
		
	
	Rectangle{
		y : parent.height/4
		x : button_layout.width
		color : "red"
		border.color : "pink"
		width : parent.width * 3/4 
		height : (parent.height * 3/4) -10
		visible : button_page1.checked
		
		Text {
			y : -((parent.height * 1/4 ))
			text : "line to dot"
			font.pixelSize : 22
			color : "pink"
			font.family: "Helvetica"
			anchors.horizontalCenter: parent.horizontalCenter
		
		}
		
		}
		
	Rectangle{
		y : parent.height/4
		x : button_layout.width
		color : "red"
		border.color : "pink"
		width : parent.width * 3/4 
		height : (parent.height * 3/4) -10
		visible : button_page2.checked
		
		Text {
			y : -((parent.height * 1/4 ))
			text : "dot to line"
			font.pixelSize : 22
			color : "pink"
			font.family: "Helvetica"
			anchors.horizontalCenter: parent.horizontalCenter
		
		}
		
		}
		
	Rectangle{
		y : parent.height/4
		x : button_layout.width
		color : "red"
		border.color : "pink"
		width : parent.width * 3/4 
		height : (parent.height * 3/4) -10
		visible : button_page3.checked
		
		Text {
			y : -((parent.height * 1/4 ))
			text : "interpolate"
			font.pixelSize : 22
			color : "pink"
			font.family: "Helvetica"
			anchors.horizontalCenter: parent.horizontalCenter
		
		}
		
		}
		
	Rectangle{
		y : parent.height/4
		x : button_layout.width
		color : "red"
		border.color : "pink"
		width : parent.width * 3/4 
		height : (parent.height * 3/4) -10
		visible : button_page4.checked
		
		Text {
			y : -((parent.height * 1/4 ))
			text : "intersection"
			font.pixelSize : 22
			color : "pink"
			font.family: "Helvetica"
			anchors.horizontalCenter: parent.horizontalCenter
		
		}
		
		}
	
	
	
}













