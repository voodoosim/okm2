# session_creation_dialog.py - 완전 수정된 버전
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import asyncio
import os
from telethon import TelegramClient
from session_manager import SessionManager

class SessionCreationDialog:
    """세션 생성 전용 다이얼로그"""

    def __init__(self, parent):
        self.parent = parent
        self.result = None
        self.window = tk.Toplevel(parent)
        self.window.title("새 세션 생성")
        self.window.geometry("400x300")
        self.window.transient(parent)
        self.window.grab_set()
        self.setup_ui()

    def setup_ui(self):
        """UI 설정"""
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 제목
        ttk.Label(main_frame, text="새 세션 생성", font=('Arial', 14, 'bold')).pack(pady=(0, 20))

        # 전화번호 입력
        ttk.Label(main_frame, text="전화번호 (+82 형식):").pack(anchor=tk.W)
        self.phone_entry = ttk.Entry(main_frame, width=30)
        self.phone_entry.pack(pady=(5, 15), fill=tk.X)
        self.phone_entry.insert(0, "+82")

        # 세션 이름 입력
        ttk.Label(main_frame, text="세션 이름:").pack(anchor=tk.W)
        self.name_entry = ttk.Entry(main_frame, width=30)
        self.name_entry.pack(pady=(5, 15), fill=tk.X)

        # 인증 코드 입력 (숨김)
        self.code_frame = ttk.Frame(main_frame)
        self.code_label = ttk.Label(self.code_frame, text="인증 코드:")
        self.code_entry = ttk.Entry(self.code_frame, width=30)

        # 상태
        self.status_label = ttk.Label(main_frame, text="전화번호와 세션 이름을 입력하세요")
        self.status_label.pack(pady=10)

        # 버튼
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)

        self.create_button = ttk.Button(button_frame, text="세션 생성", command=self.start_creation)
        self.create_button.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="취소", command=self.cancel).pack(side=tk.LEFT)

    def start_creation(self):
        """세션 생성 시작"""
        phone = self.phone_entry.get().strip()
        name = self.name_entry.get().strip()

        if not phone or not name:
            messagebox.showwarning("입력 오류", "전화번호와 세션 이름을 입력하세요.")
            return

        if not phone.startswith('+'):
            messagebox.showwarning("형식 오류", "전화번호는 +로 시작해야 합니다.")
            return

        self.create_button.configure(state='disabled')
        self.status_label.configure(text="인증 코드 요청 중...")

        thread = threading.Thread(target=self.create_session_thread, args=(phone, name), daemon=True)
        thread.start()

    def create_session_thread(self, phone, name):
        """세션 생성 스레드"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.create_session_async(phone, name))

            if result:
                self.window.after(0, self.creation_complete)
            else:
                self.window.after(0, self.creation_failed)
        except Exception as exception:
            self.window.after(0, lambda err=str(exception): self.creation_error(err))
        finally:
            loop.close()

    async def create_session_async(self, phone, name):
        """세션 생성"""
        manager = SessionManager()
        session_path = os.path.join(manager.sessions_dir, f"{name}.session")

        if os.path.exists(session_path):
            self.window.after(0, lambda: messagebox.showerror("오류", f"세션 '{name}'이 이미 존재합니다"))
            return False

        client = TelegramClient(session_path, manager.api_id, manager.api_hash)

        try:
            await client.connect()
            await client.send_code_request(phone)

            self.window.after(0, self.show_code_input)
            code = await self.wait_for_code()

            if not code:
                return False

            await client.sign_in(phone, code)
            await client.disconnect()
            return True

        except Exception as client_error:
            await client.disconnect()
            raise client_error

    def show_code_input(self):
        """인증 코드 입력 UI"""
        self.status_label.configure(text="텔레그램에서 받은 인증 코드를 입력하세요")

        self.code_frame.pack(pady=(0, 15), fill=tk.X)
        self.code_label.pack(anchor=tk.W)
        self.code_entry.pack(pady=(5, 0), fill=tk.X)
        self.code_entry.focus()

        self.create_button.configure(text="인증 코드 확인", state='normal', command=self.submit_code)

    async def wait_for_code(self):
        """코드 입력 대기"""
        self.code_input = None
        while self.code_input is None:
            await asyncio.sleep(0.1)
        return self.code_input

    def submit_code(self):
        """인증 코드 제출"""
        code = self.code_entry.get().strip()
        if not code:
            messagebox.showwarning("입력 오류", "인증 코드를 입력하세요.")
            return

        self.code_input = code
        self.create_button.configure(state='disabled')
        self.status_label.configure(text="로그인 중...")

    def creation_complete(self):
        """생성 완료"""
        self.status_label.configure(text="세션 생성 완료!")
        self.result = True
        self.window.after(1000, self.close)

    def creation_failed(self):
        """생성 실패"""
        self.status_label.configure(text="세션 생성 실패")
        self.create_button.configure(state='normal')

    def creation_error(self, error_msg):
        """생성 오류"""
        self.status_label.configure(text=f"오류: {error_msg}")
        self.create_button.configure(state='normal')
        messagebox.showerror("세션 생성 오류", error_msg)

    def cancel(self):
        """취소"""
        self.result = False
        self.close()

    def close(self):
        """닫기"""
        self.window.destroy()
