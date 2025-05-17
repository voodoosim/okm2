"""
세션 관리자 모듈
텔레그램 세션 파일 관리를 담당합니다.
"""
from typing import Dict, Any, List, Optional, Tuple
import os
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv

from utils.logger import session_logger
from utils.helpers import session_validator, file_manager
from config.settings import settings


class SessionManager:
    """세션 관리를 위한 싱글톤 클래스"""
    _instance: Optional['SessionManager'] = None

    def __new__(cls) -> 'SessionManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """초기화"""
        if not hasattr(self, '_initialized') or not self._initialized:
            self._api_id = None
            self._api_hash = None
            self._sessions_dir = "sessions"
            self._config_file = "config.json"
            self._env_loaded = False
            self._initialized = True

            # 환경 변수 로드
            self._load_env()

            # 세션 디렉토리 확인
            self._ensure_sessions_dir()

    def _load_env(self) -> None:
        """환경 변수 로드"""
        if not self._env_loaded:
            load_dotenv()
            self._api_id = os.getenv("TELEGRAM_API_ID") or settings.telegram_api_id
            self._api_hash = os.getenv("TELEGRAM_API_HASH") or settings.telegram_api_hash
            self._env_loaded = True

            # 환경 변수에서 로드 실패시 config.json 확인
            if not self._api_id or not self._api_hash:
                self._load_config()

    def _load_config(self) -> None:
        """설정 파일 로드"""
        try:
            if os.path.exists(self._config_file):
                with open(self._config_file, 'r') as f:
                    config = json.load(f)
                    if not self._api_id:
                        self._api_id = config.get("api_id")
                    if not self._api_hash:
                        self._api_hash = config.get("api_hash")

                session_logger.info("설정 파일에서 API 정보 로드 성공")
            else:
                session_logger.warning("설정 파일이 존재하지 않습니다.")
        except Exception as e:
            session_logger.error(f"설정 파일 로드 오류: {e}")

    def _ensure_sessions_dir(self) -> None:
        """세션 디렉토리 확인 및 생성"""
        if not os.path.exists(self._sessions_dir):
            os.makedirs(self._sessions_dir)
            session_logger.info(f"세션 디렉토리 생성: {self._sessions_dir}")

    def save_config(self, api_id: str, api_hash: str) -> bool:
        """API 정보 저장"""
        try:
            config = {
                "api_id": api_id,
                "api_hash": api_hash
            }

            with open(self._config_file, 'w') as f:
                json.dump(config, f, indent=4)

            self._api_id = api_id
            self._api_hash = api_hash
            session_logger.info("API 정보 저장 성공")
            return True
        except Exception as e:
            session_logger.error(f"API 정보 저장 실패: {e}")
            return False

    async def get_api_credentials(self) -> Tuple[Optional[str], Optional[str]]:
        """API 자격 증명 조회"""
        if not self._api_id or not self._api_hash:
            self._load_env()

        return self._api_id, self._api_hash

    def get_session_files(self) -> List[str]:
        """세션 파일 목록 조회"""
        try:
            # 세션 파일 확장자
            session_files = []

            # 세션 디렉토리 확인
            if os.path.exists(self._sessions_dir):
                # 세션 파일만 필터링
                for file in os.listdir(self._sessions_dir):
                    if file.endswith(".session"):
                        # .session-journal 파일은 제외
                        if not file.endswith(".session-journal"):
                            # 확장자 제거한 파일명(전화번호)만 추출
                            session_name = file.replace(".session", "")
                            session_files.append(session_name)

            return session_files
        except Exception as e:
            session_logger.error(f"세션 파일 목록 조회 오류: {e}")
            return []

    def validate_session_file(self, phone: str) -> bool:
        """세션 파일 유효성 검사"""
        # 세션 파일 경로
        session_path = os.path.join(self._sessions_dir, f"{phone}.session")

        # 파일 존재 확인
        if not os.path.exists(session_path):
            session_logger.warning(f"세션 파일 없음: {phone}")
            return False

        # 세션 파일 검증
        return session_validator.validate_session_file(session_path)

    async def cleanup_active_sessions(self) -> int:
        """활성 세션 정리"""
        # 세션 디렉토리의 .session-journal 파일 삭제
        count = 0
        try:
            for file in os.listdir(self._sessions_dir):
                if file.endswith(".session-journal"):
                    file_path = os.path.join(self._sessions_dir, file)
                    os.remove(file_path)
                    count += 1
                    session_logger.info(f"세션 저널 파일 삭제: {file}")
            return count
        except Exception as e:
            session_logger.error(f"세션 정리 중 오류: {e}")
            return count


# 전역 세션 관리자 인스턴스
session_manager = SessionManager()
