"""
세션 관리자 모듈
텔레그램 세션 파일 관리를 담당합니다.
"""
from typing import Dict, Any, List, Optional, Tuple
import os
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv

from utils.logger import session_logger
from utils.helpers import session_validator, file_manager

class DatabaseManager:
    def __init__(self, db_path: str):
        """
        데이터베이스 관리자 초기화

        Args:
            db_path: 데이터베이스 파일 경로
        """
        self.db_path = db_path

    async def initialize(self) -> None:
        """데이터베이스 초기화 및 필요한 테이블 생성"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # 메시지 로그 테이블 생성
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS message_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        phone TEXT,
                        chat_id TEXT,
                        message TEXT,
                        message_type TEXT,
                        status TEXT,
                        error_message TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                await db.commit()
                logger.info("데이터베이스 초기화 완료")
        except Exception as e:
            logger.error(f"데이터베이스 초기화 오류: {e}")
            raise

    async def log_message(self, log_data: Dict[str, Any]) -> bool:
        """
        메시지 로그를 데이터베이스에 기록

        Args:
            log_data: 로그 데이터 딕셔너리
                {
                    'phone': 전화번호,
                    'chat_id': 채팅 ID,
                    'message': 메시지 내용,
                    'message_type': 메시지 유형,
                    'status': 상태,
                    'error_message': 오류 메시지
                }

        Returns:
            bool: 성공 여부
        """
        try:
            # 필요한 필드 추출 및 기본값 설정
            phone = log_data.get('phone', '')
            chat_id = log_data.get('chat_id', '')
            message = log_data.get('message', '')[:500]  # 메시지 길이 제한
            message_type = log_data.get('message_type', 'text')
            status = log_data.get('status', '')
            error_message = log_data.get('error_message', '')

            # 데이터베이스에 로그 저장
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO message_logs
                    (phone, chat_id, message, message_type, status, error_message)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (phone, chat_id, message, message_type, status, error_message))
                await db.commit()
                logger.debug(f"메시지 로그 저장 완료: {chat_id}")
                return True
        except Exception as e:
            logger.error(f"메시지 로그 저장 오류: {e}")
            return False

    async def get_message_logs(self,
                              phone: Optional[str] = None,
                              chat_id: Optional[str] = None,
                              limit: int = 100) -> List[Dict[str, Any]]:
        """
        메시지 로그 조회

        Args:
            phone: 전화번호 필터 (선택)
            chat_id: 채팅 ID 필터 (선택)
            limit: 반환할 최대 로그 수

        Returns:
            List[Dict]: 메시지 로그 목록
        """
        try:
            query = "SELECT * FROM message_logs"
            params = []
            conditions = []

            # 필터 조건 추가
            if phone:
                conditions.append("phone = ?")
                params.append(phone)
            if chat_id:
                conditions.append("chat_id = ?")
                params.append(chat_id)

            # 조건이 있는 경우 WHERE 절 추가
            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            # 정렬 및 제한
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            # 쿼리 실행
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(query, params)
                rows = await cursor.fetchall()

                # 결과를 딕셔너리 목록으로 변환
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"메시지 로그 조회 오류: {e}")
            return []
