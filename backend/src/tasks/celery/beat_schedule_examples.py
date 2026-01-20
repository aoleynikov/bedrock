"""
Examples of Celery Beat schedule patterns using crontab.

This file is for reference only - actual schedules are defined in celery_app.py
"""

from celery.schedules import crontab

# Examples of different cron patterns:

# Every minute
crontab()

# Every hour at minute 0
crontab(minute=0, hour='*')

# Every 6 hours (current setup)
crontab(hour='*/6', minute=0)

# Every day at midnight (00:00)
crontab(minute=0, hour=0)

# Every day at 2:30 AM
crontab(hour=2, minute=30)

# Every Monday at 7:30 AM
crontab(hour=7, minute=30, day_of_week=1)

# Every 15 minutes
crontab(minute='*/15')

# Every weekday (Monday-Friday) at 9:00 AM
crontab(hour=9, minute=0, day_of_week='1-5')

# First day of every month at midnight
crontab(minute=0, hour=0, day_of_month=1)

# Every 3 hours
crontab(hour='*/3', minute=0)

# Every 30 minutes
crontab(minute='*/30')

# Specific times: 8:00, 12:00, 18:00 daily
crontab(hour='8,12,18', minute=0)
