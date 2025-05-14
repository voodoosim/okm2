# relay_chat_simple.py - 수정된 간결한 릴레이 채팅 시스템
import customtkinter as ctk
import asyncio
import json
import random


class RelayChat:
    """간결한 릴레이 채팅 시스템"""

    def __init__(self, session_manager):
        self.sm = session_manager
        self.group_id = None
        self.sessions = []
        self.messages = []
        self.interval = 30
        self.random_delay = 5
        self.running = False
        self.task = None
        self.current_session = 0
        self.current_message = 0
        self.total_sent = 0

    async def start(self):
        """릴레이 시작"""
        if self.running:
            return "이미 실행 중"

        if not all([self.group_id, self.sessions, self.messages]):
            return "설정이 완료되지 않음"

        self.running = True
        self.task = asyncio.create_task(self._relay_loop())
        return "릴레이 시작됨"

    async def stop(self):
        """릴레이 중지"""
        self.running = False
        if self.task:
            self.task.cancel()
        return "릴레이 중지됨"

    async def _relay_loop(self):
        """릴레이 메인 루프"""
        while self.running:
            try:
                # 현재 세션과 메시지
                session = self.sessions[self.current_session]
                message = self.messages[self.current_message]

                # 메시지 전송
                if await self._send_message(session, message):
                    self.total_sent += 1

                # 다음 세션/메시지로 이동
                self._next_turn()

                # 딜레이
                delay = self.interval + random.uniform(-self.random_delay, self.random_delay)
                await asyncio.sleep(max(1, delay))

            except Exception as e:
                print(f"릴레이 오류: {e}")

    async def _send_message(self, session, message):
        """메시지 전송"""
        if session not in self.sm.clients:
            return False

        try:
            client = self.sm.clients[session]['client']
            await client.send_message(self.group_id, message)
            return True
        except Exception:
            return False

    def _next_turn(self):
        """다음 턴으로 이동"""
        self.current_session = (self.current_session + 1) % len(self.sessions)

        if self.current_session == 0:
            self.current_message = (self.current_message + 1) % len(self.messages)

    def save_config(self):
        """설정 저장"""
        config = {
            'group_id': self.group_id,
            'sessions': self.sessions,
            'messages': self.messages,
            'interval': self.interval,
            'random_delay': self.random_delay
        }
        try:
            with open('relay_config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def load_config(self):
        """설정 로드"""
        try:
            with open('relay_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.group_id = config.get('group_id')
                self.sessions = config.get('sessions', [])
                self.messages = config.get('messages', [])
                self.interval = config.get('interval', 30)
                self.random_delay = config.get('random_delay', 5)
        except Exception:
            pass


class RelayGUI(ctk.CTkFrame):
    """간결한 릴레이 GUI"""

    def __init__(self, parent, session_manager):
        super().__init__(parent)
        self.relay = RelayChat(session_manager)
        self.relay.load_config()
        self.setup_ui()
        self.update_status()

    def setup_ui(self):
        """UI 설정"""
        # 제목
        ctk.CTkLabel(self, text="🔄 릴레이 채팅",
                    font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)

        # 상태
        self.status_label = ctk.CTkLabel(self, text="정지됨")
        self.status_label.pack(pady=5)

        # 그룹 ID
        ctk.CTkLabel(self, text="그룹 ID (숫자):").pack(anchor="w", padx=20)
        self.group_entry = ctk.CTkEntry(self, placeholder_text="-1001234567890")
        self.group_entry.pack(fill="x", padx=20, pady=5)
        if self.relay.group_id:
            self.group_entry.insert(0, str(self.relay.group_id))

        # 세션 선택
        ctk.CTkLabel(self, text="세션 선택:").pack(anchor="w", padx=20, pady=(10,0))
        self.session_frame = ctk.CTkScrollableFrame(self, height=100)
        self.session_frame.pack(fill="x", padx=20, pady=5)
        self.session_checkboxes = {}
        self.refresh_sessions()

        # 메시지
        ctk.CTkLabel(self, text="메시지:").pack(anchor="w", padx=20, pady=(10,0))
        self.message_text = ctk.CTkTextbox(self, height=80)
        self.message_text.pack(fill="x", padx=20, pady=5)

        # 메시지 버튼
        msg_btn_frame = ctk.CTkFrame(self)
        msg_btn_frame.pack(fill="x", padx=20, pady=5)
        ctk.CTkButton(msg_btn_frame, text="추가", command=self.add_message, width=80).pack(side="left", padx=5)
        ctk.CTkButton(msg_btn_frame, text="삭제", command=self.del_message, width=80).pack(side="left", padx=5)

        # 메시지 목록
        self.message_list = ctk.CTkScrollableFrame(self, height=80)
        self.message_list.pack(fill="x", padx=20, pady=5)
        self.refresh_messages()

        # 설정
        setting_frame = ctk.CTkFrame(self)
        setting_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(setting_frame, text="간격(초):").pack(side="left", padx=5)
        self.interval_entry = ctk.CTkEntry(setting_frame, width=60)
        self.interval_entry.pack(side="left", padx=5)
        self.interval_entry.insert(0, str(self.relay.interval))

        ctk.CTkLabel(setting_frame, text="랜덤(±):").pack(side="left", padx=5)
        self.random_entry = ctk.CTkEntry(setting_frame, width=60)
        self.random_entry.pack(side="left", padx=5)
        self.random_entry.insert(0, str(self.relay.random_delay))

        # 제어 버튼
        ctrl_frame = ctk.CTkFrame(self)
        ctrl_frame.pack(fill="x", padx=20, pady=10)

        self.start_btn = ctk.CTkButton(ctrl_frame, text="시작", command=self.start_relay)
        self.start_btn.pack(side="left", fill="x", expand=True, padx=5)

        self.stop_btn = ctk.CTkButton(ctrl_frame, text="중지", command=self.stop_relay)
        self.stop_btn.pack(side="left", fill="x", expand=True, padx=5)

        ctk.CTkButton(ctrl_frame, text="저장", command=self.save_config, width=80).pack(side="right", padx=5)

    def refresh_sessions(self):
        """세션 목록 새로고침"""
        for widget in self.session_frame.winfo_children():
            widget.destroy()
        self.session_checkboxes.clear()

        if not hasattr(self.relay.sm, 'get_session_files'):
            return

        try:
            session_files = self.relay.sm.get_session_files()
            connected = self.relay.sm.get_connected_sessions()

            for file in session_files:
                name = file[:-8]
                status = "🟢" if name in connected else "⚪"
                cb = ctk.CTkCheckBox(self.session_frame, text=f"{status} {name}")
                cb.pack(anchor="w", pady=2)
                if name in self.relay.sessions:
                    cb.select()
                self.session_checkboxes[name] = cb
        except Exception:
            pass

    def add_message(self):
        """메시지 추가"""
        text = self.message_text.get("1.0", "end-1c").strip()
        if text:
            self.relay.messages.append(text)
            self.message_text.delete("1.0", "end")
            self.refresh_messages()

    def del_message(self):
        """마지막 메시지 삭제"""
        if self.relay.messages:
            self.relay.messages.pop()
            self.refresh_messages()

    def refresh_messages(self):
        """메시지 목록 새로고침"""
        for widget in self.message_list.winfo_children():
            widget.destroy()

        for i, msg in enumerate(self.relay.messages):
            preview = msg[:30] + "..." if len(msg) > 30 else msg
            ctk.CTkLabel(self.message_list, text=f"{i+1}. {preview}").pack(anchor="w", pady=1)

    def save_config(self):
        """설정 저장"""
        # UI에서 값 수집
        try:
            self.relay.group_id = int(self.group_entry.get().strip())
        except ValueError:
            self.relay.group_id = None

        self.relay.sessions = [name for name, cb in self.session_checkboxes.items() if cb.get()]

        try:
            self.relay.interval = int(self.interval_entry.get())
            self.relay.random_delay = int(self.random_entry.get())
        except ValueError:
            pass

        self.relay.save_config()

    def start_relay(self):
        """릴레이 시작"""
        self.save_config()

        def run():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.relay.start())
            finally:
                loop.close()

        import threading
        threading.Thread(target=run, daemon=True).start()

    def stop_relay(self):
        """릴레이 중지"""
        def run():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.relay.stop())
            finally:
                loop.close()

        import threading
        threading.Thread(target=run, daemon=True).start()

    def update_status(self):
        """상태 업데이트"""
        if self.relay.running:
            self.status_label.configure(text=f"🟢 실행 중 | 전송: {self.relay.total_sent}개")
            self.start_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
        else:
            self.status_label.configure(text=f"⚪ 정지됨 | 전송: {self.relay.total_sent}개")
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")

        self.after(1000, self.update_status)
