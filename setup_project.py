#!/usr/bin/env python3
"""
TMC 텔레쏜 프로젝트 구조 생성 스크립트

기존 파일을 삭제하고 새로운 구조로 재구성합니다.
세션 파일(.session)과 .env 파일은 보존됩니다.
"""

import os
import shutil
from pathlib import Path
import sys


def backup_important_files():
    """중요한 파일들 백업"""
    backup_dir = Path("backup_temp")
    backup_dir.mkdir(exist_ok=True)

    important_files = []

    # .env 파일 백업
    if Path(".env").exists():
        shutil.copy2(".env", backup_dir / ".env")
        important_files.append(".env")

    # 세션 파일들 백업 (.session 확장자)
    for session_file in Path(".").glob("*.session"):
        shutil.copy2(session_file, backup_dir / session_file.name)
        important_files.append(session_file.name)

    # sessions 폴더 백업
    if Path("sessions").exists():
        if backup_dir.joinpath("sessions").exists():
            shutil.rmtree(backup_dir / "sessions")
        shutil.copytree("sessions", backup_dir / "sessions")
        important_files.append("sessions/")

    return important_files


def clean_current_directory():
    """현재 디렉토리 정리 (중요 파일 제외)"""
    # 보존할 파일/폴더 목록
    keep_files = {
        ".env",                     # 환경 변수
        "setup_project.py",         # 이 스크립트
        "backup_temp",              # 백업 임시 폴더
        ".venv",                    # 가상환경
        ".git",                     # Git 저장소
        ".gitignore",               # Git 무시 목록
        "LICENSE",                  # 라이선스
        "README.md",                # 리드미 (있다면 덮어쓰기됨)
        "pyrproject.toml",          # Python 프로젝트 설정
        "poetry.lock",              # Poetry 잠금 파일
        "Pipfile",                  # Pipenv 파일
        "Pipfile.lock"              # Pipenv 잠금 파일
    }

    # 패턴 매칭으로 보존할 파일들
    keep_patterns = {
        "*.session",                # 텔레그램 세션 파일
        "*.env*",                   # 환경 설정 파일들
        "*.key",                    # 키 파일들
        "*.pem",                    # 인증서 파일들
        "__pycache__"               # Python 캐시 (자동 재생성됨)
    }

    for item in Path(".").iterdir():
        if item.name in keep_files:
            continue

        # 패턴 매칭
        should_keep = False
        for pattern in keep_patterns:
            if item.match(pattern):
                should_keep = True
                break

        if should_keep:
            continue

        # 삭제 실행
        if item.is_dir():
            shutil.rmtree(item)
            print(f"🗑️ 폴더 삭제: {item.name}")
        else:
            item.unlink()
            print(f"🗑️ 파일 삭제: {item.name}")


def create_project_structure():
    """새로운 프로젝트 구조 생성"""
    structure = {
        "config": ["__init__.py", "settings.py"],
        "core": ["__init__.py", "session_manager.py", "account_manager.py", "message_sender.py"],
        "database": ["__init__.py", "db_manager.py"],
        "gui": ["__init__.py", "main_window.py"],
        "gui/widgets": ["__init__.py", "account_list.py", "message_editor.py", "log_viewer.py"],
        "gui/styles": ["__init__.py", "theme.py"],
        "cli": ["__init__.py", "cli_interface.py"],
        "utils": ["__init__.py", "logger.py", "helpers.py"]
    }

    # 폴더 및 파일 생성
    for folder, files in structure.items():
        folder_path = Path(folder)
        folder_path.mkdir(parents=True, exist_ok=True)
        print(f"📁 폴더 생성: {folder}")

        for file in files:
            file_path = folder_path / file
            if not file_path.exists():
                file_path.touch()
                print(f"  📄 파일 생성: {file}")


def create_main_files():
    """메인 파일들 생성"""
    files = {
        "main.py": '''#!/usr/bin/env python3
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
''',

        "requirements.txt": '''# TMC 텔레쏜 필수 패키지
telethon>=1.34.0
PyQt6>=6.0.0
aiosqlite>=0.18.0

# 개발/테스트 도구 (선택사항)
black>=23.0.0
mypy>=1.0.0
pytest>=7.0.0
''',

        "README.md": '''# TMC 텔레쏜

텔레쏜 기반 텔레그램 다중 계정 관리 도구

## 설치

```bash
pip install -r requirements.txt
```

## 실행

```bash
# GUI 모드
python main.py

# CLI 모드
python main.py --mode cli
```

## 기능

- 기존 텔레쏜 세션 파일 활용
- 다중 계정 관리
- 메시지 전송
- 실시간 상태 모니터링

'''
    }

    for filename, content in files.items():
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"📄 메인 파일 생성: {filename}")


def restore_important_files():
    """백업된 중요 파일들 복원"""
    backup_dir = Path("backup_temp")

    if not backup_dir.exists():
        return []

    restored_files = []

    # 백업 폴더의 모든 파일 복원
    for item in backup_dir.iterdir():
        if item.is_file():
            shutil.copy2(item, Path(".") / item.name)
            restored_files.append(item.name)
        elif item.is_dir() and item.name == "sessions":
            # sessions 폴더 복원
            if Path("sessions").exists():
                shutil.rmtree("sessions")
            shutil.copytree(item, Path("sessions"))
            restored_files.append("sessions/")

    # 백업 폴더 삭제
    shutil.rmtree(backup_dir)

    return restored_files


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("    TMC 텔레쏜 프로젝트 구조 생성")
    print("=" * 60)
    print()

    # 1. 중요 파일 백업
    print("1️⃣ 중요 파일 백업 중...")
    backed_up = backup_important_files()
    print(f"   ✅ 백업 완료: {backed_up}")
    print()

    # 2. 기존 파일 정리
    print("2️⃣ 기존 파일 정리 중...")
    clean_current_directory()
    print("   ✅ 정리 완료")
    print()

    # 3. 새 구조 생성
    print("3️⃣ 새 프로젝트 구조 생성 중...")
    create_project_structure()
    print("   ✅ 구조 생성 완료")
    print()

    # 4. 메인 파일 생성
    print("4️⃣ 메인 파일 생성 중...")
    create_main_files()
    print("   ✅ 메인 파일 생성 완료")
    print()

    # 5. 중요 파일 복원
    print("5️⃣ 중요 파일 복원 중...")
    restored = restore_important_files()
    print(f"   ✅ 복원 완료: {restored}")
    print()

    # 완료 메시지
    print("🎉 프로젝트 구조 생성 완료!")
    print()
    print("다음 단계:")
    print("1. pip install -r requirements.txt")
    print("2. 각 모듈의 코드 구현")
    print("3. python main.py 로 실행")
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
