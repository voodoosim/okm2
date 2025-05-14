# session_gui_modern.py - 완성된 세션별 터미널 + 공통 입력창 GUI
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading
import asyncio
from session_manager import SessionManager
from session_creation_dialog import SessionCreationDialog

class SessionTerminal(ctk.CTkFrame):
    """개별 세션용 터미널"""

    def __init__(self, master, session_name, session_manager, main_gui):
        super().__init__(master)
        self.session_name = session_name
        self.session_manager = session_manager
        self.main_gui = main_gui

        # 세션 정보 표시
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=(10, 5))

        self.status_label = ctk.CTkLabel(
            header_frame,
            text=f"세션: {session_name} - ⚪ 연결안됨",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.status_label.pack(side="left", padx=10, pady=5)

        # 세션 제어 버튼들
        button_frame = ctk.CTkFrame(header_frame)
        button_frame.pack(side="right", padx=10, pady=5)

        self.connect_btn = ctk.CTkButton(button_frame, text="연결", command=self.connect_session, width=80)
        self.connect_btn.pack(side="left", padx=5)

        self.test_btn = ctk.CTkButton(button_frame, text="테스트", command=self.test_session, width=80)
        self.test_btn.pack(side="left", padx=5)

        self.disconnect_btn = ctk.CTkButton(button_frame, text="해제", command=self.disconnect_session, width=80)
        self.disconnect_btn.pack(side="left", padx=5)

        # 터미널 출력 영역
        self.output = ctk.CTkTextbox(self, height=400, font=("Consolas", 11))
        self.output.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        # 초기 메시지
        self.add_output(f"=== {session_name} 세션 터미널 ===")
        self.add_output("이 세션에 대한 모든 활동이 여기에 표시됩니다.")

        # 상태 업데이트
        self.update_status()

    def add_output(self, text):
        """터미널에 출력 추가"""
        timestamp = self.get_timestamp()
        self.output.insert("end", f"[{timestamp}] {text}\n")
        self.output.see("end")

    def get_timestamp(self):
        """현재 시간 반환"""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")

    def update_status(self):
        """세션 상태 업데이트"""
        connected_sessions = self.session_manager.get_connected_sessions()

        if self.session_name in connected_sessions:
            user = connected_sessions[self.session_name]
            status_text = f"세션: {self.session_name} - 🟢 연결됨 ({user.first_name})"
            self.connect_btn.configure(state="disabled")
            self.test_btn.configure(state="normal")
            self.disconnect_btn.configure(state="normal")
        else:
            status_text = f"세션: {self.session_name} - ⚪ 연결안됨"
            self.connect_btn.configure(state="normal")
            self.test_btn.configure(state="disabled")
            self.disconnect_btn.configure(state="disabled")

        self.status_label.configure(text=status_text)

    def connect_session(self):
        """세션 연결"""
        self.add_output("연결 시도 중...")

        async def connect():
            try:
                result = await self.session_manager.connect_session(self.session_name)
                user = result['user']
                self.add_output(f"✅ 연결 성공: {user.first_name} ({user.phone})")
                self.main_gui.root.after(0, self.update_status)
                self.main_gui.root.after(0, self.main_gui.refresh_sessions)
            except Exception as e:
                self.add_output(f"❌ 연결 실패: {e}")
                self.main_gui.root.after(0, self.update_status)

        self.main_gui.run_task(connect())

    def disconnect_session(self):
        """세션 해제"""
        self.add_output("연결 해제 중...")

        async def disconnect():
            try:
                await self.session_manager.disconnect_session(self.session_name)
                self.add_output("✅ 연결 해제 완료")
                self.main_gui.root.after(0, self.update_status)
                self.main_gui.root.after(0, self.main_gui.refresh_sessions)
            except Exception as e:
                self.add_output(f"❌ 연결 해제 실패: {e}")
                self.main_gui.root.after(0, self.update_status)

        self.main_gui.run_task(disconnect())

    def test_session(self):
        """세션 테스트"""
        self.add_output("테스트 메시지 전송 중...")

        async def test():
            try:
                await self.session_manager.test_session(self.session_name)
                self.add_output("✅ 테스트 완료: 자신에게 메시지 전송됨")
            except Exception as e:
                self.add_output(f"❌ 테스트 실패: {e}")

        self.main_gui.run_task(test())

    def execute_command(self, command):
        """명령어 실행 (전역 입력창에서 호출)"""
        self.add_output(f"> {command}")

        parts = command.strip().split()
        if not parts:
            return

        cmd = parts[0].lower()

        if cmd == "connect":
            self.connect_session()
        elif cmd == "disconnect":
            self.disconnect_session()
        elif cmd == "test":
            self.test_session()
        elif cmd == "status":
            self.update_status()
            connected = self.session_name in self.session_manager.get_connected_sessions()
            self.add_output(f"상태: {'연결됨' if connected else '연결안됨'}")
        elif cmd == "clear":
            self.output.delete("1.0", "end")
            self.add_output(f"=== {self.session_name} 세션 터미널 ===")
        elif cmd == "help":
            self.show_help()
        else:
            self.add_output(f"알 수 없는 명령어: {command}")
            self.add_output("'help' 입력시 사용 가능한 명령어를 볼 수 있습니다.")

    def show_help(self):
        """도움말 표시"""
        help_text = """
이 세션에서 사용 가능한 명령어:
  connect - 세션 연결
  disconnect - 세션 해제
  test - 세션 테스트 (자신에게 메시지)
  status - 현재 상태 확인
  clear - 터미널 화면 지우기
  help - 도움말 표시
        """
        self.add_output(help_text)

class GlobalCommandFrame(ctk.CTkFrame):
    """전역 명령어 입력창"""

    def __init__(self, master, main_gui):
        super().__init__(master)
        self.main_gui = main_gui

        # 제목
        ctk.CTkLabel(self, text="명령어 입력", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(10, 5))

        # 현재 선택된 세션 표시
        self.current_session_label = ctk.CTkLabel(self, text="선택된 세션: 없음")
        self.current_session_label.pack(pady=5)

        # 입력 프레임
        input_frame = ctk.CTkFrame(self)
        input_frame.pack(fill="x", padx=10, pady=(5, 10))

        ctk.CTkLabel(input_frame, text="명령:").pack(side="left", padx=(5, 10))

        self.command_entry = ctk.CTkEntry(input_frame, placeholder_text="명령어를 입력하세요...")
        self.command_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.command_entry.bind("<Return>", self.execute_command)

        self.execute_button = ctk.CTkButton(input_frame, text="실행", width=80, command=self.execute_command)
        self.execute_button.pack(side="right", padx=(0, 5))

        # 전역 명령어 버튼들
        global_frame = ctk.CTkFrame(self)
        global_frame.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkLabel(global_frame, text="전역 명령:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=5, pady=(5, 0))

        button_grid = ctk.CTkFrame(global_frame)
        button_grid.pack(fill="x", padx=5, pady=5)

        global_buttons = [
            ("모든 세션 연결", self.main_gui.connect_all_sessions),
            ("모든 세션 해제", self.main_gui.disconnect_all_sessions),
            ("새로고침", self.main_gui.refresh_sessions),
            ("새 세션 생성", self.main_gui.create_session_gui)
        ]

        for i, (text, command) in enumerate(global_buttons):
            btn = ctk.CTkButton(button_grid, text=text, command=command, width=140)
            btn.grid(row=i//2, column=i%2, padx=5, pady=5, sticky="ew")

        button_grid.grid_columnconfigure(0, weight=1)
        button_grid.grid_columnconfigure(1, weight=1)

    def update_selected_session(self, session_name):
        """선택된 세션 업데이트"""
        self.current_session_label.configure(text=f"선택된 세션: {session_name}")

    def execute_command(self, event=None):
        """명령어 실행"""
        command = self.command_entry.get().strip()
        if not command:
            return

        self.command_entry.delete(0, "end")

        # 현재 선택된 탭의 세션에 명령어 전달
        current_tab = self.main_gui.session_tabview.get()
        if current_tab in self.main_gui.session_terminals:
            terminal = self.main_gui.session_terminals[current_tab]
            terminal.execute_command(command)
        else:
            # 일반 로그에 출력
            self.main_gui.log(f"명령어 실행: {command}")

class SessionManagerGUI:
    """CustomTkinter 기반 세션 관리 GUI - 개선된 버전"""

    def __init__(self):
        self.session_manager = SessionManager()
        self.session_terminals = {}  # 세션별 터미널 저장
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
        # CustomTkinter 테마 설정
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # 메인 윈도우
        self.root = ctk.CTk()
        self.root.title("📱 Telegram Session Manager")
        self.root.geometry("1100x800")

        # 메인 컨테이너
        main_container = ctk.CTkFrame(self.root)
        main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # 상단: 세션 목록 탭
        self.session_tabview = ctk.CTkTabview(main_container)
        self.session_tabview.pack(fill="both", expand=True, pady=(0, 10))

        # 하단: 전역 명령어 입력창
        self.command_frame = GlobalCommandFrame(main_container, self)
        self.command_frame.pack(fill="x")

        # 탭 변경 이벤트 바인딩
        self.session_tabview.configure(command=self.on_tab_changed)

        # 초기 개요 탭 생성
        self.setup_overview_tab()

    def setup_overview_tab(self):
        """개요 탭 설정 - 기능 버튼 포함"""
        overview_tab = self.session_tabview.add("📊 개요")

        # 메인 컨테이너
        main_container = ctk.CTkFrame(overview_tab)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # 상단 섹션: 세션 목록 + 제어 버튼
        top_section = ctk.CTkFrame(main_container)
        top_section.pack(fill="both", expand=True, pady=(0, 10))

        # 좌측: 세션 목록
        left_panel = ctk.CTkFrame(top_section)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))

        ctk.CTkLabel(left_panel, text="세션 목록", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 5))

        # 트리뷰
        tree_frame = ctk.CTkFrame(left_panel)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.tree = tk.ttk.Treeview(tree_frame, columns=('상태', '이름', '사용자', '전화번호'), show='headings', height=12)

        for col in self.tree['columns']:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=130)

        self.tree.pack(fill="both", expand=True, padx=5, pady=5)

        # 더블클릭으로 세션 터미널 열기
        self.tree.bind("<Double-1>", self.on_session_double_click)

        # 우측: 제어 버튼들
        right_panel = ctk.CTkFrame(top_section)
        right_panel.pack(side="right", fill="y", padx=(10, 0))

        ctk.CTkLabel(right_panel, text="세션 제어", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(10, 15))

        # 개별 세션 제어 버튼
        session_buttons = [
            ("🔄 새 세션 생성", self.create_session_gui),
            ("🔗 선택 세션 연결", self.connect_session),
            ("❌ 선택 세션 해제", self.disconnect_session),
            ("🧪 선택 세션 테스트", self.test_session),
            ("🖥️ 터미널 열기", self.open_session_terminal),
        ]

        for text, command in session_buttons:
            btn = ctk.CTkButton(right_panel, text=text, command=command, width=180)
            btn.pack(pady=5, padx=15)

        # 구분선
        separator = ctk.CTkFrame(right_panel, height=2)
        separator.pack(fill="x", padx=15, pady=15)

        # 전역 제어 버튼
        ctk.CTkLabel(right_panel, text="전역 제어", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(5, 15))

        global_buttons = [
            ("🚀 모든 세션 연결", self.connect_all_sessions),
            ("🔚 모든 세션 해제", self.disconnect_all_sessions),
            ("🔄 목록 새로고침", self.refresh_sessions),
        ]

        for text, command in global_buttons:
            btn = ctk.CTkButton(right_panel, text=text, command=command, width=180)
            btn.pack(pady=5, padx=15)

        # 하단: 로그 영역
        log_frame = ctk.CTkFrame(main_container)
        log_frame.pack(fill="x", pady=(0, 0))

        ctk.CTkLabel(log_frame, text="전역 로그", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))

        self.log_textbox = ctk.CTkTextbox(log_frame, height=120, font=("Consolas", 10))
        self.log_textbox.pack(fill="x", padx=10, pady=(0, 10))

    def on_session_double_click(self, event):
        """세션 더블클릭 시 터미널 탭 열기"""
        selection = self.tree.selection()
        if not selection:
            return

        item = self.tree.item(selection[0])
        session_name = item['values'][1]
        self.create_session_terminal(session_name)

    def open_session_terminal(self):
        """선택된 세션의 터미널 탭 열기"""
        session_name = self.get_selected_session()
        if session_name:
            self.create_session_terminal(session_name)

    def create_session_terminal(self, session_name):
        """세션 터미널 탭 생성"""
        tab_name = f"🖥️ {session_name}"

        # 이미 존재하는 탭인지 확인
        if tab_name not in self.session_terminals:
            session_tab = self.session_tabview.add(tab_name)
            terminal = SessionTerminal(session_tab, session_name, self.session_manager, self)
            terminal.pack(fill="both", expand=True)
            self.session_terminals[tab_name] = terminal

        # 해당 탭으로 전환
        self.session_tabview.set(tab_name)
        self.command_frame.update_selected_session(session_name)

    def on_tab_changed(self):
        """탭 변경 이벤트"""
        current_tab = self.session_tabview.get()

        if current_tab == "📊 개요":
            self.command_frame.update_selected_session("없음")
        elif current_tab in self.session_terminals:
            # 탭 이름에서 세션명 추출
            session_name = current_tab.replace("🖥️ ", "")
            self.command_frame.update_selected_session(session_name)
            # 세션 상태 업데이트
            self.session_terminals[current_tab].update_status()

    def log(self, message):
        """전역 로그 출력"""
        timestamp = self.get_timestamp()
        self.log_textbox.insert("end", f"[{timestamp}] {message}\n")
        self.log_textbox.see("end")

    def get_timestamp(self):
        """현재 시간 반환"""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")

    def refresh_sessions(self):
        """세션 목록 새로고침"""
        # 기존 목록 클리어
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 세션 파일 가져오기
        session_files = self.session_manager.get_session_files()
        connected_sessions = self.session_manager.get_connected_sessions()

        for session_file in session_files:
            session_name = session_file[:-8]

            if session_name in connected_sessions:
                user = connected_sessions[session_name]
                status = "🟢 연결됨"
                username = f"{user.first_name} {user.last_name or ''}"
                phone = user.phone or ""
            else:
                status = "⚪ 연결안됨"
                username = ""
                phone = ""

            self.tree.insert('', 'end', values=(status, session_name, username, phone))

        # 모든 세션 터미널 상태 업데이트
        for terminal in self.session_terminals.values():
            terminal.update_status()

        self.log(f"세션 목록 새로고침 완료 - 총 {len(session_files)}개")

    def get_selected_session(self):
        """선택된 세션 반환"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("선택 오류", "세션을 선택해주세요.")
            return None

        item = self.tree.item(selection[0])
        return item['values'][1]

    # 세션 작업 메서드들
    def create_session_gui(self):
        """세션 생성"""
        dialog = SessionCreationDialog(self.root)
        self.root.wait_window(dialog.window)
        if dialog.result:
            self.log("세션 생성 완료!")
            self.refresh_sessions()

    def connect_session(self):
        """선택된 세션 연결"""
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
        """선택된 세션 해제"""
        session_name = self.get_selected_session()
        if not session_name:
            return

        self.log(f"세션 해제: {session_name}")
        self.run_task(self.session_manager.disconnect_session(session_name))

    def test_session(self):
        """선택된 세션 테스트"""
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

    def run(self):
        """GUI 실행"""
        self.root.mainloop()

def main():
    """메인 함수"""
    app = SessionManagerGUI()
    app.run()

if __name__ == "__main__":
    main()
