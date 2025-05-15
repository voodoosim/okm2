# session_manager.py - 릴레이 시스템을 위한 확장된 세션 관리
import os
import asyncio
import json
import random
from datetime import datetime
from telethon import TelegramClient
from telethon.errors import FloodWaitError, SessionPasswordNeededError
from dotenv import load_dotenv

class SessionManager:
    """릴레이 시스템을 위한 확장된 세션 관리"""

    def __init__(self):
        load_dotenv()
        self.api_id = int(os.getenv('TELEGRAM_API_ID'))
        self.api_hash = os.getenv('TELEGRAM_API_HASH')
        self.sessions_dir = "sessions"
        self.clients = {}
        self._main_loop = None

        # 릴레이 관련 설정
        self.relay_settings = {
            'min_delay': 1,    # 최소 지연 시간 (초)
            'max_delay': 5,    # 최대 지연 시간 (초)
            'flood_wait': 30,  # Flood wait 시 대기 시간
            'retry_count': 3   # 재시도 횟수
        }

        # 세션 디렉토리 생성
        os.makedirs(self.sessions_dir, exist_ok=True)

    def get_session_files(self):
        """세션 파일 목록 반환"""
        return [f for f in os.listdir(self.sessions_dir) if f.endswith('.session')]

    async def create_session(self, phone_number, session_name):
        """새 세션 생성"""
        session_path = os.path.join(self.sessions_dir, f"{session_name}.session")

        if os.path.exists(session_path):
            raise Exception(f"세션 '{session_name}'이 이미 존재합니다")

        client = TelegramClient(session_path, self.api_id, self.api_hash)

        try:
            await client.start(phone=phone_number)
            # 2FA 확인
            if not await client.is_user_authorized():
                raise SessionPasswordNeededError("2FA 인증이 필요합니다")

            # 세션 저장 후 연결 종료
            await client.disconnect()
            return True
        except Exception as e:
            await client.disconnect()
            raise e

    async def connect_session(self, session_name):
        """세션 연결"""
        session_path = os.path.join(self.sessions_dir, f"{session_name}.session")

        if not os.path.exists(session_path):
            raise Exception(f"세션 파일을 찾을 수 없습니다: {session_name}")

        if session_name in self.clients:
            return self.clients[session_name]

        # 현재 실행 중인 루프 저장
        self._main_loop = asyncio.get_event_loop()

        client = TelegramClient(session_path, self.api_id, self.api_hash)
        await client.start()

        # 사용자 정보 확인
        me = await client.get_me()
        self.clients[session_name] = {
            'client': client,
            'user': me,
            'last_message_time': None,
            'message_count': 0,
            'status': 'connected'
        }

        return self.clients[session_name]

    async def disconnect_session(self, session_name):
        """세션 연결 해제"""
        if session_name in self.clients:
            await self.clients[session_name]['client'].disconnect()
            del self.clients[session_name]

    async def disconnect_all(self):
        """모든 세션 해제"""
        for session_name in list(self.clients.keys()):
            await self.disconnect_session(session_name)

    def get_connected_sessions(self):
        """연결된 세션 정보 반환"""
        return {name: info['user'] for name, info in self.clients.items()}

    async def test_session(self, session_name):
        """세션 테스트"""
        if session_name not in self.clients:
            raise Exception(f"세션 '{session_name}'이 연결되지 않음")

        client = self.clients[session_name]['client']

        # 연결 상태 확인
        if not client.is_connected():
            await client.connect()

        await client.send_message('me', f'테스트 메시지 - {session_name}')
        return True

    async def send_message_with_retry(self, session_name, target, message, retry_count=None):
        """재시도 기능이 있는 메시지 발송"""
        if retry_count is None:
            retry_count = self.relay_settings['retry_count']

        if session_name not in self.clients:
            raise Exception(f"세션 '{session_name}'이 연결되지 않음")

        client = self.clients[session_name]['client']
        session_info = self.clients[session_name]

        for attempt in range(retry_count):
            try:
                # Flood wait 처리
                if session_info.get('flood_wait_until'):
                    wait_time = session_info['flood_wait_until'] - datetime.now().timestamp()
                    if wait_time > 0:
                        await asyncio.sleep(wait_time)
                        session_info.pop('flood_wait_until', None)

                # 메시지 발송
                await client.send_message(target, message)

                # 성공 시 통계 업데이트
                session_info['last_message_time'] = datetime.now()
                session_info['message_count'] += 1
                session_info['status'] = 'success'

                return True

            except FloodWaitError as e:
                # Flood wait 에러 처리
                wait_time = e.seconds
                session_info['flood_wait_until'] = datetime.now().timestamp() + wait_time
                session_info['status'] = f'flood_wait_{wait_time}s'

                if attempt < retry_count - 1:
                    await asyncio.sleep(wait_time)
                else:
                    raise Exception(f"FloodWaitError: {wait_time}초 대기 필요")

            except Exception as e:
                session_info['status'] = f'error_{str(e)[:50]}'
                if attempt < retry_count - 1:
                    await asyncio.sleep(2 ** attempt)  # 지수 백오프
                else:
                    raise e

        return False

    def get_session_stats(self):
        """세션별 통계 반환"""
        stats = {}
        for session_name, info in self.clients.items():
            stats[session_name] = {
                'user': info['user'].first_name,
                'message_count': info.get('message_count', 0),
                'last_message': info.get('last_message_time'),
                'status': info.get('status', 'connected')
            }
        return stats

    async def check_all_sessions_health(self):
        """모든 세션의 건강 상태 확인"""
        health_report = {}

        for session_name, info in self.clients.items():
            try:
                client = info['client']
                if client.is_connected():
                    # 간단한 API 호출로 연결 상태 확인
                    await client.get_me()
                    health_report[session_name] = 'healthy'
                else:
                    health_report[session_name] = 'disconnected'
            except Exception as e:
                health_report[session_name] = f'error: {str(e)[:50]}'

        return health_report

    def save_session_stats(self, filename='session_stats.json'):
        """세션 통계를 파일로 저장"""
        stats = self.get_session_stats()

        # datetime 객체를 문자열로 변환
        for session_name, stat in stats.items():
            if stat['last_message']:
                stat['last_message'] = stat['last_message'].isoformat()

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"통계 저장 실패: {e}")

    def load_session_stats(self, filename='session_stats.json'):
        """세션 통계를 파일에서 로드"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                stats = json.load(f)

            # 기존 세션 정보에 통계 적용
            for session_name, stat in stats.items():
                if session_name in self.clients:
                    self.clients[session_name]['message_count'] = stat.get('message_count', 0)
                    if stat.get('last_message'):
                        self.clients[session_name]['last_message_time'] = datetime.fromisoformat(stat['last_message'])
        except FileNotFoundError:
            pass  # 파일이 없으면 무시
        except Exception as e:
            print(f"통계 로드 실패: {e}")

    def update_relay_settings(self, settings):
        """릴레이 설정 업데이트"""
        self.relay_settings.update(settings)

    def get_random_delay(self):
        """랜덤 지연 시간 생성"""
        return random.uniform(
            self.relay_settings['min_delay'],
            self.relay_settings['max_delay']
        )
