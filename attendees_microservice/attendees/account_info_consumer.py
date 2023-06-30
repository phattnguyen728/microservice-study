from datetime import datetime
import json
import pika
from pika.exceptions import AMQPConnectionError
import django
import os
import sys
import time

sys.path.append("")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "attendees_bc.settings")
django.setup()

from .models import AccountVO


def update_account(ch, method, properties, body):
    content = json.loads(body)
    first_name = content["first_name"]
    last_name = content["last_name"]
    email = content["email"]
    is_active = content["is_active"]
    updated_string = content["updated"]
    updated = datetime.fromisoformat(updated_string)
    if is_active:
        AccountVO.objects.update_or_create(
            {
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "is_active": is_active,
                "updated": updated,
            }
        )
    else:
        account = AccountVO.objects.filter(email=email)
        AccountVO.objects.delete(account)

while True:
    try:
        parameters = pika.ConnectionParameters(host="rabbitmq")
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.exchange_declare(exchange='account_info', exchange_type='fanout')
        result = channel.queue_declare(queue='', exclusive=True)
        queue_name = result.method.queue
        channel.queue_bind(exchange='account_info', queue=queue_name)
        channel.basic_consume(
            queue='',
            on_message_callback=update_account,
            auto_ack=True,
        )
        print("Start consuming update account")
        channel.start_consuming()
    except AMQPConnectionError:
        print("Could not connect to RabbitMQ")
        time.sleep(2.0)
