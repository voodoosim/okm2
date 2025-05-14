# main.py
import tkinter as tk
from session_gui import SessionManagerGUI

def main():
    """메인 진입점"""
    root = tk.Tk()
    SessionManagerGUI(root)  # app 변수 제거
    root.mainloop()

if __name__ == "__main__":
    main()
