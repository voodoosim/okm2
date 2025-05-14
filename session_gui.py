# session_gui.py - 가장 간단한 버전 (100줄 이내)
import threading
import asyncio
from session_manager import SessionManager
from session_creation_dialog import SessionCreationDialog

class SessionManagerGUI:
    """간단한 세션 관리 GUI"""

    def __init__(self, root):
        self.root = root
        self.root.title("📱 Telegram Session Manager")
        self.root.geometry("800x600")

        self.session_manager = SessionManager()
        self.loop = None
        self.setup_event_loop()
        self.setup_ui()
        self.refresh_sessions()

    def setup_event_loop(self):
        """전용 이벤트 루프 설정"""
        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()

        threading.Thread(target=run_loop, daemon=True).start()

    def run_task(self, coro):
        """태스크 실행"""
        if self.loop:
            future = asyncio.run_coroutine_threadsafe(coro, self.loop)
            threading.Thread(
                target=lambda: self._handle_task_result(future),
                daemon=True
            ).start()

    def _handle_task_result(self, future):
        """태스크 결과 처리"""
        try:
            future.result(timeout=10)
        except Exception as e:
            self.log(f"오류: {e}")
        finally:
            self.root.after(0, self.refresh_sessions)

    def setup_ui(self):
        """UI 설정"""
        from ui_components import SessionUI
        self.ui = SessionUI(self.root, self)

    def log(self, message):
        """로그 출력"""
        self.ui.add_log(message)

    def refresh_sessions(self):
        """세션 새로고침"""
        self.ui.refresh_session_list(
            self.session_manager.get_session_files(),
            self.session_manager.get_connected_sessions()
        )

    def get_selected_session(self):
        """선택된 세션 반환"""
        return self.ui.get_selected_session()

    # 세션 작업들
    def create_session_gui(self):
        """세션 생성"""
        dialog = SessionCreationDialog(self.root)
        self.root.wait_window(dialog.window)
        if dialog.result:
            self.log("세션 생성 완료!")
            self.refresh_sessions()

    def connect_session(self):
        """세션 연결"""
        session_name = self.get_selected_session()
        if not session_name:
            return

        self.log(f"세션 연결 시작: {session_name}")

        async def connect():
            result = await self.session_manager.connect_session(session_name)
            user = result['user']
            self.log(f"세션 연결 완료: {session_name} ({user.first_name})")

        self.run_task(connect())

    def disconnect_session(self):
        """세션 해제"""
        session_name = self.get_selected_session()
        if not session_name:
            return

        self.log(f"세션 해제: {session_name}")
        self.run_task(self.session_manager.disconnect_session(session_name))

    def test_session(self):
        """세션 테스트"""
        session_name = self.get_selected_session()
        if not session_name:
            return

        self.log(f"세션 테스트: {session_name}")
        self.run_task(self.session_manager.test_session(session_name))

    def connect_all_sessions(self):
        """모든 세션 연결"""
        self.log("모든 세션 연결 시작...")

        async def connect_all():
            for session_file in self.session_manager.get_session_files():
                session_name = session_file[:-8]
                try:
                    await self.session_manager.connect_session(session_name)
                    self.log(f"✅ {session_name} 연결 완료")
                except Exception as e:
                    self.log(f"❌ {session_name} 연결 실패: {e}")

        self.run_task(connect_all())

    def disconnect_all_sessions(self):
        """모든 세션 해제"""
        self.log("모든 세션 해제...")
        self.run_task(self.session_manager.disconnect_all())
