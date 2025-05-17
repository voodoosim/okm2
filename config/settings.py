# config/settings.py
"""
TMC 텔레쏜 애플리케이션 설정
환경변수와 기본 설정을 관리합니다.
"""

# 예외 처리로 최대한 호환성 확보
try:
    # 최신 버전의 pydantic
    from pydantic_settings import BaseSettings
    from pydantic import Field
except ImportError:
    try:
        # 이전 버전의 pydantic
        from pydantic import BaseSettings, Field
    except ImportError:
        # pydantic 없는 경우 대체 구현
        class BaseSettings:
            """Pydantic BaseSettings 대체 클래스"""
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)

                # 기본값 설정
                if not hasattr(self, "db_path"):
                    self.db_path = "data/tmc.db"
                if not hasattr(self, "sessions_path"):
                    self.sessions_path = "sessions"
                if not hasattr(self, "logs_path"):
                    self.logs_path = "logs"
                if not hasattr(self, "exports_path"):
                    self.exports_path = "exports"
                if not hasattr(self, "temp_path"):
                    self.temp_path = "temp"
                if not hasattr(self, "log_level"):
                    self.log_level = "INFO"
                if not hasattr(self, "log_rotation"):
                    self.log_rotation = "1 day"
                if not hasattr(self, "log_retention"):
                    self.log_retention = "30 days"

                self.ensure_directories()

            class Config:
                env_file = ".env"
                env_prefix = "TMC_"

        # Field 함수 대체 구현
        def Field(default=None, **kwargs):
            return default

from typing import Optional, Dict, Any, List
from pathlib import Path
import os

class Settings(BaseSettings):
    """TMC 애플리케이션 설정 클래스"""

    # 애플리케이션 고정 설정 (환경변수 불필요)
    db_path: str = "data/tmc.db"
    db_pool_size: int = 5

    # 텔레그램 API 설정 (환경변수에서 가져옴)
    telegram_api_id: Optional[str] = None
    telegram_api_hash: Optional[str] = None

    # 경로 설정 (환경변수에서 가져옴)
    sessions_dir: Optional[str] = None
    logs_dir: Optional[str] = None

    # 사용자 설정 (환경변수로 오버라이드 가능)
    message_delay: float = 1.0
    theme: str = "dark"
    log_level: str = "INFO"

    # 애플리케이션 고정 설정
    window_width: int = 1200
    window_height: int = 800
    log_rotation: str = "1 day"
    log_retention: str = "30 days"
    encrypt_sessions: bool = True
    session_backup_enabled: bool = True

    # 기본 경로 설정 (환경변수가 없을 경우 사용)
    sessions_path: str = "sessions"
    logs_path: str = "logs"
    exports_path: str = "exports"
    temp_path: str = "temp"

    class Config:
        env_file = ".env"
        env_prefix = ""  # 접두사 없음, .env 파일의 변수 이름 그대로 사용
        env_file_encoding = 'utf-8'

    def ensure_directories(self):
        """필요한 디렉토리들을 생성합니다."""
        directories = [
            "data",
            "data/backups",
            self.sessions_path,
            f"{self.sessions_path}/original",
            f"{self.sessions_path}/active",
            f"{self.sessions_path}/backup",
            self.logs_path,
            self.exports_path,
            self.temp_path
        ]

        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

    @property
    def db_full_path(self) -> str:
        """데이터베이스 전체 경로 반환"""
        path_obj = Path(self.db_path)
        return str(path_obj.resolve())

    @property
    def is_api_configured(self) -> bool:
        """API 설정이 완료되었는지 확인"""
        return self.telegram_api_id is not None and self.telegram_api_hash is not None


# 전역 설정 인스턴스
settings = Settings()
settings.ensure_directories()
