import json
import pika
import django
import os
import sys
from pika.exceptions import AMQPConnectionError
import time
from django.core.mail import send_mail


sys.path.append("")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "presentation_mailer.settings")
django.setup()


def process_rejection(ch, method, properties, body):
    print(" [x] received %r" % body)
    presentation = json.loads(body)
    send_mail(
        'Your presentation has been rejected.',
        f"{presentation['presenter_name']}, we're saddened to inform you that your presentation {presentation['title']} has not been accepted",
        'admin@conference.go',
        [presentation['presenter_email']],
        fail_silently=False,
    )
    print("sent rejection notice")


def process_approval(ch, method, properties, body):
    print(" [x] received %r" % body)
    presentation = json.loads(body)
    send_mail(
        'Your presentation has been accepted',
        f"{presentation['presenter_name']}, we're happy to tell you that your presentation {presentation['title']} has been accepted",
        'admin@conference.go',
        [presentation['presenter_email']],
        fail_silently=False,
    )
    print("sent acceptance notice")

while True:
    try:
        parameters = pika.ConnectionParameters(host='rabbitmq')
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.queue_declare(queue='presentation_approvals')
        channel.queue_declare(queue='presentation_rejections')
        channel.basic_consume(
            queue='presentation_rejections',
            on_message_callback=process_rejection,
            auto_ack=True,
        )
        channel.basic_consume(
            queue='presentation_approvals',
            on_message_callback=process_approval,
            auto_ack=True,
        )
        channel.start_consuming()
    except AMQPConnectionError:
        print("Could not connect to RabbitMQ")
        time.sleep(2.0)
