from PyQt5.QtCore import QThread, pyqtSignal

from exec.stock_tmp import StockTmp


class ThreadLoadStocks(QThread):
    msg = pyqtSignal(str)
    stock_tmp = pyqtSignal(StockTmp)

    def __init__(self):
        super(QThread, self).__init__()
        self.stock = StockTmp()

    def load_stocks(self):
        msg = self.stock.init()
        return msg

    def run(self):
        msg = self.load_stocks()
        self.msg.emit(msg)
        self.stock_tmp.emit(self.stock)
