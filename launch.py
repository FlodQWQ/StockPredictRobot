import os
import sys
from exec.mainLogic import mainUI

from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow

def restart_program():
    python = sys.executable
    os.execl(python, python, *sys.argv)


def main():
    app = QApplication(sys.argv)
    while 1:
        ui = mainUI()
        ui.exitSignal.connect(app.exit)
        ui.show()
        ui.move(ui.x(), ui.y())
        exit_code = app.exec_()
        if exit_code == 42:
            restart_program()
            continue
        sys.exit(exit_code)


if __name__ == '__main__':
    main()
