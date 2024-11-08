import datetime
import json
import logging
import os
import requests
from http import HTTPStatus
from logging.handlers import RotatingFileHandler

from activities.models import Activity
from core.bitrix24.bitrix24 import (ActivityB24, DealB24, ListB24,
                                    SmartProcessB24, ProductRowB24)
from core.models import Portals
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from pybitrix24 import Bitrix24
from requests import Session
from requests.auth import HTTPBasicAuth
from settings.models import SettingsPortal
from zeep import Client, Transport
import logging.config


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
def add_productrow(request):
    """Method from adding productrow in deal products."""
    initial_data = _get_initial_data_add_productrow(request)
    portal, settings_portal = _create_portal(initial_data)
    _check_initial_data(portal, initial_data)

    try:
        fields = {
            'ownerId': initial_data.get('deal_id'),
            'ownerType': 'D',
            'productName': initial_data.get('name'),
            'price': initial_data.get('price'),
            'quantity': initial_data.get('quantity'),
            'taxRate': '20',
            'taxIncluded': 'Y',
        }
        productrow = ProductRowB24(portal, 0)
        result = productrow.add(fields)

        _response_for_bp(
            portal,
            initial_data['event_token'],
            'Успех',
            return_values={'result': f'Success: {result}'},
        )
        return HttpResponse(status=HTTPStatus.OK)

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


@csrf_exempt
def copy_deal(request):
    """Method from copy deal with expenses and clear 1c fields."""
    fields_for_del = ['ID', 'UF_CRM_1665054060', 'UF_CRM_1665054102',
                      'UF_CRM_1665054289', 'UF_CRM_1667785528',
                      'UF_CRM_1667785549', 'UF_CRM_1667785572',
                      'UF_CRM_1665034515', 'UF_CRM_1665054125']
    field_origin_deal_code = 'UF_CRM_1674380869'
    field_type_id_value = 'SALE'
    field_stage_id_value = 'NEW'
    field_opened_value = 'Y'
    field_closed_value = 'N'
    field_is_new_value = 'Y'

    initial_data = _get_initial_data_copy_deal(request)
    portal, settings_portal = _create_portal(initial_data)
    _check_initial_data(portal, initial_data)
    return_values = {
        'result': '',
        'has_error': 'N',
        'error_desc': '',
    }

    try:
        deal = DealB24(portal, initial_data.get('deal_id'))
        for field in fields_for_del:
            if field not in deal.properties:
                continue
            del deal.properties[field]
        deal.properties['TITLE'] = f'( КОПИЯ ) {deal.properties["TITLE"]}'
        deal.properties['TYPE_ID'] = field_type_id_value
        deal.properties['STAGE_ID'] = field_stage_id_value
        deal.properties['OPENED'] = field_opened_value
        deal.properties['CLOSED'] = field_closed_value
        deal.properties['IS_NEW'] = field_is_new_value
        new_deal_id = DealB24(portal, 0).create(deal.properties)
        if initial_data['is_copy_expenses'] == 'Y':
            new_deal = DealB24(portal, new_deal_id)
            new_deal.update({
                field_origin_deal_code: initial_data.get('deal_id')
            })
        deal_products_rows = ProductRowB24(portal, 0).list(
            'D', initial_data.get('deal_id'))
        for deal_product_row in deal_products_rows.get('productRows'):
            del deal_product_row['id']
        ProductRowB24(portal, 0).set('D', new_deal_id,
                                     deal_products_rows.get('productRows'))
        return_values['result'] = f'ID созданной сделки = {new_deal_id}'
        _response_for_bp(
            portal,
            initial_data['event_token'],
            'Активити успешно завершило свои действия',
            return_values=return_values,
        )
        return HttpResponse(status=HTTPStatus.OK)
    except RuntimeError as ex:
        return_values['result'] = 'Ошибка. Просмотр в поле error_desc.'
        return_values['has_error'] = 'Y'
        return_values['error_desc'] = (f'Ошибка: {ex.args[0]}. Описание ошибки'
                                       f': {ex.args[1]}')
        _response_for_bp(
            portal,
            initial_data['event_token'],
            'Ошибка в работе активити',
            return_values=return_values,
        )
        return HttpResponse(status=HTTPStatus.OK)
    except Exception as ex:
        return_values['result'] = 'Ошибка. Просмотр в поле error_desc.'
        return_values['has_error'] = 'Y'
        return_values['error_desc'] = f'Ошибка. Описание ошибки: {ex.args[0]}'
        _response_for_bp(
            portal,
            initial_data['event_token'],
            'Ошибка в работе активити',
            return_values=return_values,
        )
        return HttpResponse(status=HTTPStatus.OK)


@csrf_exempt
def b24_to_1c(request):
    """Method send request from b24 to 1C."""
    # logging.config.dictConfig({
    #     'version': 1,
    #     'formatters': {
    #         'verbose': {
    #             'format': '%(name)s: %(message)s'
    #         }
    #     },
    #     'handlers': {
    #         'console': {
    #             'level': 'DEBUG',
    #             'class': 'logging.StreamHandler',
    #             'formatter': 'verbose',
    #         },
    #     },
    #     'loggers': {
    #         'zeep.transports': {
    #             'level': 'DEBUG',
    #             'propagate': True,
    #             'handlers': ['console'],
    #         },
    #     }
    # })
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

    logger.info('\n\n*****-----Start application-----*****')

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
        company_kpp = initial_data.get('client_kpp')
        company_name = initial_data.get('client_name')
        company_address = initial_data.get('client_address')
        if not company_inn:
            _response_for_bp(
                portal,
                initial_data['event_token'],
                'Ошибка: У компании в сделке не найден ИНН',
                return_values={'result': 'Error: company has not inn'},
            )
            return HttpResponse(status=HTTPStatus.OK)
        logger.info(f'Company: {company_name = }, {company_inn = }, '
                    f'{company_kpp = }, {company_address = }')
        # Document
        document_date = datetime.datetime.strptime(
            initial_data.get('document_date'), '%d.%m.%Y').strftime('%Y-%m-%d')
        transfer_date = datetime.datetime.strptime(
            initial_data.get('transfer_date'), '%d.%m.%Y').strftime('%Y-%m-%d')
        document, airline_id, city_in_id, city_out_id = _create_document(
            portal, settings_portal, deal)
        document['DocDate'] = document_date
        document['TransportationDate'] = transfer_date
        document['Tax'] = '1' if initial_data.get('tax') == 'Y' else '0'
        document['IsTaxIncluded'] = ('1' if initial_data.get('tax_include') ==
                                            'Y' else '0')
        document['CompanyINN'] = initial_data.get('my_company_inn')
        # Airline
        if airline_id and airline_id > 0:
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
        if company_kpp:
            document['Client']['KPP'] = company_kpp
        if company_address:
            document['Client']['Address'] = company_address
        logger.info('Document: \n{}'.format(json.dumps(document, indent=2,
                                                       ensure_ascii=False)))

        result = _send_soap(settings_portal, document)
        logger.info('Result: \n{}'.format(json.dumps(result, indent=2,
                                                     ensure_ascii=False)))

        if result.get('Status') == 'Error':
            _response_for_bp(
                portal,
                initial_data['event_token'],
                'Ошибка',
                return_values={'result': f'Error: {result.get("Description")}'}
            )
            return HttpResponse(status=HTTPStatus.OK)

        if 'DocGuid' in result:
            link_print_bill = (settings_portal.link_get_print + 'bill/'
                               + result.get('DocGuid'))
            link_print_bill_stamp = (settings_portal.link_get_print + 'bill/'
                                     + result.get('DocGuid') + '?facsimile=1')
            link_print_invoice = (settings_portal.link_get_print + 'invoice/'
                                  + result.get('DocGuid'))
            link_print_invoice_stamp = (settings_portal.link_get_print +
                                        'invoice/' + result.get('DocGuid') +
                                        '?facsimile=1')
        else:
            link_print_bill = ''
            link_print_bill_stamp = ''
            link_print_invoice = ''
            link_print_invoice_stamp = ''

        fields = {
            settings_portal.document_number_in_1c_code: result.get(
                'DocRequest'),
            settings_portal.bill_number_in_1c_code: (
                result.get('DocBill') if 'DocBill' in result else ''),
            settings_portal.sale_number_in_1c_code: (
                result.get('DocSale') if 'DocSale' in result else ''),
            settings_portal.invoice_number_in_1c_code: (
                result.get('DocInvoice') if 'DocInvoice' in result else ''),
            settings_portal.link_print_bill_code: link_print_bill,
            settings_portal.link_print_bill_stamp_code: link_print_bill_stamp,
            settings_portal.link_print_invoice_code: link_print_invoice,
            settings_portal.link_print_invoice_stamp_code: (
                link_print_invoice_stamp),
        }

        result_updated_deal = deal.update(fields)
        logger.info('Result updated deal: \n{}'.format(json.dumps(
            result_updated_deal, indent=2, ensure_ascii=False)))

        _response_for_bp(
            portal,
            initial_data['event_token'],
            'Успех',
            return_values={'result': 'Success'},
        )
        return HttpResponse(status=HTTPStatus.OK)

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
        'transfer_date': request.POST.get('properties[transfer_date]'),
        'deal_id': request.POST.get('properties[deal_id]') or 0,
        'is_organization': request.POST.get('properties[is_organization]'),
        'client_inn': request.POST.get('properties[client_inn]'),
        'client_kpp': request.POST.get('properties[client_kpp]'),
        'client_name': request.POST.get('properties[client_name]'),
        'client_address': request.POST.get('properties[client_address]'),
        'tax': request.POST.get('properties[tax]'),
        'tax_include': request.POST.get('properties[tax_include]'),
        'my_company_inn': request.POST.get('properties[my_company_inn]'),
    }


def _get_initial_data_add_productrow(request):
    """Method for get initial data from Post request for add_productrow."""
    if request.method != 'POST':
        return HttpResponse(status=HTTPStatus.BAD_REQUEST)
    return {
        'member_id': request.POST.get('auth[member_id]'),
        'event_token': request.POST.get('event_token'),
        'deal_id': request.POST.get('properties[deal_id]') or 0,
        'name': request.POST.get('properties[productrow_name]'),
        'price': request.POST.get('properties[productrow_price]'),
        'quantity': request.POST.get('properties[productrow_quantity]'),
    }


def _get_initial_data_copy_deal(request):
    """Method for get initial data from Post request for copy_deal."""
    if request.method != 'POST':
        return HttpResponse(status=HTTPStatus.BAD_REQUEST)
    return {
        'member_id': request.POST.get('auth[member_id]'),
        'event_token': request.POST.get('event_token'),
        'deal_id': request.POST.get('properties[deal_id]') or 0,
        'is_copy_expenses': request.POST.get('properties[is_copy_expenses]'),
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
    number_awb = next(iter(cargo_smart_element.get(
        settings_portal.number_awb_code)), None)
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

    return ({'DocNumber': document_number,
             'NumberAWB': number_awb,
             'WeightPaid': weight_pay,
             'WeightFact': weight_fact,
             'Positions': count_position}, airline_id, city_in_id, city_out_id)


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

    result = soap.service.POST(Document=document)
    session.close()

    return json.loads(result)


def _get_file(settings_portal, link_file):
    """Method for get file from site 1c."""
    user = settings_portal.user_soap
    passwd = settings_portal.passwd_soap

    with requests.Session() as s:
        s.auth = (user, passwd)
        upload_file = s.get(link_file)

    with open('uploads/upload.pdf', 'wb') as file:
        file.write(upload_file.content)


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
