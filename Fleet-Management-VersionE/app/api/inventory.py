from datetime import datetime

from flask import jsonify, request
from sqlalchemy import case, func, or_, text

from app import db
from app.logger import get_api_logger
from app.models import (
    GATE_RESULT_LABELS,
    SIZE_CHOICES,
    STATUS_LABELS,
    CounterLog,
    Customer,
    Employee,
    GateLog,
    InventoryItem,
    SearchLog,
)

from . import api


logger = get_api_logger(__name__)


def error_response(message, status_code=400):
    logger.warning('API error [%d]: %s', status_code, message)
    response = jsonify({'error': message})
    response.status_code = status_code
    return response


def parse_payload():
    return request.get_json(silent=True) or request.form.to_dict()


def parse_datetime(value):
    if not value:
        return datetime.utcnow()

    for fmt in ('%Y-%m-%dT%H:%M', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    raise ValueError('timestamp format is invalid')


def parse_int(value, field_name, default=None, minimum=None):
    raw = default if value in (None, '') else value
    try:
        parsed = int(raw)
    except (TypeError, ValueError):
        raise ValueError(f'{field_name} 不合法')

    if minimum is not None and parsed < minimum:
        raise ValueError(f'{field_name} 不可小於 {minimum}')
    return parsed


def generate_serial_numbers(quantity):
    existing = InventoryItem.query.with_entities(InventoryItem.serial_number).all()
    used_indexes = set()
    for (serial_number,) in existing:
        if serial_number.startswith('SN-'):
            suffix = serial_number.replace('SN-', '', 1)
            if suffix.isdigit():
                used_indexes.add(int(suffix))

    serials = []
    candidate = 1
    while len(serials) < quantity:
        if candidate not in used_indexes:
            serials.append(f'SN-{candidate:06d}')
        candidate += 1
    return serials


def serialize_item(item):
    return item.to_dict()


def grouped_inventory_rows():
    rows = (
        db.session.query(
            InventoryItem.item_name.label('item_name'),
            InventoryItem.color.label('color'),
            InventoryItem.size.label('size'),
            func.count(InventoryItem.serial_number).label('total_count'),
            func.sum(case((InventoryItem.status_code == 0, 1), else_=0)).label('in_stock_count'),
            func.sum(case((InventoryItem.status_code == 1, 1), else_=0)).label('sold_count'),
            func.sum(case((InventoryItem.status_code == 2, 1), else_=0)).label('unauthorized_count'),
        )
        .group_by(InventoryItem.item_name, InventoryItem.color, InventoryItem.size)
        .order_by(
            InventoryItem.item_name.asc(),
            InventoryItem.color.asc(),
            InventoryItem.size.asc(),
        )
        .all()
    )

    return [
        {
            'item_name': row.item_name,
            'color': row.color,
            'size': row.size,
            'total_count': int(row.total_count or 0),
            'in_stock_count': int(row.in_stock_count or 0),
            'sold_count': int(row.sold_count or 0),
            'unauthorized_count': int(row.unauthorized_count or 0),
        }
        for row in rows
    ]


def summary_payload():
    unread_unauthorized = GateLog.query.filter_by(result='unauthorized', is_unread=True).count()
    return {
        'total_items': InventoryItem.query.count(),
        'in_stock_count': InventoryItem.query.filter_by(status_code=0).count(),
        'sold_count': InventoryItem.query.filter_by(status_code=1).count(),
        'unauthorized_count': GateLog.query.filter_by(result='unauthorized').count(),
        'unread_unauthorized_count': unread_unauthorized,
        'counter_log_count': CounterLog.query.count(),
        'gate_log_count': GateLog.query.count(),
        'grouped_inventory_count': len(grouped_inventory_rows()),
        'employee_count': Employee.query.count(),
        'customer_count': Customer.query.count(),
        'search_log_count': SearchLog.query.count(),
    }


@api.route('/summary', methods=['GET'])
def get_summary():
    return jsonify(summary_payload())


@api.route('/system/reset', methods=['POST'])
def reset_system():
    gate_count = GateLog.query.count()
    counter_count = CounterLog.query.count()
    search_count = SearchLog.query.count()
    item_count = InventoryItem.query.count()
    employee_count = Employee.query.count()
    customer_count = Customer.query.count()

    GateLog.query.delete()
    CounterLog.query.delete()
    SearchLog.query.delete()
    InventoryItem.query.delete()
    Customer.query.delete()
    Employee.query.delete()

    dialect = db.session.bind.dialect.name if db.session.bind else ''
    auto_increment_tables = (
        'counter_logs',
        'gate_logs',
        'search_logs',
        'employees',
        'customers',
    )
    if dialect == 'sqlite':
        # sqlite_sequence 只有在使用 AUTOINCREMENT 時才存在，先確認再清
        has_sequence = db.session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence'")
        ).first()
        if has_sequence:
            names = ', '.join(f"'{name}'" for name in auto_increment_tables)
            db.session.execute(text(f'DELETE FROM sqlite_sequence WHERE name IN ({names})'))
    else:
        for name in auto_increment_tables:
            db.session.execute(text(f'ALTER TABLE {name} AUTO_INCREMENT = 1'))

    db.session.commit()

    logger.warning(
        'System reset completed: removed %d items, %d counter logs, %d gate logs, '
        '%d search logs, %d employees, %d customers',
        item_count,
        counter_count,
        gate_count,
        search_count,
        employee_count,
        customer_count,
    )
    return jsonify({
        'message': '系統已清空，現在是一切從零的狀態',
        'deleted_items': item_count,
        'deleted_counter_logs': counter_count,
        'deleted_gate_logs': gate_count,
        'deleted_search_logs': search_count,
        'deleted_employees': employee_count,
        'deleted_customers': customer_count,
    })


# ---------------------------------------------------------------------------
# 員工 employees
# ---------------------------------------------------------------------------
@api.route('/employees', methods=['GET'])
def list_employees():
    employees = Employee.query.order_by(Employee.employee_id.asc()).all()
    return jsonify([employee.to_dict() for employee in employees])


@api.route('/employees', methods=['POST'])
def create_employee():
    payload = parse_payload()
    name = (payload.get('name') or '').strip()

    if not name:
        return error_response('name 為必填欄位')

    employee = Employee(name=name)
    db.session.add(employee)
    db.session.commit()
    logger.info('Created employee %s', name)
    return jsonify(employee.to_dict()), 201


# ---------------------------------------------------------------------------
# 會員 customers
# ---------------------------------------------------------------------------
@api.route('/customers', methods=['GET'])
def list_customers():
    customers = Customer.query.order_by(Customer.customer_id.asc()).all()
    return jsonify([customer.to_dict() for customer in customers])


@api.route('/customers', methods=['POST'])
def create_customer():
    payload = parse_payload()
    name = (payload.get('name') or '').strip()
    preferred_size = (payload.get('preferred_size') or '').strip()
    phone = (payload.get('phone') or '').strip() or None

    if not name:
        return error_response('name 為必填欄位')
    if not preferred_size:
        return error_response('preferred_size 為必填欄位')

    customer = Customer(name=name, preferred_size=preferred_size, phone=phone)
    db.session.add(customer)
    db.session.commit()
    logger.info('Created customer %s (size=%s)', name, preferred_size)
    return jsonify(customer.to_dict()), 201


# ---------------------------------------------------------------------------
# 商品 inventory_items
# ---------------------------------------------------------------------------
@api.route('/inventory-items', methods=['GET'])
def list_inventory_items():
    keyword = request.args.get('keyword', '').strip()

    query = InventoryItem.query
    if keyword:
        search = f'%{keyword}%'
        query = query.filter(
            or_(
                InventoryItem.serial_number.ilike(search),
                InventoryItem.item_name.ilike(search),
                InventoryItem.color.ilike(search),
                InventoryItem.size.ilike(search),
            )
        )

    items = query.order_by(InventoryItem.updated_at.desc()).all()
    return jsonify([serialize_item(item) for item in items])


@api.route('/inventory-items', methods=['POST'])
def create_inventory_items():
    payload = parse_payload()

    item_name = (payload.get('item_name') or '').strip()
    color = (payload.get('color') or '').strip()
    # 尺寸為選填，配件類商品可留空
    size = (payload.get('size') or '').strip() or None

    if not item_name:
        return error_response('item_name 為必填欄位')
    if not color:
        return error_response('color 為必填欄位')

    try:
        quantity = parse_int(payload.get('quantity'), 'quantity', default=1, minimum=1)
    except ValueError as exc:
        return error_response(str(exc))

    serial_numbers = generate_serial_numbers(quantity)
    items = []
    for serial_number in serial_numbers:
        item = InventoryItem(
            serial_number=serial_number,
            item_name=item_name,
            color=color,
            size=size,
            status_code=0,
        )
        db.session.add(item)
        items.append(item)

    db.session.commit()
    logger.info('Created %d inventory items for %s / %s / %s', quantity, item_name, color, size)
    return jsonify({
        'created_count': len(items),
        'serial_numbers': serial_numbers,
        'items': [serialize_item(item) for item in items],
    }), 201


@api.route('/inventory-items/<string:serial_number>', methods=['PATCH'])
def update_inventory_item(serial_number):
    item = InventoryItem.query.get_or_404(serial_number)
    payload = parse_payload()

    item_name = payload.get('item_name')
    color = payload.get('color')
    size = payload.get('size')
    status_code = payload.get('status_code')

    if item_name is not None:
        item_name = item_name.strip()
        if not item_name:
            return error_response('item_name 不可為空')
        item.item_name = item_name

    if color is not None:
        color = color.strip()
        if not color:
            return error_response('color 不可為空')
        item.color = color

    if size is not None:
        # 允許清空尺寸（設為 NULL），代表此商品沒有尺寸
        item.size = size.strip() or None

    if status_code not in (None, ''):
        try:
            parsed_status = parse_int(status_code, 'status_code', minimum=0)
        except ValueError as exc:
            return error_response(str(exc))
        if parsed_status not in STATUS_LABELS:
            return error_response('status_code 不合法')
        item.status_code = parsed_status

    item.updated_at = datetime.utcnow()
    db.session.commit()

    logger.info('Updated inventory item %s', serial_number)
    return jsonify(serialize_item(item))


@api.route('/inventory-items/<string:serial_number>', methods=['DELETE'])
def delete_inventory_item(serial_number):
    item = InventoryItem.query.get_or_404(serial_number)
    db.session.delete(item)
    db.session.commit()
    logger.info('Deleted inventory item %s', serial_number)
    return jsonify({'message': '物品已刪除', 'serial_number': serial_number})


# ---------------------------------------------------------------------------
# 會員尺寸查詢 inventory-search（會寫一筆 search_log）
# ---------------------------------------------------------------------------
@api.route('/inventory-search', methods=['POST'])
def search_inventory_by_size():
    payload = parse_payload()

    try:
        employee_id = parse_int(payload.get('employee_id'), 'employee_id', minimum=1)
        customer_id = parse_int(payload.get('customer_id'), 'customer_id', minimum=1)
    except ValueError as exc:
        return error_response(str(exc))

    employee = Employee.query.get(employee_id)
    if not employee:
        return error_response('找不到這位員工', 404)

    customer = Customer.query.get(customer_id)
    if not customer:
        return error_response('找不到這位會員', 404)

    # 尺寸為選填。留空代表不限尺寸（適合配件等沒有尺寸的商品）
    size = (payload.get('size') or '').strip() or None
    item_name = (payload.get('item_name') or '').strip()

    query = InventoryItem.query.filter(InventoryItem.status_code == 0)
    if item_name:
        query = query.filter(InventoryItem.item_name.ilike(f'%{item_name}%'))
    if size:
        # 指定尺寸時，符合該尺寸的、以及沒有尺寸的商品（配件）都納入，不硬性排除
        query = query.filter(
            or_(InventoryItem.size == size, InventoryItem.size.is_(None))
        )

    results = query.order_by(InventoryItem.item_name.asc(), InventoryItem.color.asc()).all()
    result_count = len(results)

    log = SearchLog(
        employee_id=employee_id,
        customer_id=customer_id,
        queried_size=size,
        queried_item_name=item_name or None,
        result_count=result_count,
        timestamp=datetime.utcnow(),
    )
    db.session.add(log)
    db.session.commit()

    logger.info(
        'Employee %s searched size=%s for customer %s -> %d items',
        employee_id, size, customer_id, result_count,
    )
    return jsonify({
        'queried_size': size,
        'queried_item_name': item_name or None,
        'result_count': result_count,
        'results': [serialize_item(item) for item in results],
        'search_log': log.to_dict(),
    })


@api.route('/search-logs', methods=['GET'])
def list_search_logs():
    logs = SearchLog.query.order_by(SearchLog.timestamp.desc()).limit(50).all()
    return jsonify([log.to_dict() for log in logs])


# ---------------------------------------------------------------------------
# 櫃檯 counter_logs
# ---------------------------------------------------------------------------
@api.route('/counter-logs', methods=['GET'])
def list_counter_logs():
    logs = CounterLog.query.order_by(CounterLog.timestamp.desc()).limit(50).all()
    return jsonify([log.to_dict() for log in logs])


@api.route('/counter-logs', methods=['POST'])
def create_counter_log():
    payload = parse_payload()
    serial_number = (payload.get('serial_number') or '').strip().upper()
    note = (payload.get('note') or '').strip() or None

    if not serial_number:
        return error_response('serial_number 為必填欄位')

    try:
        employee_id = parse_int(payload.get('employee_id'), 'employee_id', minimum=1)
        customer_id = parse_int(payload.get('customer_id'), 'customer_id', minimum=1)
    except ValueError as exc:
        return error_response(str(exc))

    employee = Employee.query.get(employee_id)
    if not employee:
        return error_response('找不到這位員工', 404)

    customer = Customer.query.get(customer_id)
    if not customer:
        return error_response('找不到這位會員', 404)

    try:
        timestamp = parse_datetime(payload.get('timestamp'))
    except ValueError as exc:
        return error_response(str(exc))

    item = InventoryItem.query.get_or_404(serial_number)
    previous_status = item.status_code

    if item.status_code != 0:
        return error_response(f'目前狀態為「{item.status_label}」，不能再走櫃檯正常出貨流程', 409)

    item.status_code = 1
    item.updated_at = datetime.utcnow()

    log = CounterLog(
        serial_number=item.serial_number,
        employee_id=employee_id,
        customer_id=customer_id,
        previous_status=previous_status,
        new_status=1,
        note=note or '櫃檯完成正常出貨設定',
        timestamp=timestamp,
    )
    db.session.add(log)
    db.session.commit()

    logger.info('Counter (employee %s) sold %s to customer %s', employee_id, serial_number, customer_id)
    return jsonify(log.to_dict()), 201


# ---------------------------------------------------------------------------
# 閘門 gate_logs
# ---------------------------------------------------------------------------
@api.route('/gate-logs', methods=['GET'])
def list_gate_logs():
    logs = GateLog.query.order_by(GateLog.timestamp.desc()).limit(50).all()
    return jsonify([log.to_dict() for log in logs])


@api.route('/gate-logs', methods=['POST'])
def create_gate_log():
    payload = parse_payload()
    serial_number = (payload.get('serial_number') or '').strip().upper()
    note = (payload.get('note') or '').strip() or None

    if not serial_number:
        return error_response('serial_number 為必填欄位')

    try:
        timestamp = parse_datetime(payload.get('timestamp'))
    except ValueError as exc:
        return error_response(str(exc))

    item = InventoryItem.query.get_or_404(serial_number)
    previous_status = item.status_code

    if item.status_code == 1:
        result = 'authorized'
        new_status = 1
        final_note = note or '閘門確認商品已正常售出'
    elif item.status_code == 0:
        result = 'unauthorized'
        new_status = 2
        final_note = note or '商品未經櫃檯正常出貨，閘門判定為未授權'
    else:
        result = 'unauthorized'
        new_status = 2
        final_note = note or '商品已處於未授權狀態，再次通過閘門'

    item.status_code = new_status
    item.updated_at = datetime.utcnow()

    log = GateLog(
        serial_number=item.serial_number,
        result=result,
        previous_status=previous_status,
        new_status=new_status,
        note=final_note,
        is_unread=(result == 'unauthorized'),
        timestamp=timestamp,
    )
    db.session.add(log)
    db.session.commit()

    logger.info('Gate checked %s result=%s', serial_number, result)
    return jsonify(log.to_dict()), 201


@api.route('/inventory-groups', methods=['GET'])
def get_inventory_groups():
    return jsonify(grouped_inventory_rows())


@api.route('/unauthorized-gate-logs/mark-read', methods=['POST'])
def mark_unauthorized_gate_logs_read():
    unread_rows = GateLog.query.filter_by(result='unauthorized', is_unread=True).all()
    for row in unread_rows:
        row.is_unread = False

    if unread_rows:
        db.session.commit()

    return jsonify({'marked_count': len(unread_rows)})


@api.route('/labels', methods=['GET'])
def get_labels():
    return jsonify({
        'status_labels': STATUS_LABELS,
        'gate_result_labels': GATE_RESULT_LABELS,
        'size_choices': list(SIZE_CHOICES),
    })
