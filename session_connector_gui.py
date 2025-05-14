# mtc/session_connector_gui.py
"""
텔레그램 세션 연동 GUI 프로그램 (디버그 향상 버전)
- 시각적 인터페이스로 세션 관리
- 버튼 클릭으로 세션 연결/해제
- 실시간 상태 표시 및 상세 디버깅
"""

import asyncio
import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import traceback
from telethon import TelegramClient, errors
from dotenv import load_dotenv


class SessionConnectorGUI:
    """세션 연동 GUI 클래스"""

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

        # GUI 초기화
        self.root = tk.Tk()
        self.setup_gui()

        # 세션 파일들
        self.session_files = []
        self._validate_config()
        self._load_session_files()

        # 초기 세션 목록 업데이트
        self.update_session_list()

    def _validate_config(self):
        """API 설정 검증 (향상된 디버깅)"""
        self.log("🔍 API 설정 검증 중...")

        if not self.api_id or not self.api_hash:
            error_msg = "API ID와 API Hash가 설정되지 않았습니다.\n.env 파일을 확인하세요."
            self.log(f"❌ {error_msg}")
            messagebox.showerror("설정 오류", error_msg)
            self.root.destroy()
            return

        try:
            self.api_id = int(self.api_id)
            self.log(f"✅ API ID 검증 성공: {self.api_id}")
            self.log(f"🔑 API Hash 길이: {len(self.api_hash)} 문자")
        except ValueError:
            error_msg = "API ID는 숫자여야 합니다."
            self.log(f"❌ {error_msg}")
            messagebox.showerror("설정 오류", error_msg)
            self.root.destroy()
            return

    def _load_session_files(self):
        """세션 파일 목록 로드 (향상된 디버깅)"""
        self.log(f"📁 세션 디렉토리 확인: {self.sessions_dir}")

        if not os.path.exists(self.sessions_dir):
            self.log("⚠️ 세션 디렉토리 없음. 생성 중...")
            os.makedirs(self.sessions_dir)
            self.session_files = []
            return

        all_files = os.listdir(self.sessions_dir)
        self.log(f"📋 디렉토리 내 전체 파일: {len(all_files)}개")

        self.session_files = [f for f in all_files if f.endswith('.session')]

        self.log(f"🔑 발견된 세션 파일: {len(self.session_files)}개")
        for session_file in self.session_files:
            file_path = os.path.join(self.sessions_dir, session_file)
            file_size = os.path.getsize(file_path)
            self.log(f"   - {session_file} ({file_size} bytes)")

    def setup_gui(self):
        """GUI 설정"""
        self.root.title("텔레그램 세션 연동 관리자 (디버그 버전)")
        self.root.geometry("900x700")
        self.root.configure(bg='#2c3e50')

        # 메인 프레임
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 상단 제목
        title_label = tk.Label(main_frame, text="🔗 텔레그램 세션 연동 관리자 (디버그)",
                              font=('Arial', 16, 'bold'), bg='#2c3e50', fg='white')
        title_label.pack(pady=(0, 20))

        # 세션 목록 프레임 (좌측)
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # 세션 목록 라벨
        session_label = ttk.Label(left_frame, text="세션 목록", font=('Arial', 12, 'bold'))
        session_label.pack(anchor=tk.W)

        # 세션 목록 트리뷰
        columns = ('상태', '계정명', '이름', '전화번호', '상태상세')
        self.session_tree = ttk.Treeview(left_frame, columns=columns, show='headings', height=15)

        # 컬럼 설정
        self.session_tree.heading('상태', text='상태')
        self.session_tree.heading('계정명', text='계정명')
        self.session_tree.heading('이름', text='이름')
        self.session_tree.heading('전화번호', text='전화번호')
        self.session_tree.heading('상태상세', text='상태상세')

        self.session_tree.column('상태', width=60)
        self.session_tree.column('계정명', width=100)
        self.session_tree.column('이름', width=120)
        self.session_tree.column('전화번호', width=120)
        self.session_tree.column('상태상세', width=100)

        # 스크롤바
        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.session_tree.yview)
        self.session_tree.configure(yscrollcommand=scrollbar.set)

        self.session_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 컨트롤 패널 (우측)
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))

        # 상태 표시
        self.status_label = ttk.Label(right_frame, text="대기 중...", font=('Arial', 10))
        self.status_label.pack(pady=(0, 10))

        # 버튼들
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(fill=tk.X)

        ttk.Button(button_frame, text="🔄 목록 새로고침", command=self.refresh_sessions).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="🚀 모든 세션 연결", command=self.connect_all_sessions_thread).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="🔗 선택 세션 연결", command=self.connect_selected_session_thread).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="❌ 선택 세션 해제", command=self.disconnect_selected_session_thread).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="🔚 모든 세션 해제", command=self.disconnect_all_sessions_thread).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="🧪 세션 테스트", command=self.test_all_sessions_thread).pack(fill=tk.X, pady=2)

        # 디버그 추가 버튼
        ttk.Separator(button_frame, orient='horizontal').pack(fill=tk.X, pady=5)
        ttk.Button(button_frame, text="🔍 API 검증", command=self.test_api_connection).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="🧹 로그 지우기", command=self.clear_log).pack(fill=tk.X, pady=2)

        # 로그 창
        log_label = ttk.Label(right_frame, text="실시간 로그 (상세 디버깅)", font=('Arial', 10, 'bold'))
        log_label.pack(anchor=tk.W, pady=(20, 5))

        self.log_text = scrolledtext.ScrolledText(right_frame, height=20, width=45,
                                                 bg='#1a1a1a', fg='white', font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 상태바
        self.status_bar = ttk.Label(self.root, text="준비", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def log(self, message, level="INFO"):
        """로그 메시지 추가 (레벨 지원)"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        level = level.upper()

        # 레벨별 이모지 자동 추가
        level_prefixes = {
            "DEBUG": "🔍",
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "WARNING": "⚠️",
            "ERROR": "❌"
        }

        # 메시지에 이미 이모지가 있는지 확인
        has_emoji = any(char in message for char in "❌✅⚠️ℹ️🔍🚀📁📊🔄🔗🧪📤📂🔑👤📱🆔🔚")

        # 이모지가 없으면 레벨에 맞는 이모지 추가
        if not has_emoji and level in level_prefixes:
            message = f"{level_prefixes[level]} {message}"

        formatted_message = f"[{timestamp}][{level}] {message}\n"

        # 스레드 안전하게 GUI 업데이트
        self.root.after(0, self._update_log, formatted_message)

    def _update_log(self, message):
        """로그 GUI 업데이트 (스레드 안전)"""
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)

        # 로그가 너무 길어지면 상위 라인 삭제
        lines = self.log_text.get(1.0, tk.END).count('\n')
        if lines > 500:
            self.log_text.delete(1.0, "2.0")

    def clear_log(self):
        """로그 창 지우기"""
        self.log_text.delete(1.0, tk.END)
        self.log("🧹 로그가 초기화되었습니다.")

    def update_status(self, message):
        """상태 업데이트"""
        self.status_label.config(text=message)
        self.status_bar.config(text=message)

    def update_session_list(self):
        """세션 목록 업데이트 (향상된 상태 표시)"""
        # 기존 목록 클리어
        for item in self.session_tree.get_children():
            self.session_tree.delete(item)

        # 세션 파일 다시 로드
        self._load_session_files()

        # 세션 목록 추가
        for session_file in self.session_files:
            session_name = session_file[:-8]  # .session 제거

            if session_name in self.connected_clients:
                status = "🟢"
                info = self.client_info[session_name]
                name = f"{info['first_name']} {info['last_name']}"
                phone = info['phone']
                status_detail = "연결됨"
            else:
                status = "⚪"
                name = "연결 안됨"
                phone = "연결 안됨"
                status_detail = "미연결"

            self.session_tree.insert('', tk.END, values=(status, session_name, name, phone, status_detail))

        # 상태 업데이트
        connected_count = len(self.connected_clients)
        total_count = len(self.session_files)
        self.update_status(f"연결: {connected_count}/{total_count}")

    def refresh_sessions(self):
        """세션 목록 새로고침"""
        self.log("📁 세션 목록을 새로고침합니다...", "INFO")
        self.update_session_list()

    def test_api_connection(self):
        """API 연결 테스트"""
        self.log("🔍 API 연결 테스트 시작...", "INFO")
        threading.Thread(target=self._test_api_thread).start()

    def _test_api_thread(self):
        """API 테스트 스레드"""
        asyncio.set_event_loop(asyncio.new_event_loop())
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._test_api_async())

    async def _test_api_async(self):
        """API 비동기 테스트"""
        try:
            # 임시 클라이언트 생성하여 API 테스트
            temp_client = TelegramClient(':memory:', self.api_id, self.api_hash)
            self.log("🔑 임시 클라이언트 생성 완료", "SUCCESS")

            # 연결 테스트 (실제 로그인 없이)
            await temp_client.connect()
            self.log("✅ Telegram 서버 연결 성공", "SUCCESS")

            await temp_client.disconnect()
            self.log("🔚 API 테스트 완료", "SUCCESS")

        except Exception as e:
            self.log(f"❌ API 테스트 실패: {e}", "ERROR")
            self.log(f"🔍 상세 오류: {traceback.format_exc()}", "DEBUG")

    # 비동기 작업을 위한 스레드 래퍼 메서드들
    def connect_all_sessions_thread(self):
        """모든 세션 연결 (스레드)"""
        self.log("🚀 모든 세션 연결 작업 시작...", "INFO")
        threading.Thread(target=self._run_async, args=(self.connect_all_sessions,)).start()

    def connect_selected_session_thread(self):
        """선택 세션 연결 (스레드)"""
        self.log("🔗 선택 세션 연결 작업 시작...", "INFO")
        threading.Thread(target=self._run_async, args=(self.connect_selected_session,)).start()

    def disconnect_selected_session_thread(self):
        """선택 세션 해제 (스레드)"""
        self.log("❌ 선택 세션 해제 작업 시작...", "INFO")
        threading.Thread(target=self._run_async, args=(self.disconnect_selected_session,)).start()

    def disconnect_all_sessions_thread(self):
        """모든 세션 해제 (스레드)"""
        self.log("🔚 모든 세션 해제 작업 시작...", "INFO")
        threading.Thread(target=self._run_async, args=(self.disconnect_all_sessions,)).start()

    def test_all_sessions_thread(self):
        """모든 세션 테스트 (스레드)"""
        self.log("🧪 모든 세션 테스트 작업 시작...", "INFO")
        threading.Thread(target=self._run_async, args=(self.test_all_sessions,)).start()

    def _run_async(self, async_func):
        """비동기 함수를 새로운 이벤트 루프에서 실행"""
        try:
            asyncio.set_event_loop(asyncio.new_event_loop())
            loop = asyncio.get_event_loop()
            loop.run_until_complete(async_func())
        except Exception as e:
            self.log(f"❌ 비동기 작업 오류: {e}", "ERROR")
            self.log(f"🔍 상세 오류: {traceback.format_exc()}", "DEBUG")

    async def connect_session(self, session_name):
        """단일 세션 연결 (강화된 디버깅)"""
        session_path = os.path.join(self.sessions_dir, f"{session_name}.session")

        self.log(f"🔍 세션 연결 시작: {session_name}", "INFO")
        self.log(f"📂 세션 경로: {session_path}", "DEBUG")

        # 파일 존재 확인
        if not os.path.exists(session_path):
            self.log(f"❌ 세션 파일 없음: {session_name}.session", "ERROR")
            return False

        # 파일 크기 확인
        file_size = os.path.getsize(session_path)
        self.log(f"📏 세션 파일 크기: {file_size} bytes", "DEBUG")

        # 이미 연결된 세션 확인
        if session_name in self.connected_clients:
            self.log(f"ℹ️ 이미 연결된 세션: {session_name}", "WARNING")
            return True

        try:
            self.log(f"🔑 API 정보 확인 - ID: {self.api_id}", "DEBUG")
            self.log(f"🔑 API Hash 길이: {len(self.api_hash)} 문자", "DEBUG")

            # 클라이언트 생성
            self.log(f"📱 클라이언트 생성 중: {session_name}", "DEBUG")
            client = TelegramClient(session_path, self.api_id, self.api_hash)

            # 연결 시작
            self.log(f"🔗 Telegram 서버 연결 중: {session_name}", "INFO")
            await client.start()
            self.log(f"✅ 서버 연결 성공: {session_name}", "SUCCESS")

            # 사용자 정보 가져오기
            self.log(f"👤 사용자 정보 조회 중: {session_name}", "DEBUG")
            me = await client.get_me()
            self.log(f"📊 사용자 ID 획득: {me.id}", "DEBUG")

            # 연결된 클라이언트 저장
            self.connected_clients[session_name] = client
            self.client_info[session_name] = {
                'id': me.id,
                'first_name': me.first_name,
                'last_name': me.last_name or '',
                'username': me.username,
                'phone': me.phone
            }

            self.log(f"✅ {session_name} 연결 완료!", "SUCCESS")
            self.log(f"   👤 {me.first_name} {me.last_name or ''}", "INFO")
            self.log(f"   📱 {me.phone}", "INFO")
            self.log(f"   🆔 @{me.username or '없음'}", "INFO")

            # GUI 업데이트
            self.root.after(0, self.update_session_list)

            return True

        except errors.AuthKeyUnregisteredError as e:
            self.log(f"❌ {session_name}: 인증 키 만료", "ERROR")
            self.log(f"🔍 세부 사항: {e}", "DEBUG")
            return False
        except errors.UserDeactivatedError as e:
            self.log(f"❌ {session_name}: 계정 비활성화", "ERROR")
            self.log(f"🔍 세부 사항: {e}", "DEBUG")
            return False
        except errors.SessionPasswordNeededError as e:
            self.log(f"❌ {session_name}: 2단계 인증 필요", "ERROR")
            self.log(f"🔍 세부 사항: {e}", "DEBUG")
            return False
        except errors.FloodWaitError as e:
            self.log(f"❌ {session_name}: API 제한 ({e.seconds}초 대기 필요)", "ERROR")
            return False
        except Exception as e:
            self.log(f"❌ {session_name} 연결 실패: {type(e).__name__}", "ERROR")
            self.log(f"🔍 오류 메시지: {str(e)}", "ERROR")
            self.log(f"🔍 상세 추적: {traceback.format_exc()}", "DEBUG")
            return False

    async def connect_all_sessions(self):
        """모든 세션 연결 (향상된 디버깅)"""
        total_sessions = len(self.session_files)
        self.log(f"🚀 전체 {total_sessions}개 세션 연결 시작", "INFO")

        if total_sessions == 0:
            self.log("⚠️ 연결할 세션이 없습니다", "WARNING")
            return

        # 순차적 연결 (동시 연결 시 충돌 방지)
        success_count = 0
        for i, session_file in enumerate(self.session_files, 1):
            session_name = session_file[:-8]
            self.log(f"📊 진행률: {i}/{total_sessions} ({session_name})", "INFO")

            if await self.connect_session(session_name):
                success_count += 1

            # 세션 간 짧은 대기 (API 제한 방지)
            if i < total_sessions:
                await asyncio.sleep(0.5)

        # 결과 요약
        self.log(f"📊 연결 완료: {success_count}/{total_sessions} 성공", "SUCCESS")
        self.log(f"📊 실패: {total_sessions - success_count}개", "INFO" if success_count == total_sessions else "WARNING")

        # GUI 업데이트
        self.root.after(0, self.update_session_list)

    async def connect_selected_session(self):
        """선택 세션 연결"""
        selected = self.session_tree.selection()
        if not selected:
            messagebox.showwarning("선택 오류", "연결할 세션을 선택해주세요.")
            self.log("⚠️ 세션이 선택되지 않았습니다", "WARNING")
            return

        item = self.session_tree.item(selected[0])
        session_name = item['values'][1]
        self.log(f"🔗 선택 세션 연결 시도: {session_name}", "INFO")

        await self.connect_session(session_name)

    async def disconnect_session(self, session_name):
        """단일 세션 연결 해제 (향상된 디버깅)"""
        self.log(f"🔄 세션 해제 시작: {session_name}", "INFO")

        if session_name not in self.connected_clients:
            self.log(f"ℹ️ 연결되지 않은 세션: {session_name}", "WARNING")
            return

        try:
            client = self.connected_clients[session_name]
            self.log(f"🔚 클라이언트 연결 해제 중: {session_name}", "DEBUG")

            await client.disconnect()

            del self.connected_clients[session_name]
            del self.client_info[session_name]

            self.log(f"✅ {session_name} 연결 해제 완료", "SUCCESS")

            # GUI 업데이트
            self.root.after(0, self.update_session_list)

        except Exception as e:
            self.log(f"❌ {session_name} 연결 해제 실패: {e}", "ERROR")
            self.log(f"🔍 상세 오류: {traceback.format_exc()}", "DEBUG")

    async def disconnect_selected_session(self):
        """선택 세션 연결 해제"""
        selected = self.session_tree.selection()
        if not selected:
            messagebox.showwarning("선택 오류", "해제할 세션을 선택해주세요.")
            self.log("⚠️ 세션이 선택되지 않았습니다", "WARNING")
            return

        item = self.session_tree.item(selected[0])
        session_name = item['values'][1]
        self.log(f"❌ 선택 세션 해제 시도: {session_name}", "INFO")

        await self.disconnect_session(session_name)

    async def disconnect_all_sessions(self):
        """모든 세션 연결 해제 (향상된 디버깅)"""
        active_sessions = len(self.connected_clients)
        self.log(f"🔚 전체 {active_sessions}개 활성 세션 해제 시작", "INFO")

        if active_sessions == 0:
            self.log("ℹ️ 연결된 세션이 없습니다", "INFO")
            return

        disconnected_count = 0
        for session_name in list(self.connected_clients.keys()):
            await self.disconnect_session(session_name)
            disconnected_count += 1
            self.log(f"📊 진행률: {disconnected_count}/{active_sessions}", "INFO")

        self.log(f"✅ 모든 세션 연결 해제 완료 ({disconnected_count}개)", "SUCCESS")

        # GUI 업데이트
        self.root.after(0, self.update_session_list)

    async def test_session(self, session_name):
        """세션 테스트 (향상된 디버깅)"""
        self.log(f"🧪 세션 테스트 시작: {session_name}", "INFO")

        if session_name not in self.connected_clients:
            self.log(f"❌ 연결되지 않은 세션: {session_name}", "ERROR")
            return False

        try:
            client = self.connected_clients[session_name]
            test_message = f'🤖 [{session_name}] 세션 테스트 메시지 - {os.getpid()}'

            self.log(f"📤 테스트 메시지 전송 중: {session_name}", "DEBUG")
            await client.send_message('me', test_message)

            self.log(f"✅ {session_name} 테스트 성공!", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"❌ {session_name} 테스트 실패: {e}", "ERROR")
            self.log(f"🔍 상세 오류: {traceback.format_exc()}", "DEBUG")
            return False

    async def test_all_sessions(self):
        """모든 연결된 세션 테스트 (향상된 디버깅)"""
        active_sessions = len(self.connected_clients)
        self.log(f"🧪 전체 {active_sessions}개 활성 세션 테스트 시작", "INFO")

        if active_sessions == 0:
            self.log("❌ 연결된 세션이 없습니다", "WARNING")
            return

        # 순차 테스트 (동시 테스트 시 API 제한 방지)
        success_count = 0
        for i, session_name in enumerate(self.connected_clients, 1):
            self.log(f"📊 테스트 진행률: {i}/{active_sessions} ({session_name})", "INFO")

            if await self.test_session(session_name):
                success_count += 1

            # 테스트 간 짧은 대기
            if i < active_sessions:
                await asyncio.sleep(0.5)

        # 결과 요약
        self.log(f"📊 테스트 완료: {success_count}/{active_sessions} 성공", "SUCCESS")
        if success_count < active_sessions:
            self.log(f"⚠️ 실패: {active_sessions - success_count}개", "WARNING")

    def run(self):
        """GUI 실행"""
        self.log("🚀 GUI 애플리케이션 시작", "SUCCESS")

        # 프로그램 종료 시 세션 해제
        def on_closing():
            self.log("🔚 애플리케이션 종료 중...", "INFO")
            self._run_async(self.disconnect_all_sessions)
            self.root.destroy()

        self.root.protocol("WM_DELETE_WINDOW", on_closing)
        self.root.mainloop()


def main():
    """메인 함수"""
    try:
        app = SessionConnectorGUI()
        app.run()
    except Exception as e:
        error_msg = f"프로그램 실행 중 오류가 발생했습니다:\n{e}\n\n{traceback.format_exc()}"
        messagebox.showerror("치명적 오류", error_msg)
        print(error_msg)


if __name__ == "__main__":
    main()
