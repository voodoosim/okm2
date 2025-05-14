# main.py - 개선된 메인 진입점
import customtkinter as ctk
from session_gui_modern import SessionManagerGUI

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

def main():
    """메인 진입점 - 세션 자동 연결 포함"""
    print("🚀 Telegram Session Manager 시작...")
    print("📡 세션 자동 연결 중...")

    app = SessionManagerGUI()
    app.run()

if __name__ == "__main__":
    main()
