# -*- coding: utf-8 -*-
"""
Log Manager
모든 로그를 stderr로 리다이렉트하여 JSON 출력(stdout)과 분리
"""

import sys
from datetime import datetime
from typing import Optional

class LogManager:
    """
    로그 매니저 - stdout 오염 방지

    사용법:
        logger = LogManager()
        logger.info("This goes to stderr")
        logger.error("This also goes to stderr")
        print(json_output)  # This goes to stdout (only JSON!)
    """

    def __init__(self, prefix: str = ""):
        self.prefix = prefix

    def _log(self, level: str, message: str):
        """
        로그 출력 (항상 stderr)

        Args:
            level: 로그 레벨 (INFO, ERROR, WARN, DEBUG)
            message: 로그 메시지
        """
        timestamp = datetime.now().strftime("%H:%M:%S")

        if self.prefix:
            log_line = f"[{timestamp}] [{level}] [{self.prefix}] {message}"
        else:
            log_line = f"[{timestamp}] [{level}] {message}"

        # 항상 stderr로 출력
        print(log_line, file=sys.stderr)

    def info(self, message: str):
        """INFO 로그"""
        self._log("INFO", message)

    def error(self, message: str):
        """ERROR 로그"""
        self._log("ERROR", message)

    def warn(self, message: str):
        """WARN 로그"""
        self._log("WARN", message)

    def debug(self, message: str):
        """DEBUG 로그"""
        self._log("DEBUG", message)

    def section(self, title: str):
        """섹션 헤더 출력"""
        separator = "=" * 80
        self._log("INFO", separator)
        self._log("INFO", title)
        self._log("INFO", separator)


# 전역 로거 인스턴스
_global_logger: Optional[LogManager] = None


def get_logger(prefix: str = "") -> LogManager:
    """
    로거 인스턴스 가져오기

    Args:
        prefix: 로그 접두사 (예: "AutoRec", "POBParser")

    Returns:
        LogManager 인스턴스
    """
    global _global_logger

    if _global_logger is None:
        _global_logger = LogManager(prefix)
    elif prefix and _global_logger.prefix != prefix:
        # 새로운 prefix로 로거 생성
        return LogManager(prefix)

    return _global_logger


def setup_stdout_protection():
    """
    stdout을 보호하기 위한 초기 설정
    모든 print()를 stderr로 리다이렉트 (JSON 출력 제외)
    """
    # UTF-8 설정
    if sys.platform == 'win32':
        if sys.stdout.encoding != 'utf-8':
            sys.stdout.reconfigure(encoding='utf-8')
        if sys.stderr.encoding != 'utf-8':
            sys.stderr.reconfigure(encoding='utf-8')


if __name__ == "__main__":
    # 테스트
    logger = get_logger("TEST")

    logger.section("Log Manager Test")
    logger.info("This is an info message")
    logger.warn("This is a warning")
    logger.error("This is an error")
    logger.debug("This is debug info")

    # stdout은 JSON만 출력해야 함
    import json
    result = {"status": "success", "data": [1, 2, 3]}
    print(json.dumps(result, ensure_ascii=False))
