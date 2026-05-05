from flask import abort, render_template

from app.models import (
    GATE_RESULT_LABELS,
    INVENTORY_ACTION_LABELS,
    PRODUCT_STATUS_LABELS,
    GateRecord,
    InventoryOperation,
    Product,
)

from . import main


FOCUS_TOPICS = {
    'products': {
        'title': '商品總數',
        'subtitle': '檢視系統內目前所有商品主檔，適合快速盤點整體庫存資料。',
        'accent': 'clay',
        'empty_message': '目前沒有任何商品資料。',
    },
    'in-stock': {
        'title': '庫存中商品',
        'subtitle': '只顯示目前仍在庫存中的商品，適合做現場盤點與剩餘量確認。',
        'accent': 'forest',
        'empty_message': '目前沒有庫存中的商品。',
    },
    'checked-out': {
        'title': '已結帳商品',
        'subtitle': '檢視已完成出庫或結帳流程的商品，方便對照交易或出貨紀錄。',
        'accent': 'amber',
        'empty_message': '目前沒有已結帳商品。',
    },
    'unauthorized': {
        'title': '未授權離場商品',
        'subtitle': '聚焦異常事件，優先協助你追蹤未經授權即離場的商品。',
        'accent': 'crimson',
        'empty_message': '目前沒有未授權離場商品。',
    },
    'operations': {
        'title': '操作紀錄',
        'subtitle': '顯示全部入庫與出庫操作，適合回顧操作流程與人員行為。',
        'accent': 'slate',
        'empty_message': '目前沒有任何操作紀錄。',
    },
    'gate-records': {
        'title': '門禁紀錄',
        'subtitle': '顯示所有閘道事件，方便你檢查授權進出與異常通行。',
        'accent': 'violet',
        'empty_message': '目前沒有任何門禁紀錄。',
    },
}


def get_focus_context(topic):
    config = FOCUS_TOPICS.get(topic)
    if not config:
        return None

    if topic == 'products':
        records = Product.query.order_by(Product.update_time.desc()).all()
        rows = [product.to_dict() for product in records]
        table_type = 'products'
    elif topic == 'in-stock':
        records = Product.query.filter_by(status_code=0).order_by(Product.update_time.desc()).all()
        rows = [product.to_dict() for product in records]
        table_type = 'products'
    elif topic == 'checked-out':
        records = Product.query.filter_by(status_code=1).order_by(Product.update_time.desc()).all()
        rows = [product.to_dict() for product in records]
        table_type = 'products'
    elif topic == 'unauthorized':
        records = Product.query.filter_by(status_code=2).order_by(Product.update_time.desc()).all()
        rows = [product.to_dict() for product in records]
        table_type = 'products'
    elif topic == 'operations':
        records = InventoryOperation.query.order_by(InventoryOperation.timestamp.desc()).all()
        rows = [operation.to_dict() for operation in records]
        table_type = 'operations'
    else:
        records = GateRecord.query.order_by(GateRecord.timestamp.desc()).all()
        rows = [record.to_dict() for record in records]
        table_type = 'gate-records'

    return {
        'topic': topic,
        'title': config['title'],
        'subtitle': config['subtitle'],
        'accent': config['accent'],
        'empty_message': config['empty_message'],
        'rows': rows,
        'count': len(rows),
        'table_type': table_type,
    }


@main.route('/')
def index():
    return render_template(
        'index.html',
        status_labels=PRODUCT_STATUS_LABELS,
        action_labels=INVENTORY_ACTION_LABELS,
        gate_result_labels=GATE_RESULT_LABELS,
    )


@main.route('/focus/<string:topic>')
def focus(topic):
    context = get_focus_context(topic)
    if not context:
        abort(404)

    return render_template('focus_list.html', **context)
