"""
PathcraftAI Patch Monitor - Cron Scheduler
Runs automated patch monitoring on schedule

Usage:
    python patch_monitor_cron.py

Environment Variables:
    DISCORD_WEBHOOK_PATCHES: Discord webhook URL for patch notifications
    PATCH_MONITOR_HOURS: Hours to look back (default: 6)
"""

import os
import sys
import time
import logging
from datetime import datetime
from patch_monitor import PatchMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('patch_monitor_cron.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def run_patch_monitor():
    """Run single patch monitoring cycle"""
    logger.info("="*60)
    logger.info("PathcraftAI Patch Monitor - Cron Job")
    logger.info(f"Started at: {datetime.now().isoformat()}")
    logger.info("="*60)

    try:
        # Get configuration from environment
        discord_webhook = os.environ.get('DISCORD_WEBHOOK_PATCHES')
        hours_to_check = int(os.environ.get('PATCH_MONITOR_HOURS', '6'))

        # Initialize monitor
        monitor = PatchMonitor()

        # Monitor all sources
        news = monitor.monitor_all_sources(hours_ago=hours_to_check)

        logger.info(f"Found {len(news)} new patch announcements")

        # Send Discord notification if webhook is configured
        if discord_webhook and news:
            logger.info("Sending Discord notifications...")
            monitor.send_discord_notification(discord_webhook, news)
            logger.info("✅ Discord notifications sent")
        elif not discord_webhook:
            logger.warning("⚠️ DISCORD_WEBHOOK_PATCHES not configured")
        else:
            logger.info("ℹ️ No new patches found")

        # Check if auto-update should trigger
        for item in news:
            if monitor.should_update_pathcraft(item['analysis']):
                logger.info("⚡ AUTO-UPDATE TRIGGERED")
                # TODO: Trigger PathcraftAI rebuild
                # For now, just log it

        logger.info("="*60)
        logger.info("Patch monitoring cycle completed")
        logger.info("="*60)

        return True

    except Exception as e:
        logger.error(f"❌ Error during patch monitoring: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point"""
    success = run_patch_monitor()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
