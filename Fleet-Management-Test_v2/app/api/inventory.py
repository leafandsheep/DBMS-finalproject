from datetime import datetime

from flask import jsonify, request
from sqlalchemy import or_

from app import db
from app.models import (
    GATE_RESULT_LABELS,
    INVENTORY_ACTION_LABELS,
    PRODUCT_STATUS_LABELS,
    GateRecord,
    InventoryOperation,
    Product,
)

from . import api


def error_response(message, status_code=400):
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


def parse_status_code(value, default=0):
    try:
        return int(default if value in (None, '') else value)
    except (TypeError, ValueError):
        raise ValueError('status_code 不合法')


def parse_price(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError('price 必須是有效數字')


def summary_payload():
    return {
        'total_products': Product.query.count(),
        'in_stock_count': Product.query.filter_by(status_code=0).count(),
        'checked_out_count': Product.query.filter_by(status_code=1).count(),
        'unauthorized_count': Product.query.filter_by(status_code=2).count(),
        'operation_count': InventoryOperation.query.count(),
        'gate_record_count': GateRecord.query.count(),
    }


@api.route('/summary', methods=['GET'])
def get_summary():
    return jsonify(summary_payload())


@api.route('/products', methods=['GET'])
def list_products():
    keyword = request.args.get('keyword', '').strip()
    status = request.args.get('status', '').strip()

    query = Product.query

    if keyword:
        search = f"%{keyword}%"
        query = query.filter(
            or_(
                Product.tag_id.ilike(search),
                Product.product_name.ilike(search),
            )
        )

    if status != '':
        try:
            query = query.filter(Product.status_code == int(status))
        except ValueError:
            return error_response('status 篩選值不合法')

    products = query.order_by(Product.update_time.desc()).all()
    return jsonify([product.to_dict() for product in products])


@api.route('/products', methods=['POST'])
def create_product():
    payload = parse_payload()

    tag_id = (payload.get('tag_id') or '').strip()
    product_name = (payload.get('product_name') or '').strip()
    price = payload.get('price')
    try:
        status_code = parse_status_code(payload.get('status_code', 0))
        price = parse_price(price)
    except ValueError as exc:
        return error_response(str(exc))

    if not tag_id or not product_name or price in (None, ''):
        return error_response('tag_id、product_name、price 為必填欄位')

    if status_code not in PRODUCT_STATUS_LABELS:
        return error_response('status_code 不合法')

    if Product.query.get(tag_id):
        return error_response('商品標籤已存在', 409)

    product = Product(
        tag_id=tag_id,
        product_name=product_name,
        price=price,
        status_code=status_code,
        last_action='created',
    )
    db.session.add(product)
    db.session.commit()

    return jsonify(product.to_dict()), 201


@api.route('/products/<string:tag_id>', methods=['PATCH'])
def update_product(tag_id):
    product = Product.query.get_or_404(tag_id)
    payload = parse_payload()

    product_name = payload.get('product_name')
    price = payload.get('price')
    status_code = payload.get('status_code')

    if product_name is not None:
        product_name = product_name.strip()
        if not product_name:
            return error_response('product_name 不可為空')
        product.product_name = product_name

    if price not in (None, ''):
        try:
            product.price = parse_price(price)
        except ValueError as exc:
            return error_response(str(exc))

    if status_code not in (None, ''):
        try:
            status_code = parse_status_code(status_code)
        except ValueError as exc:
            return error_response(str(exc))
        if status_code not in PRODUCT_STATUS_LABELS:
            return error_response('status_code 不合法')
        product.status_code = status_code

    product.last_action = 'manual_update'
    product.update_time = datetime.utcnow()
    db.session.commit()

    return jsonify(product.to_dict())


@api.route('/products/<string:tag_id>', methods=['DELETE'])
def delete_product(tag_id):
    product = Product.query.get_or_404(tag_id)

    if product.operations.count() or product.gate_records.count():
        return error_response('已有操作或門禁紀錄的商品不可直接刪除', 409)

    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': '商品已刪除'})


@api.route('/operations', methods=['GET'])
def list_operations():
    operations = InventoryOperation.query.order_by(
        InventoryOperation.timestamp.desc()
    ).limit(20).all()
    return jsonify([operation.to_dict() for operation in operations])


@api.route('/operations', methods=['POST'])
def create_operation():
    payload = parse_payload()

    tag_id = (payload.get('tag_id') or '').strip()
    action = (payload.get('action') or '').strip()
    operator = (payload.get('operator') or '').strip()

    if not tag_id or not action or not operator:
        return error_response('tag_id、action、operator 為必填欄位')

    if action not in INVENTORY_ACTION_LABELS:
        return error_response('action 不合法')

    product = Product.query.get(tag_id)
    if not product:
        return error_response('找不到對應商品', 404)

    try:
        timestamp = parse_datetime(payload.get('timestamp'))
    except ValueError as exc:
        return error_response(str(exc))

    operation = InventoryOperation(
        tag_id=tag_id,
        action=action,
        operator=operator,
        timestamp=timestamp,
    )

    product.status_code = 0 if action == 'stock_in' else 1
    product.last_action = action
    product.update_time = datetime.utcnow()

    db.session.add(operation)
    db.session.commit()

    return jsonify(operation.to_dict()), 201


@api.route('/gate-records', methods=['GET'])
def list_gate_records():
    gate_records = GateRecord.query.order_by(GateRecord.timestamp.desc()).limit(20).all()
    return jsonify([record.to_dict() for record in gate_records])


@api.route('/gate-records', methods=['POST'])
def create_gate_record():
    payload = parse_payload()

    tag_id = (payload.get('tag_id') or '').strip()
    gate_id = (payload.get('gate_id') or '').strip()
    result = (payload.get('result') or '').strip()

    if not tag_id or not gate_id or not result:
        return error_response('tag_id、gate_id、result 為必填欄位')

    if result not in GATE_RESULT_LABELS:
        return error_response('result 不合法')

    product = Product.query.get(tag_id)
    if not product:
        return error_response('找不到對應商品', 404)

    try:
        timestamp = parse_datetime(payload.get('timestamp'))
    except ValueError as exc:
        return error_response(str(exc))

    gate_record = GateRecord(
        tag_id=tag_id,
        gate_id=gate_id,
        result=result,
        timestamp=timestamp,
    )

    product.status_code = 1 if result == 'authorized' else 2
    product.last_action = f'{result}_exit'
    product.update_time = datetime.utcnow()

    db.session.add(gate_record)
    db.session.commit()

    return jsonify(gate_record.to_dict()), 201
