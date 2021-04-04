import logging
import sys

from PyQt5.QtWidgets import QApplication
from kiwoom.kiwoom import Kiwoom
from kiwoom.trace import Trace


class Main():

    def __init__(self):
        print(">>> class[Main] start.")
        self.app = QApplication(sys.argv)
#         self.kiwoom = Kiwoom()
        self.trace = Trace()
        self.app.exec_()


if __name__ == "__main__":
    Main()
