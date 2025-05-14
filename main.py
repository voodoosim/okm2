# mtc/setup.py
"""
프로젝트 구조 및 필요 파일 생성 스크립트
"""

import os



def create_project_structure():
    """프로젝트 구조 생성"""

    # 필요한 폴더 생성
    folders = [
        "sessions",
        "logs"  # 나중에 로그 파일을 위한 폴더
    ]

    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"✅ 폴더 생성: {folder}/")
        else:
            print(f"📁 폴더 존재: {folder}/")

    # requirements.txt 생성
    requirements = """telethon>=1.28.0
"""

    with open("requirements.txt", "w") as f:
        f.write(requirements)
    print("✅ requirements.txt 생성")

    # .gitignore 생성 (선택사항)
    gitignore = """# 세션 파일 (보안상 중요!)
sessions/*.session

# 설정 파일
config.json

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# 로그 파일
logs/
*.log
"""

    with open(".gitignore", "w") as f:
        f.write(gitignore)
    print("✅ .gitignore 생성")

    # README.md 생성
    readme = """# Telegram Multi-Account Controller (MTC)

텔레그램 다중 계정 관리 프로그램

## 설치

```bash
pip install -r requirements.txt
```

## 실행

```bash
python main.py
```

## 주의사항

- sessions/ 폴더의 .session 파일은 절대 공유하지 마세요!
- config.json 파일도 API 정보가 포함되어 있으니 주의하세요.
"""

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme)
    print("✅ README.md 생성")

    # main.py 파일이 없으면 설명 파일 생성
    if not os.path.exists("main.py"):
        note = """# main.py
#
# 이 파일을 텔레그램 세션 매니저 코드로 교체하세요.
#
# 필요한 기능:
# 1. 세션 생성
# 2. 세션 연결
# 3. 다중 계정 관리
# 4. 메시지 전송
#

print("main.py 파일을 실제 코드로 교체해주세요!")
"""
        with open("main.py", "w", encoding="utf-8") as f:
            f.write(note)
        print("✅ main.py 템플릿 생성")

    print("\n🎉 프로젝트 구조 생성 완료!")
    print("\n다음 단계:")
    print("1. pip install -r requirements.txt")
    print("2. main.py에 실제 코드 작성")
    print("3. python main.py 실행")


if __name__ == "__main__":
    create_project_structure()
