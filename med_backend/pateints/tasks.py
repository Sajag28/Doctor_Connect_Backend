from celery import shared_task
from django.core.mail import send_mail

@shared_task
def send_email_notification(to_email, subject, message):
    send_mail(
        subject,
        message,
        "agrawalsiddhi836@gmail.com",
        [to_email],
        fail_silently=False,
    )
