# core/message_sender.py
"""
TMC 텔레쏜 메시지 전송자
텍스트 및 미디어 메시지 전송
"""

import asyncio
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union, Set
from datetime import datetime
import tempfile

from telethon import TelegramClient
from telethon.errors import (
    FloodWaitError,
    SlowModeWaitError,
    ChatWriteForbiddenError,
    ChatSendMediaForbiddenError,
    UserIsBlockedError
)
from telethon.tl.types import InputMediaUploadedPhoto, InputMediaUploadedDocument
from telethon.tl.functions.messages import SendMessageRequest, SendMediaRequest

from config.settings import settings
from utils.logger import message_logger
from utils.helpers import (
    flood_wait_handler,
    retry_handler,
    text_processor
)
from database.db_manager import db_manager, MessageStatus


class MessageSender:
    """텔레그램 메시지 전송 클래스"""

    def __init__(self):
        """메시지 전송자 초기화"""
        pass

    @property
    def account_manager(self):
        """순환 참조 방지를 위해 지연 로딩된 계정 관리자"""
        from core.account_manager import account_manager
        return account_manager

    async def send_text_message(
        self,
        chat_id: str,
        message: str,
        phones: Optional[List[str]] = None,
        delay: float = 1.0
    ) -> Tuple[int, List[Dict[str, Any]]]:
        """
        텍스트 메시지 전송
        Returns: (성공 개수, 결과 목록)
        """
        results = []
        success_count = 0

        # 채팅 ID 처리
        chat_id = text_processor.extract_chat_id(chat_id)

        # 대상 계정 목록
        target_phones = phones or list(self.account_manager.clients.keys())

        if not target_phones:
            message_logger.warning("연결된 계정이 없습니다.")
            return 0, results

        for phone in target_phones:
            result = {
                "phone": phone,
                "chat_id": chat_id,
                "message_type": "text",
                "success": False,
                "error": None,
                "sent_at": datetime.now().isoformat()
            }

            # 연결 확인
            if phone not in self.account_manager.clients:
                result["error"] = "연결되지 않음"
                results.append(result)
                await self._log_message_result(phone, chat_id, message, "text", False, "연결되지 않음")
                continue

            try:
                client = self.account_manager.clients[phone]

                # 1회 재시도 허용
                async def send_message_coro():
                    await client.send_message(chat_id, message)

                # 재시도 실행
                success, error = await retry_handler.execute_with_retry(
                    send_message_coro(), phone, "send_message"
                )

                result["success"] = success
                result["error"] = error

                # 로그 기록
                await self._log_message_result(phone, chat_id, message, "text", success, error)

                if success:
                    success_count += 1
                    message_logger.info(f"메시지 전송 성공: {phone} -> {chat_id}")
                else:
                    message_logger.warning(f"메시지 전송 실패: {phone} -> {chat_id}, {error}")

            except Exception as e:
                result["error"] = str(e)
                await self._log_message_result(phone, chat_id, message, "text", False, str(e))
                message_logger.error(f"메시지 전송 중 오류: {phone} -> {chat_id}, {e}")

            results.append(result)

            # 전송 간격 대기
            if delay > 0 and phone != target_phones[-1]:
                await asyncio.sleep(delay)

        message_logger.info(f"메시지 전송 완료: {success_count}/{len(target_phones)} 성공")
        return success_count, results

    async def send_image_message(
        self,
        chat_id: str,
        image_path: str,
        caption: Optional[str] = None,
        phones: Optional[List[str]] = None,
        delay: float = 1.0
    ) -> Tuple[int, List[Dict[str, Any]]]:
        """
        이미지 메시지 전송
        Returns: (성공 개수, 결과 목록)
        """
        results = []
        success_count = 0

        # 채팅 ID 처리
        chat_id = text_processor.extract_chat_id(chat_id)

        # 대상 계정 목록
        target_phones = phones or list(self.account_manager.clients.keys())

        # 이미지 파일 확인
        if not os.path.isfile(image_path):
            message_logger.error(f"이미지 파일이 없음: {image_path}")
            return 0, [{"error": "이미지 파일이 없음"}]

        for phone in target_phones:
            result = {
                "phone": phone,
                "chat_id": chat_id,
                "message_type": "image",
                "success": False,
                "error": None,
                "sent_at": datetime.now().isoformat()
            }

            # 연결 확인
            if phone not in self.account_manager.clients:
                result["error"] = "연결되지 않음"
                results.append(result)
                await self._log_message_result(phone, chat_id, caption or "", "image", False, "연결되지 않음")
                continue

            try:
                client = self.account_manager.clients[phone]

                # 1회 재시도 허용
                async def send_image_coro():
                    await client.send_file(
                        chat_id,
                        image_path,
                        caption=caption
                    )

                # 재시도 실행
                success, error = await retry_handler.execute_with_retry(
                    send_image_coro(), phone, "send_image"
                )

                result["success"] = success
                result["error"] = error

                # 로그 기록
                image_name = Path(image_path).name
                log_message = f"이미지: {image_name}" + (f", 캡션: {caption}" if caption else "")
                await self._log_message_result(phone, chat_id, log_message, "image", success, error)

                if success:
                    success_count += 1
                    message_logger.info(f"이미지 전송 성공: {phone} -> {chat_id}")
                else:
                    message_logger.warning(f"이미지 전송 실패: {phone} -> {chat_id}, {error}")

            except Exception as e:
                result["error"] = str(e)
                await self._log_message_result(phone, chat_id, caption or "", "image", False, str(e))
                message_logger.error(f"이미지 전송 중 오류: {phone} -> {chat_id}, {e}")

            results.append(result)

            # 전송 간격 대기
            if delay > 0 and phone != target_phones[-1]:
                await asyncio.sleep(delay)

        message_logger.info(f"이미지 전송 완료: {success_count}/{len(target_phones)} 성공")
        return success_count, results

    async def _log_message_result(
        self,
        phone: str,
        chat_id: str,
        message: str,
        message_type: str,
        success: bool,
        error: Optional[str] = None
    ):
        """메시지 결과 로그 기록"""
        # 상태 결정
        status = MessageStatus.SUCCESS.value if success else MessageStatus.FAILED.value
        if error and "flood wait" in error.lower():
            status = MessageStatus.FLOOD_WAIT.value

        # 로그 데이터 생성
        log_data = {
            "phone": phone,
            "chat_id": chat_id,
            "message": message[:500],  # 너무 긴 메시지는 자름
            "message_type": message_type,
            "status": status,
            "error_message": error
        }

        # DB에 기록
        await db_manager.log_message(log_data)

        # 로거에 기록
        message_logger.message_log(phone, chat_id, status, message[:50], error)


# 전역 메시지 전송자 인스턴스
message_sender = MessageSender()
