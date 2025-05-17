#!/usr/bin/env python3
"""
세션 연동 프로그램
텔레그램 세션 파일 생성 및 연동을 위한 명령줄 인터페이스
"""

import sys
import asyncio
import argparse
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

# 프로젝트 루트 경로를 파이썬 경로에 추가
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import session_logger
from core.session_manager import session_manager
from core.account_manager import account_manager, AccountStatus
from database.db_manager import db_manager
from utils.helpers import phone_validator, file_manager, session_validator


async def connect_session(phone: str) -> bool:
    """세션 연결 시도"""
    session_logger.info(f"세션 연결 시작: {phone}")

    # 세션 파일 검증
    if not session_manager.validate_session_file(phone):
        session_logger.error(f"유효하지 않은 세션 파일: {phone}")
        return False

    # 계정 연결 시도
    success, error = await account_manager.connect_account(phone)
    if not success:
        session_logger.error(f"세션 연결 실패: {phone}, {error}")
        return False

    # 계정 정보 업데이트
    account_info = await account_manager.get_account_info(phone)
    if not account_info:
        session_logger.error(f"계정 정보 조회 실패: {phone}")
        await account_manager.disconnect_account(phone)
        return False

    session_logger.info(f"세션 연결 성공: {phone}, {account_info.get('first_name')} {account_info.get('last_name')}")
    return True


async def connect_all_sessions() -> int:
    """모든 세션 연결"""
    session_logger.info("모든 세션 연결 시작")

    # 세션 파일 목록 가져오기
    sessions = session_manager.get_session_files()
    if not sessions:
        session_logger.warning("연결할 세션 파일이 없습니다.")
        return 0

    session_logger.info(f"세션 파일 {len(sessions)}개 발견")

    # 세션 연결 (병렬 처리)
    success_count, results = await account_manager.connect_multiple(sessions)

    # 결과 출력
    session_logger.info(f"세션 연결 완료: {success_count}/{len(sessions)} 성공")

    return success_count


async def import_session_file(src_path: str, phone: Optional[str] = None) -> bool:
    """세션 파일 가져오기"""
    src_path = Path(src_path)

    # 파일 존재 확인
    if not os.path.exists(src_path):
        session_logger.error(f"파일을 찾을 수 없음: {src_path}")
        return False

    # 전화번호 추출 또는 사용
    if phone is None:
        phone = session_validator.get_session_phone_from_filename(src_path)
        if not phone:
            session_logger.error(f"파일명에서 전화번호를 추출할 수 없음: {src_path}")
            return False
    else:
        # 전화번호 형식 검증
        normalized_phone = phone_validator.normalize_phone(phone)
        if not normalized_phone:
            session_logger.error(f"잘못된 전화번호 형식: {phone}")
            return False
        phone = normalized_phone

    # 세션 디렉토리 확인
    sessions_dir = Path("sessions")
    if not sessions_dir.exists():
        sessions_dir.mkdir(parents=True)

    # 대상 경로
    dst_path = sessions_dir / f"{phone}.session"

    # 파일 복사
    if file_manager.copy_session_file(src_path, dst_path):
        session_logger.info(f"세션 파일 가져오기 성공: {phone}")

        # DB에 계정 등록
        await db_manager.add_account({
            "phone": phone,
            "status": AccountStatus.ACTIVE.value,
            "imported_at": str(datetime.now())
        })

        return True

    return False


async def setup_api_credentials() -> bool:
    """API 자격 증명 설정"""
    print("\n=== Telegram API 자격 증명 설정 ===")
    print("텔레그램 API를 사용하기 위한 API ID와 API Hash를 입력하세요.")
    print("텔레그램 API 자격 증명이 없으신가요? https://my.telegram.org 에서 발급받으세요.\n")

    api_id = input("API ID: ")
    if not api_id.strip():
        print("API ID는 필수입니다.")
        return False

    api_hash = input("API Hash: ")
    if not api_hash.strip():
        print("API Hash는 필수입니다.")
        return False

    # API 자격 증명 저장
    if session_manager.save_config(api_id, api_hash):
        print("API 자격 증명이 성공적으로 저장되었습니다.")
        return True
    else:
        print("API 자격 증명 저장 실패!")
        return False


async def show_status() -> None:
    """계정 상태 표시"""
    # 상태 새로고침
    status = await account_manager.refresh_account_status()

    # 상태 통계
    stats = status.get("status_counts", {})

    print("\n=== 계정 상태 ===")
    print(f"총 계정 수: {stats.get('total', 0)}")
    print(f"연결됨: {stats.get('connected', 0)}")
    print(f"활성: {stats.get('active', 0)}")
    print(f"비활성: {stats.get('inactive', 0)}")
    print(f"오류: {stats.get('error', 0)}")
      # 연결된 계정 목록
    connected = status.get("connected_accounts", [])
    if connected:
        print("\n연결된 계정:")
        for phone in connected:
            info = await account_manager.get_account_info(phone)
            if info is None:
                print(f"  - {phone}: 정보 없음")
                continue

            name = f"{info.get('first_name', '')} {info.get('last_name', '')}"
            username = f"@{info.get('username')}" if info.get('username') else "없음"
            print(f"  - {phone}: {name.strip()} (유저명: {username})")


async def main() -> None:
    """메인 함수"""
    # 인자 파싱
    parser = argparse.ArgumentParser(description="텔레그램 세션 연동 프로그램")

    # 커맨드 그룹
    subparsers = parser.add_subparsers(dest="command", help="명령어")

    # 연결 명령어
    connect_parser = subparsers.add_parser("connect", help="세션 연결")
    connect_parser.add_argument("-p", "--phone", help="전화번호")
    connect_parser.add_argument("-a", "--all", action="store_true", help="모든 세션 연결")

    # 가져오기 명령어
    import_parser = subparsers.add_parser("import", help="세션 파일 가져오기")
    import_parser.add_argument("file", help="세션 파일 경로")
    import_parser.add_argument("-p", "--phone", help="전화번호 (선택사항)")

    # 설정 명령어
    setup_parser = subparsers.add_parser("setup", help="API 자격 증명 설정")

    # 상태 명령어
    status_parser = subparsers.add_parser("status", help="계정 상태 표시")

    # 종료 명령어
    disconnect_parser = subparsers.add_parser("disconnect", help="연결 종료")
    disconnect_parser.add_argument("-p", "--phone", help="전화번호")
    disconnect_parser.add_argument("-a", "--all", action="store_true", help="모든 연결 종료")

    args = parser.parse_args()

    # DB 초기화
    await db_manager.initialize()

    # 명령어 처리
    if args.command == "connect":
        if args.all:
            await connect_all_sessions()
        elif args.phone:
            await connect_session(args.phone)
        else:
            print("오류: 전화번호를 지정하거나 --all 옵션을 사용하세요.")

    elif args.command == "import":
        await import_session_file(args.file, args.phone)

    elif args.command == "setup":
        await setup_api_credentials()

    elif args.command == "status":
        await show_status()

    elif args.command == "disconnect":
        if args.all:
            count = await account_manager.disconnect_all()
            print(f"{count}개 계정 연결이 종료되었습니다.")
        elif args.phone:
            success = await account_manager.disconnect_account(args.phone)
            if success:
                print(f"{args.phone} 계정 연결이 종료되었습니다.")
            else:
                print(f"{args.phone} 계정 연결 종료 실패!")
        else:
            print("오류: 전화번호를 지정하거나 --all 옵션을 사용하세요.")

    else:
        # 명령어가 없으면 도움말 표시
        parser.print_help()

    # 프로그램 종료 전 연결 정리
    await account_manager.disconnect_all()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n프로그램 종료...")
    except Exception as e:
        print(f"오류 발생: {e}")
        sys.exit(1)
