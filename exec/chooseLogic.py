from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QDialog

from ui.choose import Ui_Dialog


class dialogUI(QDialog, Ui_Dialog):
    receive_data = pyqtSignal(list)
    send_data = pyqtSignal(str)

    def __init__(self, parent=None):
        super(dialogUI, self).__init__(parent)
        self.setupUi(self)
        self.receive_data.connect(self.receive)
        self.setWindowTitle("选择公司")
        self.buttonBox.accepted.connect(self.send_slot)

    def receive(self, data: list):
        self.list_choices.clear()
        for i in data:
            self.list_choices.addItem(i['名称'])
        self.list_choices.setCurrentRow(0)

    def send_slot(self):
        self.send_data.emit(self.list_choices.currentItem().text())
        self.close()
