#!/usr/bin/env python3
"""
TMC 텔레쏜 - 메인 실행 파일
"""

import sys
import argparse
from pathlib import Path

# 프로젝트 루트를 파이썬 패스에 추가
sys.path.insert(0, str(Path(__file__).parent))

def main():
    parser = argparse.ArgumentParser(description="TMC 텔레쏜 - Telegram Multi Controller")
    parser.add_argument("--mode", choices=["gui", "cli"], default="gui",
                       help="실행 모드 선택 (기본값: gui)")

    args = parser.parse_args()

    if args.mode == "gui":
        print("🖥️ GUI 모드로 시작합니다...")
        from gui.main_window import start_gui
        start_gui()
    else:
        print("💻 CLI 모드로 시작합니다...")
        from cli.cli_interface import start_cli
        start_cli()

if __name__ == "__main__":
    main()
