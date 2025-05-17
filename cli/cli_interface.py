# cli/cli_interface.py
"""
TMC 텔레쏜 CLI 인터페이스
명령줄 기반 인터페이스
"""

import asyncio
from utils.logger import get_logger

cli_logger = get_logger("CLI")

def start_cli():
    """CLI 시작 함수"""
    cli_logger.info("CLI 모드 시작")
    # 임시 메시지 표시
    print("CLI 모드 개발 진행 중입니다. 추후 업데이트에서 제공됩니다.")

    # asyncio.run(main_cli())


async def main_cli():
    """CLI 메인 함수"""
    # 추후 구현
    pass


class CLIInterface:
    """CLI 인터페이스 클래스"""

    def __init__(self):
        self.running = True

    async def start(self):
        """CLI 인터페이스 시작"""
        # 추후 구현
        pass
