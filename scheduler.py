"""
Scheduler for EDUARDO-V2 weekly trading tasks.
Runs every Monday at 8:30 AM CDT.
"""
import schedule
import time
import logging
from datetime import datetime, timedelta
import pytz
from typing import Callable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('eduardo.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# CDT timezone
CDT = pytz.timezone('America/Chicago')


class EduardoScheduler:
    """Scheduler for EDUARDO-V2 trading pipeline."""
    
    def __init__(self, task_func: Callable[[], bool]):
        """
        Initialize scheduler.
        
        Args:
            task_func: The main task function to run. Should return True on success, False on failure.
        """
        self.task_func = task_func
        self.retry_scheduled = False
    
    def run_task(self) -> None:
        """Execute the main trading task with retry logic."""
        logger.info("=" * 50)
        logger.info("EDUARDO-V2 Weekly Task Starting")
        logger.info(f"Current time: {datetime.now(CDT).strftime('%Y-%m-%d %H:%M:%S %Z')}")
        logger.info("=" * 50)
        
        try:
            success = self.task_func()
            
            if success:
                logger.info("OK: Task completed successfully")
                self.retry_scheduled = False
            else:
                logger.warning("FAIL: Task failed - scheduling retry for tomorrow")
                self._schedule_retry()
                
        except Exception as e:
            logger.error(f"FAIL: Task failed with exception: {e}")
            logger.exception("Full traceback:")
            self._schedule_retry()
    
    def _schedule_retry(self) -> None:
        """Schedule a retry for the next day at 8:30 AM CDT."""
        if not self.retry_scheduled:
            self.retry_scheduled = True
            # Schedule one-time retry for tomorrow
            schedule.every().day.at("08:30").do(self._retry_once).tag('retry')
            logger.info("Retry scheduled for tomorrow at 8:30 AM CDT")
    
    def _retry_once(self) -> schedule.CancelJob:
        """Run the task once as a retry, then cancel this job."""
        logger.info("Executing scheduled retry...")
        self.retry_scheduled = False
        
        try:
            success = self.task_func()
            if success:
                logger.info("OK: Retry successful")
            else:
                logger.warning("FAIL: Retry failed - will try again next Monday")
        except Exception as e:
            logger.error(f"FAIL: Retry failed with exception: {e}")
        
        # Cancel this retry job
        return schedule.CancelJob
    
    def start(self) -> None:
        """Start the scheduler - runs every Monday at 8:30 AM CDT."""
        logger.info("=" * 50)
        logger.info("EDUARDO-V2 Scheduler Starting")
        logger.info("Schedule: Every Monday at 8:30 AM CDT")
        logger.info("=" * 50)
        
        # Schedule weekly task for Monday at 8:30 AM
        schedule.every().monday.at("08:30").do(self.run_task)
        
        logger.info("Scheduler running. Press Ctrl+C to exit.")
        
        while True:
            # Check if we need to run any scheduled tasks
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def run_now(self) -> None:
        """Run the task immediately (for testing)."""
        logger.info("Running task immediately (manual trigger)")
        self.run_task()


def calculate_next_monday_830_cdt() -> datetime:
    """Calculate the next Monday at 8:30 AM CDT."""
    now = datetime.now(CDT)
    days_until_monday = (7 - now.weekday()) % 7
    if days_until_monday == 0 and now.hour >= 9:  # Past Monday morning
        days_until_monday = 7
    
    next_monday = now + timedelta(days=days_until_monday)
    next_monday = next_monday.replace(hour=8, minute=30, second=0, microsecond=0)
    
    return next_monday


if __name__ == "__main__":
    # Test scheduler
    def dummy_task() -> bool:
        print("Running dummy task...")
        return True
    
    scheduler = EduardoScheduler(dummy_task)
    
    # Show next scheduled run
    next_run = calculate_next_monday_830_cdt()
    print(f"Next scheduled run: {next_run.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    # Run immediately for testing
    scheduler.run_now()
