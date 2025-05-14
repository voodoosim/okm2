# main.py
import customtkinter as ctk
from session_gui_modern import SessionManagerGUI

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

def main():
    """메인 진입점"""
    app = SessionManagerGUI()
    app.run()

if __name__ == "__main__":
    main()
