import datetime
import json
import logging
import os
from http import HTTPStatus
from logging.handlers import RotatingFileHandler

from requests import Session
from requests.auth import HTTPBasicAuth
from zeep import Transport, Client

from core.bitrix24.bitrix24 import ActivityB24, DealB24, SmartProcessB24, \
    ListB24
from core.models import Portals
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from pybitrix24 import Bitrix24
from settings.models import SettingsPortal
from django.conf import settings

from activities.models import Activity


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


@csrf_exempt
def b24_to_1c(request):
    """Method send request from b24 to 1C."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    if not logger.hasHandlers():
        handler = RotatingFileHandler(
            os.path.join(os.path.dirname(settings.BASE_DIR), 'logs/app.log'),
            maxBytes=5000000,
            backupCount=5
        )
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.info('*****-----Start application-----*****')

    initial_data = _get_initial_data(request)
    logger.debug('Initial data: \n{}'.format(
        json.dumps(initial_data, indent=2, ensure_ascii=False)
    ))
    portal, settings_portal = _create_portal(initial_data)
    _check_initial_data(portal, initial_data)

    try:
        deal = DealB24(portal, initial_data['deal_id'])
        deal.get_all_products()
        logger.debug('Products in deal: \n{}'.format(
            json.dumps(deal.products, indent=2, ensure_ascii=False)
        ))

        company_inn = initial_data.get('client_inn')
        company_name = initial_data.get('client_name')
        if not company_inn:
            _response_for_bp(
                portal,
                initial_data['event_token'],
                f'Ошибка: У компании в сделке не найден ИНН',
                return_values={'result': f'Error: company has not inn'},
            )
            return HttpResponse(status=HTTPStatus.OK)
        logger.info(f'Company: {company_name = }, {company_inn = }')
        # Document
        document_date = datetime.datetime.strptime(
            initial_data.get('document_date'), '%d.%m.%Y').strftime('%Y-%m-%d')
        document, airline_id, city_in_id, city_out_id = _create_document(
            portal, settings_portal, deal)
        document['DocDate'] = document_date
        # Airline
        airline = _create_airline(portal, settings_portal, airline_id)
        logger.info('Airline: \n{}'.format(json.dumps(airline, indent=2,
                                           ensure_ascii=False)))
        document['Airline'] = airline
        # Route
        route = _create_route(portal, settings_portal, city_in_id, city_out_id)
        logger.info('Route: \n{}'.format(json.dumps(route, indent=2,
                                                    ensure_ascii=False)))
        document['Routes'] = route
        # Services
        services = _create_service(deal)
        logger.info('Services: \n{}'.format(json.dumps(
            services, indent=2, ensure_ascii=False)))
        document['Services'] = services
        document['Client'] = {
            'INN': company_inn,
            'Name': company_name,
            'IsOrganization': 'true' if initial_data.get(
                'is_organization') == 'Y' else 'false'
        }
        logger.info('Document: \n{}'.format(json.dumps(document, indent=2,
                                            ensure_ascii=False)))

        result = _send_soap(settings_portal, document)
        logger.info('Result: \n{}'.format(json.dumps(result, indent=2,
                                                     ensure_ascii=False)))

    except RuntimeError as ex:
        _response_for_bp(
            portal,
            initial_data['event_token'],
            f'Ошибка: {ex.args[0]}',
            return_values={'result': f'Error: {ex.args[1]}'},
        )
        return HttpResponse(status=HTTPStatus.OK)
    except Exception as ex:
        _response_for_bp(
            portal,
            initial_data['event_token'],
            f'Ошибка: {ex.args[0]}',
            return_values={'result': f'Error: {ex.args[0]}'},
        )
        return HttpResponse(status=HTTPStatus.OK)

    _response_for_bp(
        portal,
        initial_data['event_token'],
        f'Успех',
        return_values={'result': f'Ok: {result}'},
    )
    return HttpResponse(status=HTTPStatus.OK)


def _create_portal(initial_data):
    """Method for create portal."""
    try:
        portal = Portals.objects.get(member_id=initial_data['member_id'])
        portal.check_auth()
        settings_portal = SettingsPortal.objects.get(portal=portal)
        return portal, settings_portal
    except ObjectDoesNotExist:
        return HttpResponse(status=HTTPStatus.BAD_REQUEST)


def _get_initial_data(request):
    """Method for get initial data from Post request."""
    if request.method != 'POST':
        return HttpResponse(status=HTTPStatus.BAD_REQUEST)
    return {
        'member_id': request.POST.get('auth[member_id]'),
        'event_token': request.POST.get('event_token'),
        'document_date': request.POST.get('properties[document_date]'),
        'deal_id': request.POST.get('properties[deal_id]') or 0,
        'is_organization': request.POST.get('properties[is_organization]'),
        'client_inn': request.POST.get('properties[client_inn]'),
        'client_name': request.POST.get('properties[client_name]'),
    }


def _check_initial_data(portal, initial_data):
    """Method for check initial data."""
    try:
        initial_data['deal_id'] = int(initial_data['deal_id'])
    except Exception as ex:
        _response_for_bp(
            portal,
            initial_data['event_token'],
            'Ошибка. Проверьте входные данные.',
            return_values={'result': f'Error: {ex.args[0]}'},
        )
        return HttpResponse(status=HTTPStatus.OK)


def _create_document(portal, settings_portal, deal):
    """Method for building document."""
    cargo_smart = SmartProcessB24(portal, settings_portal.cargo_smart_id)
    cargo_smart_elements = cargo_smart.get_elements_for_entity(deal.id)
    cargo_smart_element = cargo_smart_elements[0]
    number_awb = cargo_smart_element.get(
        settings_portal.number_awb_code) or None
    weight_fact = cargo_smart_element.get(
        settings_portal.weight_fact_code) or None
    weight_pay = cargo_smart_element.get(
        settings_portal.weight_pay_code) or None
    count_position = cargo_smart_element.get(
        settings_portal.count_position_code) or None
    airline_id = cargo_smart_element.get(
        settings_portal.airline_code) or None
    city_in_id = cargo_smart_element.get(
        settings_portal.route_in_code) or None
    city_out_id = cargo_smart_element.get(
        settings_portal.route_out_code) or None
    document_number = deal.properties.get(
        settings_portal.document_number_in_1c_code) or None

    return {
               'DocNumber': document_number,
               'NumberAWB': number_awb,
               'WeightPaid': weight_pay,
               'WeightFact': weight_fact,
               'Positions': count_position,
               'Tax': '1',
               'CompanyINN': settings_portal.my_company_inn,
           }, airline_id, city_in_id, city_out_id


def _create_route(portal, settings_portal, city_in_id, city_out_id):
    """Method for building router."""
    route = []
    city_list = ListB24(portal, settings_portal.city_list_id)
    for city_id in [city_in_id, city_out_id]:
        if city_id:
            city = city_list.get_element_by_id(city_id)[0]
            city_name = city.get(settings_portal.city_name_code)
            city_code = list(city.get(
                settings_portal.city_code_code).values())[0]
            city_country = list(city.get(
                settings_portal.city_country_code).values())[0]
        else:
            city_name = None
            city_code = None
            city_country = None
        route.append({
            'CityCode': city_code, 'CityName': city_name,
            'CountryCode': city_country
        })

    return route


def _create_airline(portal, settings_portal, airline_id):
    """Method for building airline."""
    if airline_id:
        airline_list = ListB24(portal, settings_portal.airline_list_id)
        airline = airline_list.get_element_by_id(airline_id)[0]
        airline_name = list(airline.get(
            settings_portal.airline_name_code).values())[0]
        airline_code = list(airline.get(
            settings_portal.airline_code_code).values())[0]
    else:
        airline_name = None
        airline_code = None

    return {'Code': airline_code, 'Name': airline_name}


def _create_service(deal):
    """Method for building services."""
    services = []
    for product in deal.products:
        services.append({
            'Name': product.get('PRODUCT_NAME'),
            'Count': product.get('QUANTITY'),
            'Price': product.get('PRICE'),
            'Unit': product.get('MEASURE_NAME'),
            'TaxRate': f'{product.get("TAX_RATE")}%',
        })

    return services


def _send_soap(settings_portal, document):
    """Method for send request to 1C with soap client."""
    user = settings_portal.user_soap
    passwd = settings_portal.passwd_soap
    server = settings_portal.address_soap

    session = Session()
    session.auth = HTTPBasicAuth(user, passwd)
    soap = Client(server, transport=Transport(session=session))

    # factory = soap.type_factory('ns0')
    # client = factory.Client(INN="5902202276", Name="Тестовая организация")

    result = soap.service.POST(Document=document)
    session.close()

    return json.loads(result)


def _response_for_bp(portal, event_token, log_message, return_values=None):
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
