from apscheduler.schedulers.background import BackgroundScheduler
import logging
import subprocess
from pathlib import Path

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

        # Run DB integrity check nightly at 02:00
        self.scheduler.add_job(
            func=self.run_integrity_check,
            trigger='cron',
            hour=2,
            minute=0,
            id='db_integrity_check',
            name='DB integrity check (nightly)',
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

    def run_integrity_check(self):
        """Run the db_integrity_check.py script and log results."""
        try:
            backend_dir = Path(__file__).resolve().parent
            script = backend_dir / 'db_integrity_check.py'
            if not script.exists():
                logger.warning("Integrity check script not found: %s", script)
                return

            logger.info("Running DB integrity check script: %s", script)
            res = subprocess.run(['python3', str(script)], cwd=str(backend_dir))
            if res.returncode == 0:
                logger.info("DB integrity check passed")
            else:
                logger.error("DB integrity check failed (exit=%s)", res.returncode)
                try:
                    # Send notification to admin email if configured, otherwise use SMTP username
                    admin_email = (os.environ.get('INTEGRITY_ALERT_EMAIL') 
                                   or self.notification_service.smtp_username)
                    subject = "[ALERT] DB integrity check failed"
                    body = f"The nightly DB integrity check returned non-zero exit code: {res.returncode}.\nPlease check logs for details."
                    if admin_email:
                        self.notification_service.send_email(admin_email, subject, body)
                        logger.info("Sent integrity failure notification to %s", admin_email)
                    else:
                        logger.warning("No admin email configured; cannot send integrity failure notification")
                except Exception:
                    logger.exception("Failed to send integrity failure notification")
        except Exception as e:
            logger.exception("Error running DB integrity check: %s", e)