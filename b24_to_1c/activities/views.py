from core.bitrix24.bitrix24 import ActivityB24
from core.models import Portals
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from pybitrix24 import Bitrix24
from settings.models import SettingsPortal

from .messages import MESSAGES_FOR_BP, MESSAGES_FOR_LOG
from .models import Activity


@csrf_exempt
def install(request):
    """View for install application in portal."""
    member_id = request.POST.get('member_id')
    activity_code = request.POST.get('code')

    portal: Portals = get_object_or_404(Portals, member_id=member_id)
    portal.check_auth()

    activity = get_object_or_404(Activity, code=activity_code)
    try:
        activity_b24 = ActivityB24(portal, obj_id=None)
        result = activity_b24.install(activity.build_params())
    except RuntimeError as ex:
        return JsonResponse({
            'result': 'False',
            'error_name': ex.args[0],
            'error_description': ex.args[1]})
    return JsonResponse({'result': result})


@csrf_exempt
def uninstall(request):
    """View for uninstall application in portal."""
    member_id = request.POST.get('member_id')
    activity_code = request.POST.get('code')

    portal: Portals = get_object_or_404(Portals, member_id=member_id)
    portal.check_auth()

    try:
        activity_b24 = ActivityB24(portal, obj_id=None, code=activity_code)
        result = activity_b24.uninstall()
    except RuntimeError as ex:
        return JsonResponse({
            'result': 'False',
            'error_name': ex.args[0],
            'error_description': ex.args[1]})
    return JsonResponse({'result': result})


def response_for_bp(portal, event_token, log_message, return_values=None):
    """Method for send parameters in bp."""
    bx24 = Bitrix24(portal.name)
    bx24._access_token = portal.auth_id
    method_rest = 'bizproc.event.send'
    params = {
        'event_token': event_token,
        'log_message': log_message,
        'return_values': return_values,
    }
    bx24.call(method_rest, params)


# def start_app(request, logger) -> dict[str, any] or HttpResponse:
#     """Start application."""
#     logger.info(MESSAGES_FOR_LOG['start_app'])
#     logger.info('{} {}'.format(MESSAGES_FOR_LOG['start_block'],
#                                'Начальные данные'))
#     if request.method != 'POST':
#         logger.error(MESSAGES_FOR_LOG['request_not_post'])
#         logger.info(MESSAGES_FOR_LOG['stop_app'])
#         return HttpResponse(status=200)
#     return {
#         'member_id': request.POST.get('auth[member_id]'),
#         'event_token': request.POST.get('event_token'),
#         'document_type': request.POST.get('document_type[2]'),
#         'obj_id': request.POST.get('properties[obj_id]') or 0,
#         'company_id': request.POST.get('properties[company_id]') or 0
#     }


# def create_portal(initial_data: dict[str, any],
#                   logger) -> tuple[Portals, SettingsPortal] or HttpResponse:
#     """Method for create portal."""
#     try:
#         portal: Portals = Portals.objects.get(
#             member_id=initial_data['member_id'])
#         portal.check_auth()
#         settings_portal = SettingsPortal.objects.get(portal=portal)
#         return portal, settings_portal
#     except ObjectDoesNotExist:
#         logger.error(MESSAGES_FOR_LOG['portal_not_found'].format(
#             initial_data['member_id']))
#         logger.info(MESSAGES_FOR_LOG['stop_app'])
#         return HttpResponse(status=200)


# def check_initial_data(portal: Portals, initial_data: dict[str, any],
#                        logger) -> tuple[int, int] or HttpResponse:
#     """Method for check initial data."""
#     try:
#         obj_id = int(initial_data['obj_id'])
#         company_id = int(initial_data['company_id'])
#         return obj_id, company_id
#     except Exception as ex:
#         logger.error(MESSAGES_FOR_LOG['error_start_data'].format(
#             initial_data['obj_id'], initial_data['company_id']
#         ))
#         logger.info(MESSAGES_FOR_LOG['stop_app'])
#         response_for_bp(
#             portal,
#             initial_data['event_token'],
#             '{} {}'.format(MESSAGES_FOR_BP['main_error'], ex.args[0]),
#         )
#         return HttpResponse(status=200)
