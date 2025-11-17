#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
자동 업데이트 스케줄러
- 매일 자동으로 POE.Ninja 데이터 갱신
- 백그라운드 서비스로 실행
"""

import sys
import time
import schedule
import logging
from datetime import datetime
from pathlib import Path
import subprocess

# UTF-8 설정
if sys.platform == 'win32':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_updater.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class AutoUpdater:
    """자동 업데이트 스케줄러"""

    def __init__(self, league: str = "Standard"):
        self.league = league
        self.script_dir = Path(__file__).parent
        self.python_exe = self.script_dir / ".venv" / "Scripts" / "python.exe"
        self.fetcher_script = self.script_dir / "poe_ninja_fetcher.py"

        # Python 경로 확인
        if not self.python_exe.exists():
            self.python_exe = Path(sys.executable)
            logger.warning(f"venv Python not found, using system Python: {self.python_exe}")

    def update_poe_ninja_data(self):
        """POE.Ninja 데이터 갱신"""
        logger.info("=" * 80)
        logger.info("Starting POE.Ninja data update...")
        logger.info(f"League: {self.league}")
        logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 80)

        try:
            # poe_ninja_fetcher.py 실행
            cmd = [
                str(self.python_exe),
                str(self.fetcher_script),
                "--collect",
                "--league", self.league
            ]

            logger.info(f"Executing: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                cwd=str(self.script_dir),
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=600  # 10분 타임아웃
            )

            if result.returncode == 0:
                logger.info("✓ POE.Ninja data updated successfully")
                logger.info(f"Output:\n{result.stdout}")
            else:
                logger.error(f"✗ Update failed with code {result.returncode}")
                logger.error(f"Error:\n{result.stderr}")

        except subprocess.TimeoutExpired:
            logger.error("✗ Update timed out after 10 minutes")
        except Exception as e:
            logger.error(f"✗ Update failed: {e}")

        logger.info("=" * 80)
        logger.info("Update job completed")
        logger.info("=" * 80)
        logger.info("")

    def update_youtube_builds(self):
        """YouTube 빌드 데이터 갱신"""
        logger.info("=" * 80)
        logger.info("Starting YouTube builds update...")
        logger.info("=" * 80)

        try:
            # popular_build_collector.py 실행
            collector_script = self.script_dir / "popular_build_collector.py"

            if not collector_script.exists():
                logger.warning("popular_build_collector.py not found, skipping YouTube update")
                return

            cmd = [
                str(self.python_exe),
                str(collector_script),
                "--league", self.league,
                "--version", "3.27"
            ]

            logger.info(f"Executing: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                cwd=str(self.script_dir),
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=300  # 5분 타임아웃
            )

            if result.returncode == 0:
                logger.info("✓ YouTube builds updated successfully")
            else:
                logger.error(f"✗ YouTube update failed with code {result.returncode}")

        except Exception as e:
            logger.error(f"✗ YouTube update failed: {e}")

        logger.info("=" * 80)
        logger.info("")

    def run_all_updates(self):
        """모든 업데이트 실행"""
        logger.info("")
        logger.info("🔄 STARTING SCHEDULED UPDATE")
        logger.info("")

        # POE.Ninja 데이터 갱신
        self.update_poe_ninja_data()

        # YouTube 빌드 갱신
        self.update_youtube_builds()

        logger.info("✓ All updates completed")
        logger.info("")

    def start_scheduler(self, update_time: str = "03:00"):
        """스케줄러 시작

        Args:
            update_time: 업데이트 시각 (HH:MM 형식)
        """
        logger.info("=" * 80)
        logger.info("PathcraftAI Auto-Updater")
        logger.info("=" * 80)
        logger.info(f"League: {self.league}")
        logger.info(f"Scheduled update time: {update_time} (daily)")
        logger.info(f"Script directory: {self.script_dir}")
        logger.info(f"Python executable: {self.python_exe}")
        logger.info("=" * 80)
        logger.info("")

        # 스케줄 등록
        schedule.every().day.at(update_time).do(self.run_all_updates)

        logger.info(f"✓ Scheduler started. Waiting for {update_time}...")
        logger.info("Press Ctrl+C to stop")
        logger.info("")

        # 즉시 한 번 실행 (옵션)
        if "--now" in sys.argv:
            logger.info("Running immediate update (--now flag)")
            self.run_all_updates()

        # 무한 루프로 스케줄 실행
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 1분마다 체크

        except KeyboardInterrupt:
            logger.info("")
            logger.info("Scheduler stopped by user")
            logger.info("Goodbye!")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='PathcraftAI 자동 업데이트 스케줄러')
    parser.add_argument('--league', type=str, default='Standard', help='League name')
    parser.add_argument('--time', type=str, default='03:00', help='Update time (HH:MM)')
    parser.add_argument('--now', action='store_true', help='Run update immediately')

    args = parser.parse_args()

    updater = AutoUpdater(league=args.league)
    updater.start_scheduler(update_time=args.time)


if __name__ == '__main__':
    main()
