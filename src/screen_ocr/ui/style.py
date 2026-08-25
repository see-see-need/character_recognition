APP_STYLE = """
QWidget {
    background: #F7F8FA;
    color: #172033;
    font-family: "Microsoft YaHei UI";
    font-size: 14px;
}
QMainWindow, QDialog { background: #F7F8FA; }
QLabel#title { font-size: 27px; font-weight: 650; color: #101828; }
QLabel#dialogTitle { font-size: 21px; font-weight: 650; color: #101828; }
QLabel#subtitle, QLabel#hint { color: #536078; }
QLabel#successHint { color: #18794E; }
QLabel#hint[error="true"] { color: #B42318; }
QLabel#status { color: #344054; }
QLabel#fieldLabel { font-weight: 600; color: #27344A; }
QLabel#shortcutValue {
    background: #E7EEFF;
    color: #1746A2;
    border-radius: 6px;
    padding: 5px 9px;
    font-weight: 600;
}
QFrame#infoPanel { background: #EEF1F6; border-radius: 12px; }
QPushButton {
    background: #FFFFFF;
    color: #24324A;
    border: 1px solid #C9D1DF;
    border-radius: 9px;
    padding: 9px 15px;
    font-weight: 600;
}
QPushButton:hover { background: #F0F4FA; border-color: #AAB6C8; }
QPushButton:pressed { background: #E7ECF4; }
QPushButton:focus { border: 2px solid #2563EB; padding: 8px 14px; }
QPushButton:disabled { color: #8993A4; background: #E8EBF0; border-color: #D7DCE5; }
QPushButton#primaryButton { background: #2563EB; color: white; border: 1px solid #2563EB; }
QPushButton#primaryButton:hover { background: #1D4ED8; border-color: #1D4ED8; }
QPushButton#primaryButton:pressed { background: #1E40AF; }
QTextEdit, QKeySequenceEdit, QLineEdit {
    background: #FFFFFF;
    color: #101828;
    border: 1px solid #BEC8D8;
    border-radius: 9px;
    padding: 10px;
    selection-background-color: #BFDBFE;
    selection-color: #102A56;
}
QTextEdit:focus, QKeySequenceEdit:focus, QLineEdit:focus { border: 2px solid #2563EB; padding: 9px; }
QFrame#translationPanel {
    background: #EEF1F6;
    border: 1px solid #C9D1DF;
    border-radius: 12px;
}
QFrame#translationPanel QLabel {
    background: transparent;
}
QFrame#translationPanel QTextEdit { background: #FFFFFF; }
QCheckBox { spacing: 9px; }
QCheckBox::indicator { width: 18px; height: 18px; }
QMenu { background: #FFFFFF; border: 1px solid #D2D8E2; padding: 5px; }
QMenu::item { padding: 8px 28px 8px 12px; border-radius: 6px; }
QMenu::item:selected { background: #E7EEFF; color: #1746A2; }
"""
