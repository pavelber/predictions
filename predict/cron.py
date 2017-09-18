import datetime
import threading
import time

from django.utils.timezone import localtime, now

from predict.models import Prediction

check_before = datetime.timedelta(days=7)
check_after = datetime.timedelta(days=7)

check_every_secs = 60


def job(tasks):
    while True:
        for t in tasks:
            t()
        time.sleep(check_every_secs)


def run_tasks_hourly(tasks):
    t = threading.Thread(target=job, args=(tasks,))
    t.setDaemon(True)
    t.start()


def check_one_week_before():
    date_in_one_week = today() + check_before
    predictions = Prediction.objects.filter(date__lte=date_in_one_week).filter(before_mails_sent=False)
    for p in predictions:
        p.creator.send_before_email(p)
        p.witness.send_before_email(p)
        p.opponent.send_before_email(p)
        p.before_mails_sent = True
        p.save()


def check_exact_date():
    predictions = Prediction.objects.filter(date__gte=today()).filter(date_mail_sent=False).filter(
        prediction_occurred=None)
    for p in predictions:
        p.send_witness_email()
        p.date_mail_sent = True
        p.save()


def check_one_week_after():
    date_in_one_week = today() - check_after
    predictions = Prediction.objects.filter(date__gte=date_in_one_week).filter(after_mails_sent=False).filter(
        date_mail_sent=True).filter(
        prediction_occurred=None)
    for p in predictions:
        p.creator.send_after_reminder_email(p)
        p.witness.send_after_reminder_email(p)
        p.opponent.send_after_reminder_email(p)
        p.after_mails_sent = True
        p.save()


def today():
    return localtime(now()).date().today()
