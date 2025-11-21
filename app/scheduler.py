"""
Background scheduler for periodic tasks.
This runs within the FastAPI application.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging
from app.tasks.payment_tasks import expire_old_payments, retry_failed_webhooks

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def start_scheduler():
    """Start the background scheduler for periodic tasks."""
    
    # Task 1: Expire old payments every 5 minutes
    scheduler.add_job(
        func=expire_old_payments,
        trigger=IntervalTrigger(minutes=5),
        id='expire_old_payments',
        name='Expire old pending payments',
        replace_existing=True
    )
    logger.info("Scheduled task: Expire old payments (every 5 minutes)")
    
    # Task 2: Retry failed webhooks every 10 minutes
    scheduler.add_job(
        func=retry_failed_webhooks,
        trigger=IntervalTrigger(minutes=10),
        id='retry_failed_webhooks',
        name='Retry failed webhook deliveries',
        replace_existing=True
    )
    logger.info("Scheduled task: Retry failed webhooks (every 10 minutes)")
    
    scheduler.start()
    logger.info("Background scheduler started")


def stop_scheduler():
    """Stop the background scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Background scheduler stopped")
