# session_manager.py - 수정된 세션 관리자
import os
import asyncio
from datetime import datetime
from telethon import TelegramClient
from telethon.errors import FloodWaitError, SessionPasswordNeededError
from dotenv import load_dotenv

class SessionManager:
    """텔레그램 세션 관리자"""

    def __init__(self):
        # .env 파일 로드
        load_dotenv()

        # API 정보 가져오기 (에러 처리 추가)
        api_id_str = os.getenv('TELEGRAM_API_ID')
        api_hash_str = os.getenv('TELEGRAM_API_HASH')

        if not api_id_str or not api_hash_str:
            raise ValueError("API_ID 또는 API_HASH가 .env 파일에 없습니다!")

        try:
            self.api_id = int(api_id_str)
        except ValueError:
            raise ValueError(f"API_ID가 올바르지 않습니다: {api_id_str}")

        self.api_hash = api_hash_str
        self.sessions_dir = "sessions"
        self.clients = {}

        # 세션 디렉토리 생성
        os.makedirs(self.sessions_dir, exist_ok=True)

        print(f"SessionManager 초기화 완료: API_ID={self.api_id}")

    def get_session_files(self):
        """세션 파일 목록 반환"""
        try:
            files = [f for f in os.listdir(self.sessions_dir) if f.endswith('.session')]
            print(f"발견된 세션 파일: {files}")
            return files
        except Exception as e:
            print(f"세션 파일 목록 가져오기 실패: {e}")
            return []

    async def create_session(self, phone_number, session_name):
        """새 세션 생성"""
        session_path = os.path.join(self.sessions_dir, f"{session_name}.session")
        print(f"세션 생성 시도: {session_path}")

        if os.path.exists(session_path):
            raise Exception(f"세션 '{session_name}'이 이미 존재합니다")

        client = TelegramClient(session_path, self.api_id, self.api_hash)

        try:
            print("Telethon 클라이언트 시작...")
            await client.start(phone=phone_number)

            # 인증 확인
            if not await client.is_user_authorized():
                raise SessionPasswordNeededError("2FA 인증이 필요합니다")

            print("세션 생성 성공, 연결 해제 중...")
            await client.disconnect()
            return True

        except Exception as e:
            print(f"세션 생성 실패: {e}")
            try:
                await client.disconnect()
            except Exception:
                pass
            raise e

    async def connect_session(self, session_name):
        """세션 연결"""
        session_path = os.path.join(self.sessions_dir, f"{session_name}.session")
        print(f"세션 연결 시도: {session_name}")

        if not os.path.exists(session_path):
            raise Exception(f"세션 파일을 찾을 수 없습니다: {session_path}")

        # 이미 연결된 세션인지 확인
        if session_name in self.clients:
            client_info = self.clients[session_name]
            if client_info['client'].is_connected():
                print(f"세션 {session_name}은 이미 연결되어 있습니다")
                return client_info
            else:
                # 연결이 끊어진 클라이언트는 제거
                print(f"연결이 끊어진 세션 {session_name} 정리 중...")
                try:
                    await client_info['client'].disconnect()
                except Exception:
                    pass
                del self.clients[session_name]

        # 새 클라이언트 생성
        print(f"새 클라이언트 생성: {session_name}")
        client = TelegramClient(session_path, self.api_id, self.api_hash)

        try:
            # 시작 - 자동으로 세션 로드 및 연결
            print("클라이언트 시작 중...")
            await client.start()

            # 연결 상태 확인
            if not client.is_connected():
                raise Exception("클라이언트가 연결되지 않았습니다")

            # 사용자 정보 가져오기
            print("사용자 정보 가져오는 중...")
            me = await client.get_me()

            # 클라이언트 저장
            self.clients[session_name] = {
                'client': client,
                'user': me,
                'last_message_time': None,
                'message_count': 0,
                'status': 'connected'
            }

            print(f"✅ 세션 연결 성공: {session_name} ({me.first_name})")
            return self.clients[session_name]

        except Exception as e:
            print(f"❌ 세션 연결 실패: {session_name} - {e}")
            try:
                await client.disconnect()
            except Exception:
                pass
            raise e

    async def disconnect_session(self, session_name):
        """세션 연결 해제"""
        print(f"세션 연결 해제: {session_name}")

        if session_name in self.clients:
            try:
                await self.clients[session_name]['client'].disconnect()
                print(f"✅ 세션 해제 완료: {session_name}")
            except Exception as e:
                print(f"세션 해제 중 오류: {e}")
            finally:
                del self.clients[session_name]
        else:
            print(f"세션 {session_name}이 연결되어 있지 않습니다")

    async def disconnect_all(self):
        """모든 세션 해제"""
        print("모든 세션 연결 해제...")
        session_names = list(self.clients.keys())

        for session_name in session_names:
            try:
                await self.disconnect_session(session_name)
            except Exception as e:
                print(f"세션 {session_name} 해제 중 오류: {e}")

    def get_connected_sessions(self):
        """연결된 세션 정보 반환"""
        connected = {}
        for name, info in self.clients.items():
            if info['client'].is_connected():
                connected[name] = info['user']
        return connected

    async def test_session(self, session_name):
        """세션 테스트"""
        print(f"세션 테스트: {session_name}")

        if session_name not in self.clients:
            raise Exception(f"세션 '{session_name}'이 연결되지 않음")

        client = self.clients[session_name]['client']

        # 연결 상태 확인
        if not client.is_connected():
            print("클라이언트 연결이 끊어짐, 재연결 시도...")
            await client.connect()

        try:
            await client.send_message('me', f'테스트 메시지 - {session_name} - {datetime.now()}')
            print(f"✅ 테스트 메시지 전송 완료: {session_name}")
            return True
        except Exception as e:
            print(f"❌ 테스트 메시지 전송 실패: {e}")
            raise e

    async def send_message_with_retry(self, session_name, target, message, retry_count=3):
        """재시도 기능이 있는 메시지 발송"""
        print(f"메시지 발송: {session_name} -> {target}")

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
                        print(f"Flood wait 대기 중: {wait_time}초")
                        await asyncio.sleep(wait_time)
                        session_info.pop('flood_wait_until', None)

                # 메시지 발송
                await client.send_message(target, message)

                # 성공 시 통계 업데이트
                session_info['last_message_time'] = datetime.now()
                session_info['message_count'] += 1
                session_info['status'] = 'success'

                print(f"✅ 메시지 발송 성공: {session_name}")
                return True

            except FloodWaitError as e:
                # Flood wait 에러 처리
                wait_time = e.seconds
                session_info['flood_wait_until'] = datetime.now().timestamp() + wait_time
                session_info['status'] = f'flood_wait_{wait_time}s'

                print(f"FloodWaitError: {wait_time}초 대기")

                if attempt < retry_count - 1:
                    await asyncio.sleep(wait_time)
                else:
                    raise Exception(f"FloodWaitError: {wait_time}초 대기 필요")

            except Exception as e:
                print(f"메시지 발송 시도 {attempt + 1} 실패: {e}")
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
            try:
                stats[session_name] = {
                    'user': info['user'].first_name if info['user'] else 'Unknown',
                    'message_count': info.get('message_count', 0),
                    'last_message': info.get('last_message_time'),
                    'status': info.get('status', 'connected')
                }
            except Exception as e:
                print(f"세션 {session_name} 통계 가져오기 실패: {e}")
                stats[session_name] = {
                    'user': 'Error',
                    'message_count': 0,
                    'last_message': None,
                    'status': 'error'
                }
        return stats

    # 기타 메서드들 (기존과 동일)
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
