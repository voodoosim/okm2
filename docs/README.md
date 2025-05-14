# MTC - 텔레그램 다중 계정 컨트롤러

텔레그램 다중 계정을 관리하고 메시지를 자동으로 전송하는 프로그램입니다.

## 📂 프로젝트 구조

```text
📂 mtc/
│
├── 📁 .venv/                          # 가상환경 폴더
│   ├── 📁 Scripts/                    # Windows 실행 파일들
│   ├── 📁 Lib/                       # Python 라이브러리들
│   └── 📄 pyvenv.cfg                 # 가상환경 설정
│
├── 📁 sessions/                       # 세션 파일 폴더 ⭐
│   ├── 🔑 계정1.session              # 세션 파일들
│   ├── 🔑 계정2.session              # (12개 세션 파일)
│   └── 🔑 계정3.session
│
├── 🔐 .env                           # 환경 변수 파일 ⭐
├── 📘 .gitignore                     # Git 제외 파일 목록
├── 🐍 main.py                        # 메인 GUI 프로그램
├── 🐍 session_connector.py           # 세션 연동 프로그램 ⭐
├── 📝 requirements.txt               # Python 의존성 목록
├── 📋 config.json                    # API 설정 백업 파일
└── 📘 README.md                      # 프로젝트 설명
```

## 🚀 사용 방법

### 1. 가상환경 활성화

```powershell
.\.venv\Scripts\Activate.ps1
```

### 2. 의존성 설치

```powershell
pip install -r requirements.txt
```

### 3. 환경 변수 설정

`.env` 파일에 API 정보를 입력하세요:

```env
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
```

### 4. 세션 연동

```powershell
python session_connector.py
```

## 📋 주요 기능

- 🔄 **다중 세션 관리**: 여러 텔레그램 계정을 동시에 관리
- 🚀 **자동 연결**: 모든 세션을 한 번에 연결 가능
- 📊 **상태 모니터링**: 연결 상태 실시간 확인
- 🧪 **세션 테스트**: 연결된 세션들의 작동 상태 검증

## 📊 체크리스트

### ✅ 완료된 항목

- [x] .venv/ - 가상환경 설정
- [x] sessions/ - 세션 파일 폴더 (12개 세션)
- [x] .env - API 정보 설정
- [x] session_connector.py - 세션 연동 프로그램

### 🔄 진행 예정

- [ ] 메시지 전송 기능
- [ ] UI 개선
- [ ] 로그 시스템
- [ ] 교차 전송 기능

## ⚠️ 주의사항

1. `.env` 파일과 `sessions/` 폴더는 보안상 중요하니 공유하지 마세요
2. API 제한을 피하기 위해 적절한 간격으로 메시지를 전송하세요
3. 텔레그램 이용약관을 준수하여 사용하세요

## 🔧 개발 환경

- Python 3.8+
- Telethon 1.28.0+
- python-dotenv 1.0.0+

## 📞 문의

프로젝트에 관한 문의나 개선 사항이 있으시면 언제든지 연락주세요.
