# tasks.py
import schedule
import time
from django.contrib.auth.models import User
from django.core.mail import send_mail
from datetime import timedelta
from django.utils import timezone

def delete_unconfirmed_users():
    now = timezone.now()
    two_minutes_ago = now - timedelta(minutes=2)
    unconfirmed_users = User.objects.filter(is_active=True, email__isnull=True, date_joined__lte=two_minutes_ago)
    unconfirmed_users.delete()
    print("Utilizatori neconfirmati stersi!")

def send_newsletter():
    now = timezone.now()
    x_minutes_ago = now - timedelta(minutes=60)
    users = User.objects.filter(date_joined__lte=x_minutes_ago)

    for user in users:
        send_mail(
            'Newsletter',
            'Acesta este newsletter-ul saptamânal.',
            'from@example.com',
            [user.email],
            fail_silently=False,
        )
    print("Newsletter trimis!")

def task_10_minute():
    print("Taskul se executa la fiecare 10 minute.")

def task_daily():
    print("Taskul zilnic se executa in fiecare marti la ora 18:00.")

schedule.every(2).minutes.do(delete_unconfirmed_users)
schedule.every().monday.at("08:00").do(send_newsletter)
schedule.every(10).minutes.do(task_10_minute)
schedule.every().tuesday.at("18:00").do(task_daily)

def run_tasks():
    while True:
        schedule.run_pending()
        time.sleep(1)
