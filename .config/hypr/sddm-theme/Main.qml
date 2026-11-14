// SDDM theme that mirrors ~/.config/hypr/hyprlock.conf: blurred wallpaper, big clock,
// date, rounded password box with a gradient ring, user name, power buttons.
// Colours and wallpaper come from theme.conf (written by ~/.config/hypr/scripts/sddm-sync).
import QtQuick
import QtQuick.Effects

Rectangle {
    id: root
    width: 1920; height: 1200
    color: "black"

    readonly property string mono: "PaperMono Nerd Font"
    property string userName: userModel.lastUser
    property int sessionIndex: -1
    property bool failed: false

    // pick the Hyprland (uwsm-managed) session; remember the user
    ListView { model: sessionModel; visible: false
        delegate: Item { Component.onCompleted: {
            if (root.sessionIndex < 0 || String(file).indexOf("hyprland-uwsm") >= 0) root.sessionIndex = index } } }
    ListView { model: userModel; visible: false
        delegate: Item { Component.onCompleted: { if (!root.userName) root.userName = name } } }

    // --- background: wallpaper, blurred and darkened (like hyprlock) ---
    Image {
        anchors.fill: parent; source: config.background
        fillMode: Image.PreserveAspectCrop
        sourceSize.width: root.width; sourceSize.height: root.height   // fit to screen first
        layer.enabled: true
        layer.effect: MultiEffect { blurEnabled: true; blur: 1.0; blurMax: 40; brightness: -0.25 }
    }

    // --- clock + date ---
    Text {
        id: clock
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.verticalCenter; anchors.verticalCenterOffset: -220
        color: config.clock; font.family: root.mono; font.pixelSize: 140; font.bold: true
        text: Qt.formatTime(new Date(), "HH:mm")
        layer.enabled: true
        layer.effect: MultiEffect { shadowEnabled: true; shadowColor: "#99000000"; shadowBlur: 0.6 }
    }
    Text {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.verticalCenter; anchors.verticalCenterOffset: -110
        color: config.date; font.family: root.mono; font.pixelSize: 28
        text: Qt.formatDate(new Date(), "dddd, dd MMMM")
    }
    Timer { interval: 1000; running: true; repeat: true
            onTriggered: clock.text = Qt.formatTime(new Date(), "HH:mm") }

    // --- password box: gradient ring + light inner box, rounded 19 ---
    Item {
        id: field
        width: 320; height: 56
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.verticalCenter; anchors.verticalCenterOffset: 40
        Rectangle {               // ring (2 px gradient)
            anchors.fill: parent; radius: 19
            gradient: Gradient { orientation: Gradient.Horizontal
                GradientStop { position: 0.0; color: root.failed ? config.fail1 : config.ring1 }
                GradientStop { position: 1.0; color: root.failed ? config.fail2 : config.ring2 } }
            layer.enabled: true
            layer.effect: MultiEffect { shadowEnabled: true; shadowColor: "#88000000"; shadowBlur: 0.8 }
        }
        Rectangle {               // inner box
            anchors.fill: parent; anchors.margins: 2; radius: 17
            color: config.box
        }
        TextInput {
            id: pw
            anchors.fill: parent; anchors.leftMargin: 20; anchors.rightMargin: 20
            verticalAlignment: TextInput.AlignVCenter; horizontalAlignment: TextInput.AlignHCenter
            echoMode: TextInput.Password; passwordCharacter: "●"
            font.family: root.mono; font.pixelSize: 18; font.letterSpacing: 4
            color: config.boxText; focus: true; clip: true
            onTextChanged: root.failed = false
            Keys.onReturnPressed: root.login()
            Keys.onEnterPressed: root.login()
        }
        Text {                    // placeholder
            anchors.centerIn: parent; visible: pw.text.length === 0
            text: root.failed ? "Wrong password" : "  Password…"
            color: root.failed ? config.fail1 : "#7b8d96"
            font.family: root.mono; font.pixelSize: 16
        }
    }

    // --- user ---
    Text {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.verticalCenter; anchors.verticalCenterOffset: 110
        color: config.user; font.family: root.mono; font.pixelSize: 18
        text: "  " + root.userName
    }

    // --- power buttons (bottom-right) ---
    Row {
        anchors.right: parent.right; anchors.bottom: parent.bottom; anchors.margins: 28
        spacing: 22
        Repeater {
            model: [ { icon: "", tip: "Restart", act: "reboot", ok: sddm.canReboot },
                     { icon: "⏻", tip: "Shut down", act: "poweroff", ok: sddm.canPowerOff } ]
            delegate: Text {
                visible: modelData.ok
                text: modelData.icon; color: mouse.containsMouse ? config.clock : config.date
                font.family: root.mono; font.pixelSize: 26
                MouseArea { id: mouse; anchors.fill: parent; hoverEnabled: true
                    onClicked: modelData.act === "reboot" ? sddm.reboot() : sddm.powerOff() }
            }
        }
    }

    function login() {
        if (pw.text.length === 0) return
        sddm.login(root.userName, pw.text, root.sessionIndex)
    }
    Connections {
        target: sddm
        function onLoginFailed() { pw.text = ""; root.failed = true; pw.forceActiveFocus() }
    }
    Component.onCompleted: pw.forceActiveFocus()
}
