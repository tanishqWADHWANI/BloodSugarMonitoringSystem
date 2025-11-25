"""
Blood Sugar Monitoring System - Scheduler Service
=================================================
This module handles background task scheduling using APScheduler.

Scheduled Tasks:
- Check for abnormal readings and send notifications (hourly)
- Process threshold breach alerts
- Send reminder emails for readings
- Clean up old temporary data
- Generate periodic reports

The scheduler runs in the background and executes tasks at configured intervals
without blocking the main Flask application.

Uses: APScheduler BackgroundScheduler
"""

from apscheduler.schedulers.background import BackgroundScheduler
import logging

# Set up logging for scheduler operations
logger = logging.getLogger(__name__)

class SchedulerService:
    """
    Background task scheduler for automated notifications and maintenance.
    Runs periodic jobs independently of user requests.
    """
    
    def __init__(self, database, notification_service):
        """Initialize scheduler with database and notification service references"""
        self.db = database
        self.notification_service = notification_service
        self.scheduler = BackgroundScheduler()
    
    def start(self):
        """Start all scheduled background tasks"""
        # Check for notifications and alerts every hour
        self.scheduler.add_job(
            func=self.check_all_notifications,
            trigger='interval',
            hours=1,
            id='check_notifications',
            name='Check notifications for abnormal readings',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("Scheduler started")
    
    def check_all_notifications(self):
        """Check notifications for all patients"""
        try:
            cursor = self.db._get_cursor()
            cursor.execute("SELECT user_id FROM users WHERE role = 'patient'")
            users = cursor.fetchall()
            cursor.close()
            
            for user in users:
                try:
                    self.notification_service.check_and_send_alerts(user['user_id'])
                except Exception as e:
                    logger.error(f"Error checking user {user['user_id']}: {e}")
            
            logger.info(f"Checked {len(users)} users")
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
    
    def stop(self):
        """Stop scheduler"""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")