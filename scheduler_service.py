from apscheduler.schedulers.background import BackgroundScheduler
import logging

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self, database, notification_service):
        """Initialize scheduler"""
        self.db = database
        self.notification_service = notification_service
        self.scheduler = BackgroundScheduler()
    
    def start(self):
        """Start scheduled tasks"""
        # Check alerts every hour
        self.scheduler.add_job(
            func=self.check_all_notifications,
            trigger='interval',
            hours=1,
            id='check_notifications',
            name='Check notifications',
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