from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
import pika
from common.json import ModelEncoder
from events.api_views import ConferenceListEncoder
from events.models import Conference
from .models import Presentation


class PresentationListEncoder(ModelEncoder):
    model = Presentation
    properties = ["title"]

    def get_extra_data(self, o):
        return {"status": o.status.name}


class PresentationDetailEncoder(ModelEncoder):
    model = Presentation
    properties = [
        "presenter_name",
        "company_name",
        "presenter_email",
        "title",
        "synopsis",
        "created",
        "conference",
    ]
    encoders = {
        "conference": ConferenceListEncoder(),
    }
    def get_extra_data(self, o):
        return {"status": o.status.name}


@require_http_methods(["GET", "POST"])
def api_list_presentations(request, conference_id):
    if request.method == "GET":
        presentations = Presentation.objects.filter(conference=conference_id)
        return JsonResponse(
            {"presentations": presentations},
            encoder=PresentationListEncoder,
        )
    else:
        content = json.loads(request.body)

        try:
            conference = Conference.objects.get(id=conference_id)
            content["conference"] = conference
        except Conference.DoesNotExist:
            return JsonResponse(
                {"message": "Invalid conference id"},
                status=400,
            )
        presentation = Presentation.create(**content)
        return JsonResponse(
            presentation,
            encoder=PresentationDetailEncoder,
            safe=False,
        )


@require_http_methods(["GET", "PUT", "DELETE"])
def api_show_presentation(request, id):
    if request.method == "GET":
        presentation = Presentation.objects.get(id=id)
        return JsonResponse(
            presentation,
            encoder=PresentationDetailEncoder,
            safe=False,
        )
    elif request.method == "DELETE":
        count, _ = Presentation.objects.filter(id=id).delete()
        return JsonResponse({"deleted": count > 0})
    else:
        content = json.loads(request.body)
        Presentation.objects.filter(id=id).update(**content)
        presentation = Presentation.objects.get(id=id)
        return JsonResponse(
            presentation,
            encoder=PresentationDetailEncoder,
            safe=False,
        )


def send_status_message(json_body, queue_name):
    parameters = pika.ConnectionParameters(host="rabbitmq")
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(queue=queue_name)
    try:
        channel.basic_publish(
                exchange="",
                routing_key=queue_name,
                body = json_body,
                mandatory=True
                )
        print('Message was published')
    except pika.exceptions.UnroutableErrror:
            print('Message was returned.')
    connection.close()

@require_http_methods(["PUT"])
def api_approve_presentation(request, id):
    presentation = Presentation.objects.get(id=id)
    presentation.approve()
    message = json.dumps({
            "presenter_name": presentation.presenter_name,
            "presenter_email": presentation.presenter_email,
            "title": presentation.title,
            })
    send_status_message(message, "presentation_approvals")
    return JsonResponse(
            presentation,
            encoder=PresentationDetailEncoder,
            safe=False,
            )

@require_http_methods(["PUT"])
def api_reject_presentation(request, id):
    presentation = Presentation.objects.get(id=id)
    presentation.reject()
    message = json.dumps({
            "presenter_name": presentation.presenter_name,
            "presenter_email": presentation.presenter_email,
            "title": presentation.title,
            })
    send_status_message(message, "presentation_rejections")
    return JsonResponse(
            presentation,
            encoder=PresentationDetailEncoder,
            safe=False,
            )
