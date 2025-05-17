# gui/main_window.py
"""
TMC 텔레쏜 GUI 메인 창
PyQt6 기반의 그래픽 인터페이스
"""

from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import QThread, pyqtSignal
import sys

from utils.logger import gui_logger

def start_gui():
    """GUI 시작 함수"""
    gui_logger.info("GUI 시작하는 중...")
    app = QApplication(sys.argv)
    # window = MainWindow()
    # window.show()
    gui_logger.info("GUI 준비 중... 곧 완료됩니다.")
    # 임시 메시지 표시
    print("GUI 모드 개발 진행 중입니다. 추후 업데이트에서 제공됩니다.")
    # sys.exit(app.exec())


class MainWindow(QMainWindow):
    """메인 윈도우 클래스"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("TMC 텔레쏜")
        self.setGeometry(100, 100, 1200, 800)
        self.setup_ui()

    def setup_ui(self):
        """UI 설정"""
        # 추후 구현
        pass
