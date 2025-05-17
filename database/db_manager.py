# database/db_manager.py
"""
TMC 텔레쏜 데이터베이스 관리자
SQLite를 사용한 계정 및 로그 관리
"""

import aiosqlite
import sqlite3
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, cast
from pathlib import Path
import json
from enum import Enum

# 로컬 임포트
from config.settings import settings


class AccountStatus(Enum):
    INACTIVE = "INACTIVE"
    ACTIVE = "ACTIVE"
    CONNECTED = "CONNECTED"
    ERROR = "ERROR"
    CONNECTING = "CONNECTING"


class MessageStatus(Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    FLOOD_WAIT = "FLOOD_WAIT"
    PENDING = "PENDING"


class DatabaseManager:
    """데이터베이스 관리 클래스"""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.db_path
        self.ensure_db_directory()

    def ensure_db_directory(self):
        """데이터베이스 디렉토리 생성"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    async def initialize(self):
        """데이터베이스 초기화 및 테이블 생성"""
        async with aiosqlite.connect(self.db_path) as db:
            # 계정 테이블
            await db.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    phone VARCHAR(20) PRIMARY KEY,
                    session_path TEXT,
                    api_id INTEGER,
                    api_hash TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    username TEXT,
                    user_id BIGINT,
                    status TEXT DEFAULT 'INACTIVE',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_connected DATETIME,
                    session_string TEXT
                )
            """)

            # 메시지 로그 테이블
            await db.execute("""
                CREATE TABLE IF NOT EXISTS message_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phone VARCHAR(20),
                    chat_id TEXT,
                    message TEXT,
                    message_type TEXT DEFAULT 'text',
                    status TEXT,
                    error_message TEXT,
                    sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (phone) REFERENCES accounts(phone)
                )
            """)

            # 설정 테이블
            await db.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    value_type TEXT DEFAULT 'string',
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 세션 백업 로그 테이블
            await db.execute("""
                CREATE TABLE IF NOT EXISTS session_backups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phone VARCHAR(20),
                    backup_path TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (phone) REFERENCES accounts(phone)
                )
            """)

            await db.commit()

    # ==================== 계정 관리 ====================

    async def add_account(self, account_data: Dict[str, Any]) -> bool:
        """계정 추가 또는 업데이트"""
        try:
            # 필요한 필드 확인
            phone = account_data.get('phone')
            if not phone:
                print("계정 추가 오류: 전화번호가 없음")
                return False

            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO accounts
                    (phone, session_path, session_string, api_id, api_hash, first_name, last_name,
                     username, user_id, status, updated_at, last_connected)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
                """, (
                    phone,
                    account_data.get('session_path', ''),
                    account_data.get('session_string', ''),
                    account_data.get('api_id'),
                    account_data.get('api_hash', ''),
                    account_data.get('first_name', ''),
                    account_data.get('last_name', ''),
                    account_data.get('username', ''),
                    account_data.get('user_id'),
                    account_data.get('status', AccountStatus.INACTIVE.value),
                    account_data.get('last_connected')
                ))
                await db.commit()
                return True
        except Exception as e:
            print(f"계정 추가 오류: {e}")
            return False

    async def get_all_accounts(self) -> List[Dict[str, Any]]:
        """모든 계정 조회"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM accounts ORDER BY created_at") as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows] if rows else []

    async def get_account(self, phone: str) -> Optional[Dict[str, Any]]:
        """특정 계정 조회"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM accounts WHERE phone = ?", (phone,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def update_account_status(self, phone: str, status: str) -> bool:
        """계정 상태 업데이트"""
        try:
            last_connected = datetime.now().isoformat() if status == AccountStatus.CONNECTED.value else None
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE accounts
                    SET status = ?, last_connected = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE phone = ?
                """, (status, last_connected, phone))
                await db.commit()
                return True
        except Exception as e:
            print(f"계정 상태 업데이트 오류: {e}")
            return False

    async def delete_account(self, phone: str) -> bool:
        """계정 삭제"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # 관련 로그도 함께 삭제
                await db.execute("DELETE FROM message_logs WHERE phone = ?", (phone,))
                await db.execute("DELETE FROM session_backups WHERE phone = ?", (phone,))
                await db.execute("DELETE FROM accounts WHERE phone = ?", (phone,))
                await db.commit()
                return True
        except Exception as e:
            print(f"계정 삭제 오류: {e}")
            return False

    # ==================== 메시지 로그 ====================

    async def log_message(self, log_data: Dict[str, Any]) -> bool:
        """메시지 로그 추가"""
        try:
            phone = log_data.get('phone', '')
            chat_id = log_data.get('chat_id', '')
            message = log_data.get('message', '')[:500]  # 메시지는 500자로 제한
            message_type = log_data.get('message_type', 'text')
            status = log_data.get('status', '')
            error_message = log_data.get('error_message', '')

            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO message_logs
                    (phone, chat_id, message, message_type, status, error_message)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    phone,
                    chat_id,
                    message,
                    message_type,
                    status,
                    error_message
                ))
                await db.commit()
                return True
        except Exception as e:
            print(f"메시지 로그 오류: {e}")
            return False

    async def get_message_logs(self, phone: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """메시지 로그 조회"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            if phone:
                query = "SELECT * FROM message_logs WHERE phone = ? ORDER BY sent_at DESC LIMIT ?"
                params = (phone, limit)
            else:
                query = "SELECT * FROM message_logs ORDER BY sent_at DESC LIMIT ?"
                params = (limit,)

            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows] if rows else []

    # ==================== 세션 백업 ====================

    async def log_session_backup(self, phone: str, backup_path: str) -> bool:
        """세션 백업 로그 추가"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO session_backups (phone, backup_path)
                    VALUES (?, ?)
                """, (phone, backup_path))
                await db.commit()
                return True
        except Exception as e:
            print(f"세션 백업 로그 오류: {e}")
            return False

    async def get_last_backup_date(self, phone: str) -> Optional[datetime]:
        """마지막 백업 날짜 조회"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT created_at FROM session_backups
                WHERE phone = ? ORDER BY created_at DESC LIMIT 1
            """, (phone,)) as cursor:
                row = await cursor.fetchone()
                if row and row[0]:
                    try:
                        return datetime.fromisoformat(str(row[0]))
                    except (ValueError, TypeError):
                        return None
                return None

    async def cleanup_old_logs(self, days: int = 30):
        """오래된 로그 정리"""
        cutoff_date = datetime.now() - timedelta(days=days)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                DELETE FROM message_logs
                WHERE sent_at < ?
            """, (cutoff_date,))

            await db.execute("""
                DELETE FROM session_backups
                WHERE created_at < ?
            """, (cutoff_date,))

            await db.commit()

    # ==================== 설정 관리 ====================

    async def get_setting(self, key: str) -> Optional[Any]:
        """설정 값 조회"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT value, value_type FROM settings WHERE key = ?
            """, (key,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    value, value_type = row
                    if value_type == 'json':
                        return json.loads(value)
                    elif value_type == 'boolean':
                        return value.lower() == 'true'
                    elif value_type == 'number':
                        return float(value)
                    return value
                return None

    async def set_setting(self, key: str, value: Any, value_type: str = 'string') -> bool:
        """설정 값 저장"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                if value_type == 'json':
                    value = json.dumps(value)
                elif value_type == 'boolean':
                    value = str(value).lower()
                elif value_type == 'number':
                    value = str(value)

                await db.execute("""
                    INSERT OR REPLACE INTO settings (key, value, value_type, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """, (key, value, value_type))
                await db.commit()
                return True
        except Exception as e:
            print(f"설정 저장 오류: {e}")
            return False

    # ==================== 통계 ====================

    async def get_statistics(self) -> Dict[str, Any]:
        """통계 정보 조회"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # 계정 통계
                async with db.execute("SELECT COUNT(*) FROM accounts") as cursor:
                    total_accounts = (await cursor.fetchone())[0]

                status_counts = {}
                async with db.execute("""
                    SELECT status, COUNT(*) FROM accounts GROUP BY status
                """) as cursor:
                    rows = await cursor.fetchall()
                    if rows:
                        status_counts = {str(row[0]): row[1] for row in rows}

                # 오늘 메시지 통계
                today = datetime.now().date().isoformat()
                today_messages = 0
                async with db.execute("""
                    SELECT COUNT(*) FROM message_logs
                    WHERE DATE(sent_at) = ?
                """, (today,)) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        today_messages = row[0]

                today_status_counts = {}
                async with db.execute("""
                    SELECT status, COUNT(*) FROM message_logs
                    WHERE DATE(sent_at) = ? GROUP BY status
                """, (today,)) as cursor:
                    rows = await cursor.fetchall()
                    if rows:
                        today_status_counts = {str(row[0]): row[1] for row in rows}

                return {
                    'total_accounts': total_accounts,
                    'status_counts': status_counts,
                    'today_messages': today_messages,
                    'today_status_counts': today_status_counts,
                    'generated_at': datetime.now().isoformat()
                }
        except Exception as e:
            print(f"통계 정보 조회 오류: {e}")
            return {
                'total_accounts': 0,
                'status_counts': {},
                'today_messages': 0,
                'today_status_counts': {},
                'generated_at': datetime.now().isoformat(),
                'error': str(e)
            }


# 전역 데이터베이스 매니저 인스턴스
db_manager = DatabaseManager()
