# utils/helpers.py
"""
TMC 텔레쏜 유틸리티 헬퍼 함수들
"""

import os
import shutil
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Union, Optional, Tuple, List, Any
import re
import hashlib
from telethon.errors import FloodWaitError

# 로컬 임포트
from config.settings import settings
from utils.logger import get_logger

helper_logger = get_logger("Helpers")


class FileManager:
    """파일 관리 유틸리티"""

    @staticmethod
    def ensure_directory(path: Union[str, Path]) -> Path:
        """디렉토리 생성 보장"""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def copy_session_file(src: Union[str, Path], dst: Union[str, Path]) -> bool:
        """세션 파일 안전 복사"""
        try:
            src, dst = Path(src), Path(dst)

            # 대상 디렉토리 생성
            dst.parent.mkdir(parents=True, exist_ok=True)

            # 파일 복사
            shutil.copy2(src, dst)
            helper_logger.info(f"세션 파일 복사 완료: {src} -> {dst}")
            return True
        except Exception as e:
            helper_logger.error(f"세션 파일 복사 실패: {e}")
            return False

    @staticmethod
    def backup_session_file(session_path: Union[str, Path], backup_dir: Union[str, Path]) -> Optional[str]:
        """세션 파일 백업 (날짜별)"""
        try:
            session_path = Path(session_path)
            backup_dir = Path(backup_dir)

            if not session_path.exists():
                helper_logger.warning(f"백업할 세션 파일이 없음: {session_path}")
                return None

            # 백업 파일명 생성
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{session_path.stem}_backup_{timestamp}.session"
            backup_path = backup_dir / backup_filename

            # 백업 실행
            if FileManager.copy_session_file(session_path, backup_path):
                return str(backup_path)
            return None

        except Exception as e:
            helper_logger.error(f"세션 백업 실패: {e}")
            return None

    @staticmethod
    def cleanup_old_backups(backup_dir: Union[str, Path], keep_days: int = 7):
        """오래된 백업 파일 정리"""
        try:
            backup_dir = Path(backup_dir)
            if not backup_dir.exists():
                return

            cutoff_date = datetime.now() - timedelta(days=keep_days)

            for backup_file in backup_dir.glob("*_backup_*.session"):
                if backup_file.stat().st_mtime < cutoff_date.timestamp():
                    backup_file.unlink()
                    helper_logger.info(f"오래된 백업 삭제: {backup_file}")

        except Exception as e:
            helper_logger.error(f"백업 정리 실패: {e}")


class PhoneValidator:
    """전화번호 검증 유틸리티"""

    @staticmethod
    def normalize_phone(phone: str) -> str:
        """전화번호 정규화"""
        # 숫자만 추출
        digits = re.sub(r'\D', '', phone)

        # 국가 코드 추가
        if not digits.startswith('82') and len(digits) >= 10:
            digits = '82' + digits.lstrip('0')

        return '+' + digits

    @staticmethod
    def validate_phone(phone: str) -> bool:
        """전화번호 유효성 검사"""
        normalized = PhoneValidator.normalize_phone(phone)
        # 기본적인 한국 전화번호 패턴 검증
        pattern = r'^\+82[1-9]\d{7,9}$'
        return bool(re.match(pattern, normalized))


class FloodWaitHandler:
    """Flood Wait 처리 유틸리티"""

    def __init__(self, max_wait_seconds: int = 30):
        self.max_wait_seconds = max_wait_seconds
        self.flood_wait_counts = {}  # phone -> count

    async def handle_flood_wait(self, phone: str, seconds: int) -> bool:
        """
        Flood Wait 처리
        Returns: True if should wait, False if should skip
        """
        helper_logger.flood_wait_log(phone, seconds, "detected")

        # 최대 대기시간 초과시 스킵
        if seconds > self.max_wait_seconds:
            helper_logger.warning(f"Flood Wait 시간 초과 ({seconds}s > {self.max_wait_seconds}s): {phone}")
            return False

        # 대기 실행
        helper_logger.info(f"Flood Wait 대기 중: {phone} ({seconds}s)")
        await asyncio.sleep(seconds)

        # 대기 횟수 기록
        self.flood_wait_counts[phone] = self.flood_wait_counts.get(phone, 0) + 1

        return True

    def get_flood_wait_count(self, phone: str) -> int:
        """계정별 Flood Wait 횟수 조회"""
        return self.flood_wait_counts.get(phone, 0)

    def reset_flood_wait_count(self, phone: str):
        """계정별 Flood Wait 횟수 초기화"""
        self.flood_wait_counts.pop(phone, None)


class RetryHandler:
    """재시도 처리 유틸리티"""

    def __init__(self, max_retries: int = 1, delay: float = 1.0):
        self.max_retries = max_retries
        self.delay = delay

    async def execute_with_retry(self, coro, phone: str, action: str) -> Tuple[bool, Optional[str]]:
        """
        재시도와 함께 코루틴 실행
        Returns: (success, error_message)
        """
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                await coro
                return True, None
            except FloodWaitError as e:
                # Flood Wait는 재시도 하지 않음
                helper_logger.flood_wait_log(phone, e.seconds, action)
                return False, f"Flood Wait: {e.seconds}s"
            except Exception as e:
                last_error = str(e)
                helper_logger.warning(f"시도 {attempt + 1}/{self.max_retries + 1} 실패: {phone} | {action} | {e}")

                # 마지막 시도가 아니면 대기
                if attempt < self.max_retries:
                    await asyncio.sleep(self.delay)

        helper_logger.error(f"모든 재시도 실패: {phone} | {action} | {last_error}")
        return False, last_error


class TextProcessor:
    """텍스트 처리 유틸리티"""

    @staticmethod
    def truncate_text(text: str, max_length: int = 100) -> str:
        """텍스트 자르기"""
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."

    @staticmethod
    def mask_sensitive_data(text: str) -> str:
        """민감한 데이터 마스킹 (전화번호 등)"""
        # 전화번호 마스킹
        text = re.sub(r'(\+82)(\d{2})(\d+)(\d{4})', r'\1**-***-\4', text)
        # API 키 마스킹
        text = re.sub(r'([a-f0-9]{8})[a-f0-9]{16}([a-f0-9]{8})', r'\1****\2', text)
        return text

    @staticmethod
    def extract_chat_id(text: str) -> Optional[str]:
        """텍스트에서 채팅 ID 추출"""
        # 숫자 ID
        if text.isdigit() or (text.startswith('-') and text[1:].isdigit()):
            return text

        # Username (@로 시작)
        if text.startswith('@'):
            return text[1:]

        # t.me 링크에서 추출
        match = re.search(r't\.me/([^/\s]+)', text)
        if match:
            return match.group(1)

        return text  # 그대로 반환


class SessionFileValidator:
    """세션 파일 유효성 검증"""

    @staticmethod
    def validate_session_file(path: Union[str, Path]) -> bool:
        """세션 파일 유효성 검사"""
        try:
            path = Path(path)

            # 파일 존재 확인
            if not path.exists() or not path.is_file():
                return False

            # 확장자 확인
            if path.suffix != '.session':
                return False

            # 파일 크기 확인 (너무 작으면 유효하지 않음)
            if path.stat().st_size < 1024:  # 1KB 미만
                return False

            # SQLite 파일 시그니처 확인
            with open(path, 'rb') as f:
                header = f.read(16)
                if not header.startswith(b'SQLite format 3'):
                    return False

            return True

        except Exception as e:
            helper_logger.error(f"세션 파일 검증 실패: {e}")
            return False

    @staticmethod
    def get_session_phone_from_filename(filename: str) -> Optional[str]:
        """파일명에서 전화번호 추출"""
        name = Path(filename).stem

        # 숫자만 추출
        digits = re.findall(r'\d+', name)
        if digits:
            phone = ''.join(digits)
            # 한국 전화번호 형식으로 변환
            if len(phone) >= 10:
                return PhoneValidator.normalize_phone(phone)

        return None


# 전역 유틸리티 인스턴스
file_manager = FileManager()
phone_validator = PhoneValidator()
flood_wait_handler = FloodWaitHandler()
retry_handler = RetryHandler()
text_processor = TextProcessor()
session_validator = SessionFileValidator()
