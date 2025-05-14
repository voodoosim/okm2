# ui_components.py - UI 구성요소 분리
import tkinter as tk
from tkinter import ttk, messagebox

class SessionUI:
    """세션 관리 UI 구성요소"""

    def __init__(self, root, controller):
        self.root = root
        self.controller = controller
        self.setup_ui()

    def setup_ui(self):
        """UI 구성"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 제목
        ttk.Label(main_frame, text="Telegram Session Manager",
                 font=('Arial', 16, 'bold')).grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # 세션 목록
        self.setup_session_list(main_frame)

        # 버튼들
        self.setup_buttons(main_frame)

        # 로그
        self.setup_log(main_frame)

    def setup_session_list(self, parent):
        """세션 목록 구성"""
        ttk.Label(parent, text="세션 목록:", font=('Arial', 12, 'bold')).grid(
            row=1, column=0, sticky=tk.W, pady=(0, 10))

        columns = ('상태', '이름', '사용자', '전화번호')
        self.tree = ttk.Treeview(parent, columns=columns, show='headings', height=10)

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)

        self.tree.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=2, column=2, sticky=(tk.N, tk.S))

    def setup_buttons(self, parent):
        """버튼 구성"""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)

        buttons = [
            ("새 세션 생성", self.controller.create_session_gui),
            ("세션 연결", self.controller.connect_session),
            ("세션 해제", self.controller.disconnect_session),
            ("모든 세션 연결", self.controller.connect_all_sessions),
            ("모든 세션 해제", self.controller.disconnect_all_sessions),
            ("세션 테스트", self.controller.test_session),
            ("새로고침", self.controller.refresh_sessions)
        ]

        for i, (text, command) in enumerate(buttons):
            ttk.Button(button_frame, text=text, command=command).grid(
                row=i//4, column=i%4, padx=5, pady=5)

    def setup_log(self, parent):
        """로그 구성"""
        ttk.Label(parent, text="로그:", font=('Arial', 12, 'bold')).grid(
            row=4, column=0, sticky=tk.W, pady=(20, 5))

        self.log_text = tk.Text(parent, height=8, width=80)
        self.log_text.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E))

        log_scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        log_scrollbar.grid(row=5, column=2, sticky=(tk.N, tk.S))

    def add_log(self, message):
        """로그 추가"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)

    def refresh_session_list(self, session_files, connected_sessions):
        """세션 목록 새로고침"""
        for item in self.tree.get_children():
            self.tree.delete(item)

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

            self.tree.insert('', tk.END, values=(status, session_name, username, phone))

        self.add_log(f"세션 목록 새로고침 완료 - 총 {len(session_files)}개")

    def get_selected_session(self):
        """선택된 세션 반환"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("선택 오류", "세션을 선택해주세요.")
            return None

        item = self.tree.item(selection[0])
        return item['values'][1]
