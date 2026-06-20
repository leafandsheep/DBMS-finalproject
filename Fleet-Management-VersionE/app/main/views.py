from flask import abort, render_template
from sqlalchemy import case, func

from app import db
from app.models import (
    GATE_RESULT_LABELS,
    STATUS_LABELS,
    CounterLog,
    Customer,
    Employee,
    GateLog,
    InventoryItem,
    SearchLog,
)

from . import main


DETAIL_TOPICS = {
    'items': {
        'title': '物品主表',
        'subtitle': '查看每一件單品的流水號、物件名稱、顏色、尺寸與目前狀態。',
        'table_type': 'items',
        'empty_message': '目前沒有任何物品。',
    },
    'in-stock': {
        'title': '庫存中物品',
        'subtitle': '狀態碼 0 的物品，也就是目前仍在庫存中的單品。',
        'table_type': 'items',
        'empty_message': '目前沒有狀態為庫存中的物品。',
    },
    'sold': {
        'title': '已售出物品',
        'subtitle': '狀態碼 1 的物品，也就是已經完成正常出貨流程的單品。',
        'table_type': 'items',
        'empty_message': '目前沒有已售出的物品。',
    },
    'unauthorized-events': {
        'title': '未授權事件',
        'subtitle': '查看所有被閘門判定為未授權的異常紀錄，並在進入此頁後清除未讀提醒。',
        'table_type': 'gate-logs',
        'empty_message': '目前沒有未授權事件。',
    },
    'counter-logs': {
        'title': '櫃檯日記',
        'subtitle': '查看所有經過櫃檯正常出貨處理的流水號紀錄。',
        'table_type': 'counter-logs',
        'empty_message': '目前沒有櫃檯日記。',
    },
    'gate-logs': {
        'title': '閘門日記',
        'subtitle': '查看所有經過閘門檢查的流水號紀錄。',
        'table_type': 'gate-logs',
        'empty_message': '目前沒有閘門日記。',
    },
    'grouped-inventory': {
        'title': '庫存彙總',
        'subtitle': '依據物件名稱、顏色與尺寸分組，回報所有可能組合的數量分布。',
        'table_type': 'grouped-inventory',
        'empty_message': '目前沒有可供彙總的物品資料。',
    },
    'employees': {
        'title': '員工名單',
        'subtitle': '查看所有可在櫃檯結帳或操作查詢的員工。',
        'table_type': 'employees',
        'empty_message': '目前沒有任何員工。',
    },
    'customers': {
        'title': '會員名單',
        'subtitle': '查看所有會員與其慣用尺寸。',
        'table_type': 'customers',
        'empty_message': '目前沒有任何會員。',
    },
    'search-logs': {
        'title': '會員查詢紀錄',
        'subtitle': '查看店員替會員查詢尺寸的所有互動，包含查詢時間與找到幾件在庫。',
        'table_type': 'search-logs',
        'empty_message': '目前沒有任何查詢紀錄。',
    },
}


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


def get_detail_context(topic):
    config = DETAIL_TOPICS.get(topic)
    if not config:
        return None

    if topic == 'items':
        rows = [item.to_dict() for item in InventoryItem.query.order_by(InventoryItem.updated_at.desc()).all()]
    elif topic == 'in-stock':
        rows = [
            item.to_dict()
            for item in InventoryItem.query.filter_by(status_code=0).order_by(InventoryItem.updated_at.desc()).all()
        ]
    elif topic == 'sold':
        rows = [
            item.to_dict()
            for item in InventoryItem.query.filter_by(status_code=1).order_by(InventoryItem.updated_at.desc()).all()
        ]
    elif topic == 'unauthorized-events':
        unread_logs = GateLog.query.filter_by(result='unauthorized', is_unread=True).all()
        for row in unread_logs:
            row.is_unread = False
        if unread_logs:
            db.session.commit()

        rows = [
            log.to_dict()
            for log in GateLog.query.filter_by(result='unauthorized').order_by(GateLog.timestamp.desc()).all()
        ]
    elif topic == 'counter-logs':
        rows = [log.to_dict() for log in CounterLog.query.order_by(CounterLog.timestamp.desc()).all()]
    elif topic == 'gate-logs':
        rows = [log.to_dict() for log in GateLog.query.order_by(GateLog.timestamp.desc()).all()]
    elif topic == 'employees':
        rows = [employee.to_dict() for employee in Employee.query.order_by(Employee.employee_id.asc()).all()]
    elif topic == 'customers':
        rows = [customer.to_dict() for customer in Customer.query.order_by(Customer.customer_id.asc()).all()]
    elif topic == 'search-logs':
        rows = [log.to_dict() for log in SearchLog.query.order_by(SearchLog.timestamp.desc()).all()]
    else:
        rows = grouped_inventory_rows()

    return {
        'topic': topic,
        'title': config['title'],
        'subtitle': config['subtitle'],
        'table_type': config['table_type'],
        'empty_message': config['empty_message'],
        'rows': rows,
        'count': len(rows),
    }


@main.route('/')
def index():
    return render_template(
        'index.html',
        status_labels=STATUS_LABELS,
        gate_result_labels=GATE_RESULT_LABELS,
    )


@main.route('/details/<string:topic>')
def details(topic):
    context = get_detail_context(topic)
    if not context:
        abort(404)
    return render_template('details.html', **context)
