from core.models import Portals
from pybitrix24 import Bitrix24


class ObjB24:
    """Базовый класс объекта Битрикс24."""
    GET_PROPS_REST_METHOD: str = ''

    def __init__(self, portal: Portals, id_obj: int):
        self.portal = portal
        self.bx24 = Bitrix24(portal.name)
        self.bx24._access_token = portal.auth_id
        self.id = id_obj
        if self.GET_PROPS_REST_METHOD and self.id:
            self.properties = self._get_properties()

    def _get_properties(self):
        """Получить свойства объекта."""
        return self._check_error(self.bx24.call(
            self.GET_PROPS_REST_METHOD,
            {'id': self.id}
        ))

    @staticmethod
    def _check_error(result):
        if 'error' in result:
            raise RuntimeError(result['error'], result['error_description'])
        elif 'result' in result:
            return result['result']
        else:
            raise RuntimeError('Error', 'No description error')


class DealB24(ObjB24):
    """Класс Сделка."""
    GET_PROPS_REST_METHOD: str = 'crm.deal.get'

    def __init__(self, portal: Portals, id_obj: int):
        super().__init__(portal, id_obj)
        self.products = None
        if self.id:
            self.responsible = self.properties.get('ASSIGNED_BY_ID')

    def get_all_products(self):
        """Получить все продукты сделки."""
        self.products = self._check_error(self.bx24.call(
            'crm.deal.productrows.get', {'id': self.id}
        ))

    def create(self, fields):
        """Создать сделку в Битрикс24"""
        return self._check_error(self.bx24.call(
            'crm.deal.add',
            {
                'fields': fields
            }
        ))

    def _create(self, title, stage_id, responsible_id):
        """Создать сделку в Битрикс24"""
        return self._check_error(self.bx24.call(
            'crm.deal.add',
            {
                'fields': {
                    'TITLE': title,
                    'STAGE_ID': stage_id,
                    'ASSIGNED_BY_ID': responsible_id,
                }
            }
        ))

    def set_products(self, prods_rows):
        """Добавить товар в сделку в Битрикс24"""
        return self._check_error(self.bx24.call(
            'crm.deal.productrows.set',
            {
                'id': self.id,
                'rows': prods_rows,
            }
        ))

    def update(self, fields):
        """Обновить сделку."""
        return self._check_error(self.bx24.call(
            'crm.deal.update',
            {
                'id': self.id,
                'fields': fields
            }
        ))


class QuoteB24(ObjB24):
    """Класс Предложение."""
    GET_PROPS_REST_METHOD: str = 'crm.quote.get'

    def __init__(self, portal: Portals, id_obj: int):
        super().__init__(portal, id_obj)
        self.products = None
        self.responsible = self.properties.get('ASSIGNED_BY_ID')

    def get_all_products(self):
        """Получить все продукты предложения."""
        self.products = self._check_error(self.bx24.call(
            'crm.quote.productrows.get', {'id': self.id}
        ))

    def set_products(self, prods_rows):
        """Добавить товар в сделку в Битрикс24"""
        return self._check_error(self.bx24.call(
            'crm.quote.productrows.set',
            {
                'id': self.id,
                'rows': prods_rows,
            }
        ))


class CompanyB24(ObjB24):
    """Класс Компания Битрикс24."""
    GET_PROPS_REST_METHOD: str = 'crm.company.get'

    def __init__(self, portal, id_obj: int):
        super().__init__(portal, id_obj)
        self.type = self.properties.get('COMPANY_TYPE')

    def get_inn(self):
        """Метод получения ИНН компании."""
        result = self._check_error(self.bx24.call(
            'crm.requisite.list',
            {'filter': {'ENTITY_ID': self.id}, 'select': ['RQ_INN']}
        ))
        return result[0].get('RQ_INN') if result else None


class ActivityB24(ObjB24):
    """Класс Активити Битрикс24 (действия бизнес-процессов)."""
    def __init__(self, portal, obj_id, code=None):
        super().__init__(portal, obj_id)
        self.code = code

    def get_all_installed(self):
        """Получить все установленные активити на портале."""
        return self._check_error(self.bx24.call('bizproc.activity.list'))

    def install(self, params):
        """Метод установки активити на портал."""
        return self._check_error(self.bx24.call(
            'bizproc.activity.add',
            params
        ))

    def uninstall(self):
        """Метод удаления активити на портале."""
        return self._check_error(self.bx24.call(
            'bizproc.activity.delete',
            {'code': self.code}
        ))


class ProductInCatalogB24(ObjB24):
    """Класс Товар в каталоге."""
    GET_PROPS_REST_METHOD: str = 'catalog.product.get'

    def __init__(self, portal: Portals, obj_id: int):
        super().__init__(portal, obj_id)
        if hasattr(self, 'properties'):
            self.properties = self.properties.get('product')

    def add(self):
        """Метод добавления товара в каталог."""
        method_rest = 'catalog.product.add'
        params = {'fields': self.properties}
        result = self.bx24.call(method_rest, params)
        return self._check_error(result)


class ProductRowB24(ObjB24):
    """Класс Товарной позиции."""
    GET_PROPS_REST_METHOD: str = 'crm.item.productrow.get'

    def __init__(self, portal: Portals, obj_id: int):
        super().__init__(portal, obj_id)
        if hasattr(self, 'properties'):
            self.properties = self.properties.get('productRow')
            self.id_in_catalog = self.properties.get('productId')

    def update(self, fields):
        """Метод изменения товарной позиции."""
        return self._check_error(self.bx24.call(
            'crm.item.productrow.update',
            {
                'id': self.id,
                'fields': fields
            }
        ))

    def add(self, fields):
        """Метод добавления товарной позиции."""
        return self._check_error(self.bx24.call(
            'crm.item.productrow.add',
            {
                'fields': fields
            }
        ))

    def set(self, owner_type, owner_id, product_rows):
        """Метод для привязки товарных позиций к сущности."""
        return self._check_error(self.bx24.call(
            'crm.item.productrow.set',
            {
                'ownerType': owner_type,
                'ownerId': owner_id,
                'productRows': product_rows,
            }
        ))

    def list(self, owner_type, owner_id):
        """Метод для получения товарных позиций по сущности."""
        return self._check_error(self.bx24.call(
            'crm.item.productrow.list',
            {
                'filter': {
                    '=ownerType': owner_type,
                    '=ownerId': owner_id
                }
            }
        ))

    def delete(self):
        """Метод удаления товарной позиции."""
        return self._check_error(self.bx24.call(
            'crm.item.productrow.delete',
            {
                'id': self.properties.get('id')
            }
        ))


class SmartProcessB24(ObjB24):
    """Класс Smart процесс."""
    GET_PROPS_REST_METHOD: str = 'crm.type.get'

    def get_all_elements(self):
        """Метод получения всех элементов смарт процесса."""
        return self._check_error(self.bx24.call(
            'crm.item.list',
            {
                'entityTypeId': int(self.properties.get('type').get(
                    'entityTypeId')),
            }
        )).get('items')

    def get_all_products(self, element_id):
        """Получить все товары smart процесса"""
        return self._check_error(self.bx24.call(
            'crm.item.productrow.list',
            {
                'filter': {
                    '=ownerType': "Tb1",
                    "=ownerId": element_id
                }
            }
        )).get('productRows')

    def get_elements_for_entity(self, parent_id):
        """Метод получения элементов смарт процесса привязанных к сделке."""
        return self._check_error(self.bx24.call(
            'crm.item.list',
            {
                'entityTypeId': int(self.properties.get('type').get(
                    'entityTypeId')),
                'filter': {
                    'parentId2': parent_id
                }
            }
        )).get('items')


class ListB24(ObjB24):
    """Класс Универсальных списков."""
    def get_element_by_id(self, element_id):
        """Метод получения элемента универсального списка по его id."""
        return self._check_error(self.bx24.call(
            'lists.element.get',
            {
                'IBLOCK_TYPE_ID': 'lists',
                'IBLOCK_ID': self.id,
                'ELEMENT_ID': element_id,
            }
        ))
