# mtc/session_connector.py
"""
텔레그램 세션 연동 프로그램
- 기존 세션 파일을 로드하여 연결
- 다중 세션 동시 관리
- 간단하고 직관적인 인터페이스
"""

import asyncio
import os
from telethon import TelegramClient, errors
from dotenv import load_dotenv


class SessionConnector:
    """세션 연동 관리 클래스"""

    def __init__(self):
        # .env 파일 로드
        load_dotenv()

        # 설정
        self.sessions_dir = "sessions"
        self.api_id = os.getenv('TELEGRAM_API_ID')
        self.api_hash = os.getenv('TELEGRAM_API_HASH')

        # 연결된 클라이언트들
        self.connected_clients = {}
        self.client_info = {}

        # 세션 파일들
        self.session_files = []

        self._validate_config()
        self._load_session_files()

    def _validate_config(self):
        """API 설정 검증"""
        if not self.api_id or not self.api_hash:
            raise ValueError("API ID와 API Hash가 설정되지 않았습니다. .env 파일을 확인하세요.")

        try:
            self.api_id = int(self.api_id)
        except ValueError:
            raise ValueError("API ID는 숫자여야 합니다.")

    def _load_session_files(self):
        """세션 파일 목록 로드"""
        if not os.path.exists(self.sessions_dir):
            print(f"⚠️ {self.sessions_dir} 폴더가 없습니다.")
            os.makedirs(self.sessions_dir)
            return

        self.session_files = [
            f for f in os.listdir(self.sessions_dir)
            if f.endswith('.session')
        ]

        print(f"📁 {len(self.session_files)}개의 세션 파일을 찾았습니다.")

    def list_sessions(self):
        """세션 목록 출력"""
        print("\n=== 사용 가능한 세션 ===")

        if not self.session_files:
            print("세션 파일이 없습니다.")
            return

        for i, session_file in enumerate(self.session_files, 1):
            session_name = session_file[:-8]  # .session 제거
            status = "🟢 연결됨" if session_name in self.connected_clients else "⚪ 연결 안됨"
            print(f"{i}. {session_name} - {status}")

    async def connect_session(self, session_name):
        """단일 세션 연결"""
        session_path = os.path.join(self.sessions_dir, f"{session_name}.session")

        if not os.path.exists(session_path):
            print(f"❌ {session_name}.session 파일이 없습니다.")
            return False

        if session_name in self.connected_clients:
            print(f"ℹ️ {session_name}은 이미 연결되어 있습니다.")
            return True

        try:
            print(f"🔄 {session_name} 연결 중...")

            # 클라이언트 생성
            client = TelegramClient(session_path, self.api_id, self.api_hash)

            # 연결 시작
            await client.start()

            # 사용자 정보 가져오기
            me = await client.get_me()

            # 연결된 클라이언트 저장
            self.connected_clients[session_name] = client
            self.client_info[session_name] = {
                'id': me.id,
                'first_name': me.first_name,
                'last_name': me.last_name or '',
                'username': me.username,
                'phone': me.phone
            }

            print(f"✅ {session_name} 연결 성공!")
            print(f"   👤 {me.first_name} {me.last_name or ''} (@{me.username or '없음'})")
            print(f"   📱 {me.phone}")

            return True

        except errors.AuthKeyUnregisteredError:
            print(f"❌ {session_name}: 인증 키가 만료되었습니다. 세션을 다시 생성하세요.")
            return False
        except errors.UserDeactivatedError:
            print(f"❌ {session_name}: 계정이 비활성화되었습니다.")
            return False
        except errors.SessionPasswordNeededError:
            print(f"❌ {session_name}: 2단계 인증이 필요합니다. 세션을 다시 생성하세요.")
            return False
        except Exception as e:
            print(f"❌ {session_name} 연결 실패: {e}")
            return False

    async def connect_all_sessions(self):
        """모든 세션 연결"""
        print(f"\n🚀 {len(self.session_files)}개 세션 연결 시작...")

        tasks = []
        for session_file in self.session_files:
            session_name = session_file[:-8]
            task = self.connect_session(session_name)
            tasks.append(task)

        # 모든 세션 동시 연결
        results = await asyncio.gather(*tasks)

        # 결과 요약
        success_count = sum(results)
        print(f"\n📊 연결 결과: {success_count}/{len(self.session_files)} 성공")

        return success_count

    async def disconnect_session(self, session_name):
        """단일 세션 연결 해제"""
        if session_name not in self.connected_clients:
            print(f"ℹ️ {session_name}은 연결되어 있지 않습니다.")
            return

        try:
            client = self.connected_clients[session_name]
            await client.disconnect()

            del self.connected_clients[session_name]
            del self.client_info[session_name]

            print(f"✅ {session_name} 연결 해제 완료")

        except Exception as e:
            print(f"❌ {session_name} 연결 해제 실패: {e}")

    async def disconnect_all_sessions(self):
        """모든 세션 연결 해제"""
        print(f"\n🔄 {len(self.connected_clients)}개 세션 연결 해제 중...")

        for session_name in list(self.connected_clients.keys()):
            await self.disconnect_session(session_name)

        print("✅ 모든 세션 연결 해제 완료")

    def get_connected_sessions(self):
        """연결된 세션 정보 반환"""
        return self.client_info.copy()

    def get_client(self, session_name):
        """특정 세션의 클라이언트 반환"""
        return self.connected_clients.get(session_name)

    async def test_session(self, session_name):
        """세션 테스트 (자신에게 메시지 전송)"""
        if session_name not in self.connected_clients:
            print(f"❌ {session_name}이 연결되어 있지 않습니다.")
            return False

        try:
            client = self.connected_clients[session_name]
            await client.send_message('me', f'🤖 {session_name} 세션 테스트 메시지')
            print(f"✅ {session_name} 테스트 성공!")
            return True
        except Exception as e:
            print(f"❌ {session_name} 테스트 실패: {e}")
            return False

    async def test_all_sessions(self):
        """모든 연결된 세션 테스트"""
        print(f"\n🧪 {len(self.connected_clients)}개 세션 테스트 중...")

        tasks = []
        for session_name in self.connected_clients:
            task = self.test_session(session_name)
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        success_count = sum(results)

        print(f"📊 테스트 결과: {success_count}/{len(self.connected_clients)} 성공")
        return success_count


# 사용 예시 함수들
async def main():
    """메인 함수 - 사용 예시"""
    connector = SessionConnector()

    try:
        # 1. 세션 목록 확인
        connector.list_sessions()

        # 2. 사용자 입력 받기
        print("\n✨ 세션 연결 옵션:")
        print("1. 모든 세션 연결")
        print("2. 특정 세션 연결")
        print("3. 연결된 세션 확인")
        print("4. 세션 테스트")
        print("0. 종료")

        while True:
            choice = input("\n선택하세요: ").strip()

            if choice == '1':
                # 모든 세션 연결
                await connector.connect_all_sessions()

            elif choice == '2':
                # 특정 세션 연결
                connector.list_sessions()
                session_num = input("연결할 세션 번호: ").strip()

                try:
                    idx = int(session_num) - 1
                    if 0 <= idx < len(connector.session_files):
                        session_name = connector.session_files[idx][:-8]
                        await connector.connect_session(session_name)
                    else:
                        print("❌ 잘못된 번호입니다.")
                except ValueError:
                    print("❌ 숫자를 입력하세요.")

            elif choice == '3':
                # 연결된 세션 확인
                connected = connector.get_connected_sessions()
                if connected:
                    print("\n=== 연결된 세션 정보 ===")
                    for name, info in connected.items():
                        print(f"🟢 {name}")
                        print(f"   👤 {info['first_name']} {info['last_name']}")
                        print(f"   📱 {info['phone']}")
                        print(f"   🆔 {info['id']}")
                else:
                    print("연결된 세션이 없습니다.")

            elif choice == '4':
                # 세션 테스트
                await connector.test_all_sessions()

            elif choice == '0':
                # 종료
                await connector.disconnect_all_sessions()
                print("👋 프로그램을 종료합니다.")
                break

            else:
                print("❌ 잘못된 선택입니다.")

    except KeyboardInterrupt:
        print("\n\n⚠️ 프로그램이 중단되었습니다.")
        await connector.disconnect_all_sessions()
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        await connector.disconnect_all_sessions()


if __name__ == "__main__":
    print("🚀 텔레그램 세션 연동 프로그램")
    print("==================================")
    asyncio.run(main())
