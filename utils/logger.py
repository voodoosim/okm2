# utils/logger.py
"""
TMC 텔레쏜 로깅 설정
loguru를 사용한 향상된 로깅 시스템
"""

import sys
from pathlib import Path
from typing import Optional
from loguru import logger

# 로컬 임포트
from config.settings import settings

# 기존 핸들러 제거
logger.remove()

# 로그 디렉토리 생성
log_dir = Path(settings.logs_path)
log_dir.mkdir(exist_ok=True)

# 콘솔 로그 설정 (개발용)
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
           "<level>{level: <8}</level> | "
           "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
           "<level>{message}</level>",
    level=settings.log_level,
    enqueue=True
)

# 파일 로그 설정 (운영용)
logger.add(
    log_dir / "app.log",
    rotation=settings.log_rotation,
    retention=settings.log_retention,
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
    compression="zip",
    encoding="utf-8",
    enqueue=True
)

# 에러 로그 설정
logger.add(
    log_dir / "error.log",
    rotation="1 week",
    retention="30 days",
    level="ERROR",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
    compression="zip",
    encoding="utf-8",
    enqueue=True
)

# 메시지 전송 로그 설정
logger.add(
    log_dir / "messages.log",
    rotation="1 day",
    retention="7 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {extra[phone]} | {extra[chat_id]} | {extra[status]} | {message}",
    filter=lambda record: "message_log" in record["extra"],
    encoding="utf-8",
    enqueue=True
)


class TMCLogger:
    """TMC 전용 로거 클래스"""

    def __init__(self, name: Optional[str] = None):
        self.logger = logger.bind(name=name or __name__)

    def info(self, message: str, **kwargs):
        """정보 로그"""
        self.logger.info(message, **kwargs)

    def debug(self, message: str, **kwargs):
        """디버그 로그"""
        self.logger.debug(message, **kwargs)

    def warning(self, message: str, **kwargs):
        """경고 로그"""
        self.logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs):
        """에러 로그"""
        self.logger.error(message, **kwargs)

    def success(self, message: str, **kwargs):
        """성공 로그"""
        self.logger.success(message, **kwargs)

    def message_log(self, phone: str, chat_id: str, status: str, message: str, error: Optional[str] = None):
        """메시지 전송 로그"""
        extra = {
            "message_log": True,
            "phone": phone,
            "chat_id": chat_id,
            "status": status
        }

        log_message = f"Message: {message[:50]}{'...' if len(message) > 50 else ''}"
        if error:
            log_message += f" | Error: {error}"

        self.logger.bind(**extra).info(log_message)

    def session_log(self, phone: str, action: str, details: Optional[str] = None):
        """세션 관련 로그"""
        message = f"Session {action}: {phone}"
        if details:
            message += f" | {details}"
        self.logger.info(message)

    def flood_wait_log(self, phone: str, seconds: int, action: str):
        """Flood Wait 로그"""
        self.logger.warning(f"Flood Wait: {phone} | {seconds}s | Action: {action}")


# 전역 로거 인스턴스들
main_logger = TMCLogger("TMC.Main")
session_logger = TMCLogger("TMC.Session")
message_logger = TMCLogger("TMC.Message")
gui_logger = TMCLogger("TMC.GUI")
db_logger = TMCLogger("TMC.Database")

# 편의 함수들
def get_logger(name: str) -> TMCLogger:
    """모듈별 로거 생성"""
    return TMCLogger(f"TMC.{name}")
