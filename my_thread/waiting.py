import time

from PyQt5.QtCore import QThread, pyqtSignal


class ThreadWaiting(QThread):
    msg = pyqtSignal(str)

    def __init__(self, content, waiting_time):
        super(QThread, self).__init__()
        self.content = content
        self.time = waiting_time

    def run(self):
        self.msg.emit(f"等待{self.content}开始...")
        for i in range(self.time):
            self.msg.emit(f"等待......{i+1}/{self.time}")
            time.sleep(1)
        self.msg.emit(f"开始{self.content}...")
