"""
계정 관리자 모듈
텔레그램 계정 연결 및 관리
"""
from typing import Dict, List, Optional, Tuple, Any
import asyncio

from telethon import TelegramClient, functions
from telethon.errors import FloodWaitError, AuthKeyError

from database.db_manager import db_manager
from utils.logger import session_logger
from utils.helpers import flood_wait_handler, retry_handler
from core.session_manager import session_manager
from enum import Enum


class AccountStatus(Enum):
    """계정 상태 열거형"""
    INACTIVE = "inactive"  # 비활성 (세션 파일만 있음)
    ACTIVE = "active"      # 활성 (DB에 등록됨)
    CONNECTED = "connected"  # 연결됨
    ERROR = "error"        # 오류 상태


class AccountManager:
    """계정 관리를 위한 싱글톤 클래스"""
    _instance: Optional['AccountManager'] = None
    
    def __new__(cls) -> 'AccountManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """초기화"""
        if not hasattr(self, '_initialized') or not self._initialized:
            self.clients: Dict[str, TelegramClient] = {}  # 활성 클라이언트
            self.connecting: List[str] = []  # 연결 중인 계정
            self._initialized = True

    async def connect_account(self, phone: str) -> Tuple[bool, Optional[str]]:
        """단일 계정 연결"""
        # 이미 연결된 경우
        if phone in self.clients:
            session_logger.info(f"이미 연결된 계정: {phone}")
            return True, None
            
        # 연결 중인 경우
        if phone in self.connecting:
            session_logger.info(f"연결 중인 계정: {phone}")
            return False, "연결 중"
            
        # 연결 시작
        self.connecting.append(phone)
        session_logger.info(f"계정 연결 시작: {phone}")
        
        try:
            # 세션 파일 경로
            session_file = f"sessions/{phone}"
            
            # API 정보 가져오기
            api_id, api_hash = await session_manager.get_api_credentials()
            if not api_id or not api_hash:
                self.connecting.remove(phone)
                session_logger.error(f"API 정보 없음: {phone}")
                return False, "API 정보 없음"
                
            # 클라이언트 생성
            client = TelegramClient(
                session_file,
                api_id,
                api_hash,
                device_model="TMC Telethon",
                system_version="Windows 11",
                app_version="1.0.0"
            )

            # 연결 시도
            await client.connect()

            # 인증 확인
            if not await client.is_user_authorized():
                await client.disconnect()
                session_logger.warning(f"세션 파일 인증 실패: {phone}")
                return False, "세션 인증 실패"

            # 연결 완료
            self.clients[phone] = client
            await db_manager.update_account_status(phone, AccountStatus.CONNECTED.value)
            session_logger.info(f"세션 파일 연결 성공: {phone}")
            return True, None

        except FloodWaitError as e:
            session_logger.warning(f"세션 파일 연결 중 Flood Wait: {phone}, {e.seconds}초")
            await flood_wait_handler.handle_flood_wait(phone, e.seconds)
            return False, f"Flood Wait: {e.seconds}초"

        except AuthKeyError:
            session_logger.error(f"세션 파일 인증 키 오류: {phone}")
            return False, "인증 키 오류"

        except Exception as e:
            session_logger.error(f"세션 파일 연결 실패: {phone}, {e}")
            return False, str(e)

    async def connect_multiple(self, phones: List[str], parallel: int = 3) -> Tuple[int, List[Dict[str, Any]]]:
        """
        여러 계정 동시 연결
        Returns: (성공 개수, 결과 목록)
        """
        # 결과 초기화
        results = []
        success_count = 0

        # 병렬 연결 제한
        semaphore = asyncio.Semaphore(parallel)

        async def connect_with_semaphore(phone: str) -> Dict[str, Any]:
            async with semaphore:
                success, error = await self.connect_account(phone)
                return {
                    "phone": phone,
                    "success": success,
                    "error": error
                }

        # 병렬 연결 실행
        tasks = [connect_with_semaphore(phone) for phone in phones]
        results = await asyncio.gather(*tasks)

        # 성공 개수 계산
        success_count = sum(1 for result in results if result["success"])

        session_logger.info(f"다중 계정 연결 완료: {success_count}/{len(phones)} 성공")
        return success_count, results

    async def disconnect_account(self, phone: str) -> bool:
        """단일 계정 연결 해제"""
        try:
            if phone not in self.clients:
                session_logger.warning(f"연결되지 않은 계정: {phone}")
                return False

            # 클라이언트 연결 해제
            client = self.clients[phone]
            await client.disconnect()

            # 상태 업데이트
            await db_manager.update_account_status(phone, AccountStatus.ACTIVE.value)

            # 클라이언트 제거
            del self.clients[phone]

            session_logger.info(f"계정 연결 해제 성공: {phone}")
            return True

        except Exception as e:
            session_logger.error(f"계정 연결 해제 실패: {phone}, {e}")
            return False

    async def disconnect_all(self) -> int:
        """모든 계정 연결 해제"""
        disconnect_count = 0

        # 모든 계정 연결 해제
        for phone in list(self.clients.keys()):
            try:
                # 클라이언트 연결 해제
                client = self.clients[phone]
                await client.disconnect()

                # 상태 업데이트
                await db_manager.update_account_status(phone, AccountStatus.ACTIVE.value)

                # 클라이언트 제거
                del self.clients[phone]

                disconnect_count += 1
                session_logger.info(f"계정 연결 해제: {phone}")

            except Exception as e:
                session_logger.error(f"계정 연결 해제 실패: {phone}, {e}")

        # 활성 세션 정리
        await session_manager.cleanup_active_sessions()

        session_logger.info(f"모든 계정 연결 해제 완료: {disconnect_count}개")
        return disconnect_count

    async def get_account_info(self, phone: str) -> Optional[Dict[str, Any]]:
        """계정 정보 조회"""
        # DB에서 계정 정보 조회
        account = await db_manager.get_account(phone)
        if not account:
            return None

        # 연결 상태 확인
        is_connected = phone in self.clients
        account["connected"] = is_connected

        # 연결된 경우 최신 정보 업데이트
        if is_connected:
            try:
                client = self.clients[phone]
                me = await client.get_me()
                if me:
                    account["first_name"] = getattr(me, "first_name", account.get("first_name", ""))
                    account["last_name"] = getattr(me, "last_name", account.get("last_name", ""))
                    account["username"] = getattr(me, "username", account.get("username"))
                    account["user_id"] = getattr(me, "id", account.get("user_id"))

                    # DB 업데이트
                    await db_manager.add_account(account)
            except Exception as e:
                session_logger.warning(f"계정 정보 업데이트 실패: {phone}, {e}")

        return account

    async def refresh_account_status(self) -> Dict[str, Any]:
        """계정 상태 새로고침"""
        # 모든 계정 조회
        accounts = await db_manager.get_all_accounts()

        # 상태 통계
        status_counts = {
            "total": len(accounts),
            "connected": len(self.clients),
            "connecting": len(self.connecting),
            "inactive": 0,
            "active": 0,
            "error": 0
        }

        # 연결된 계정 확인
        connected_phones = set(self.clients.keys())

        # 계정 상태 업데이트
        for account in accounts:
            phone = account.get("phone")
            if not phone:
                continue

            current_status = account.get("status")

            if phone in connected_phones:
                # 연결된 상태로 업데이트
                if current_status != AccountStatus.CONNECTED.value:
                    await db_manager.update_account_status(phone, AccountStatus.CONNECTED.value)
            elif phone in self.connecting:
                # 연결 중 상태 유지
                pass
            elif current_status == AccountStatus.CONNECTED.value:
                # 연결 해제된 경우 ACTIVE로 변경
                await db_manager.update_account_status(phone, AccountStatus.ACTIVE.value)
                status_counts["active"] += 1
            elif current_status == AccountStatus.INACTIVE.value:
                status_counts["inactive"] += 1
            elif current_status == AccountStatus.ERROR.value:
                status_counts["error"] += 1

        # 통계 업데이트
        db_stats = await db_manager.get_statistics()

        return {
            "status_counts": status_counts,
            "connected_accounts": list(connected_phones),
            "db_stats": db_stats
        }

    async def join_chat(self, chat_id: str, phones: Optional[List[str]] = None) -> Tuple[int, List[Dict[str, Any]]]:
        """
        채팅 참여
        Returns: (성공 개수, 결과 목록)
        """
        results = []
        success_count = 0

        # 대상 계정 목록
        target_phones = phones or list(self.clients.keys())

        for phone in target_phones:
            result = {
                "phone": phone,
                "success": False,
                "error": None
            }

            # 연결 확인
            if phone not in self.clients:
                result["error"] = "연결되지 않음"
                results.append(result)
                continue

            try:
                client = self.clients[phone]

                # 1회 재시도 허용
                async def join_chat_coro():
                    try:
                        # 채팅 ID가 URL인 경우
                        if chat_id.startswith('https://t.me/'):
                            # 초대 링크인 경우
                            if '/joinchat/' in chat_id or '+' in chat_id:
                                invite_hash = chat_id.split('/')[-1]
                                # telethon 함수로 변경
                                await client(functions.messages.ImportChatInviteRequest(hash=invite_hash))
                            else:
                                # 사용자명인 경우
                                username = chat_id.split('/')[-1]
                                # 올바른 형식으로 변경
                                entity = await client.get_entity(username)
                                await client(functions.channels.JoinChannelRequest(channel=entity))
                        # 사용자명인 경우
                        elif chat_id.startswith('@'):
                            username = chat_id[1:]
                            # 올바른 형식으로 변경
                            entity = await client.get_entity(username)
                            await client(functions.channels.JoinChannelRequest(channel=entity))
                        # 채널 ID인 경우
                        else:
                            # 올바른 형식으로 변경
                            entity = await client.get_entity(chat_id)
                            await client(functions.channels.JoinChannelRequest(channel=entity))
                    except FloodWaitError as e:
                        raise e  # 상위로 전달

                # 재시도 실행
                success, error = await retry_handler.execute_with_retry(
                    join_chat_coro(), phone, "join_chat"
                )

                result["success"] = success
                result["error"] = error

                if success:
                    success_count += 1
                    session_logger.info(f"채팅 참여 성공: {phone} -> {chat_id}")
                else:
                    session_logger.warning(f"채팅 참여 실패: {phone} -> {chat_id}, {error}")

            except Exception as e:
                result["error"] = str(e)
                session_logger.error(f"채팅 참여 중 오류: {phone} -> {chat_id}, {e}")

            results.append(result)

            # 잠시 대기 (1초)
            await asyncio.sleep(1)

        session_logger.info(f"채팅 참여 완료: {success_count}/{len(target_phones)} 성공")
        return success_count, results


# 전역 계정 관리자 인스턴스
account_manager = AccountManager()
