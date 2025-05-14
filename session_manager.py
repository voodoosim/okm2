# session_manager.py - 제대로 된 해결책
import os
import asyncio
from telethon import TelegramClient
from dotenv import load_dotenv

class SessionManager:
    """제대로 된 세션 관리"""

    def __init__(self):
        load_dotenv()
        self.api_id = int(os.getenv('TELEGRAM_API_ID'))
        self.api_hash = os.getenv('TELEGRAM_API_HASH')
        self.sessions_dir = "sessions"
        self.clients = {}
        self._main_loop = None

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
        await client.start(phone=phone_number)

        # 세션 저장 후 연결 종료
        await client.disconnect()
        return True

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
            'user': me
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
        """세션 테스트 - 같은 루프에서 실행"""
        if session_name not in self.clients:
            raise Exception(f"세션 '{session_name}'이 연결되지 않음")

        client = self.clients[session_name]['client']

        # 연결 상태 확인
        if not client.is_connected():
            # 같은 루프에서 재연결
            await client.connect()

        await client.send_message('me', f'테스트 메시지 - {session_name}')
        return True
