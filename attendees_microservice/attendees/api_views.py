from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
from common.json import ModelEncoder
from .models import Attendee, ConferenceVO, AccountVO


class ConferenceVODetailEncoder(ModelEncoder):
    model = ConferenceVO
    properties = ["name", "import_href"]

class AttendeeListEncoder(ModelEncoder):
    model = Attendee
    properties = ["name"]


class AttendeeDetailEncoder(ModelEncoder):
    model = Attendee
    properties = [
        "email",
        "name",
        "company_name",
        "created",
        "conference",
    ]
    encoders = {
        "conference": ConferenceVODetailEncoder(),
    }

    def get_extra_data(self, o):
        # count = AccountVO.objects.filter(email=o.email).count()
        count = Attendee.objects.filter(email=o.email).count()
        if count > 0:
            return {
                "has_account": True,
            }
        else:
            return {
                "has_account": False,
            }
    # def get_extra_data(self, o):
        # return super().get_extra_data(o)


# @require_http_methods(["GET", "POST"])
# # def api_list_attendees(request, conference_vo_id=None):
# def api_list_attendees(request, conference_vo_id):
#     if request.method == "GET":
#         attendees = Attendee.objects.filter(conference=conference_vo_id)
#         return JsonResponse(
#             {"attendees": attendees},
#             encoder=AttendeeListEncoder,
#         )
#     else:
#         content = json.loads(request.body)
#         try:
#             conference_href = f'/api/conferences/{conference_vo_id}/'
#             # conference = ConferenceVO.objects.get(id=conference_vo_id)
#             conference = ConferenceVO.objects.get(import_href=conference_href)
#             content["conference"] = conference
#         except ConferenceVO.DoesNotExist:
#             return JsonResponse(
#                 {"message": "Invalid conference id"},
#                 status=400,
#             )

#         attendee = Attendee.objects.create(**content)
#         return JsonResponse(
#             attendee,
#             encoder=AttendeeDetailEncoder,
#             safe=False,
#         )

@require_http_methods(["GET", "POST"])
def api_list_attendees(request, conference_vo_id=None):
    if request.method == "GET":
        attendees = Attendee.objects.filter(conference=conference_vo_id)
        return JsonResponse(
            {"attendees": attendees},
            encoder=AttendeeListEncoder,
        )
    else:
        content = json.loads(request.body)
        try:
            # conference_vo_id = content["conference_vo_id"]
            conference_href = f'/api/conferences/{content["conference"]}/'
            # conference = ConferenceVO.objects.get(id=conference_vo_id)
            conference = ConferenceVO.objects.get(import_href=conference_href)
            content["conference"] = conference
        except ConferenceVO.DoesNotExist:
            return JsonResponse(
                {"message": "Invalid conference id"},
                status=400,
            )

        attendee = Attendee.objects.create(**content)
        return JsonResponse(
            attendee,
            encoder=AttendeeDetailEncoder,
            safe=False,
        )



@require_http_methods(["GET", "PUT", "DELETE"])
def api_show_attendee(request, id):
    if request.method == "GET":
        attendee = Attendee.objects.get(id=id)
        return JsonResponse(
            {"attendee": attendee},
            encoder=AttendeeDetailEncoder,
            )
    elif request.method == "DELETE":
        count, _ = Attendee.objects.filter(id=id).delete()
        return JsonResponse({"deleted": count> 0})
    else:
        content = json.loads(request.body)
        Attendee.objects.filter(id=id).update(**content)
        attendee = Attendee.objects.get(id=id)
        return JsonResponse(
            attendee,
            encoder=AttendeeDetailEncoder,
            safe=False,
        )
