# coding=utf-8

from datetime import datetime

from . import db


PRODUCT_STATUS_LABELS = {
    0: '庫存中',
    1: '已結帳',
    2: '未授權離場',
}

INVENTORY_ACTION_LABELS = {
    'stock_in': '入庫',
    'stock_out': '出庫',
}

GATE_RESULT_LABELS = {
    'authorized': '已授權',
    'unauthorized': '未授權',
}


class Product(db.Model):
    __tablename__ = 'products'

    tag_id = db.Column(db.String(64), primary_key=True)
    product_name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    status_code = db.Column(db.Integer, nullable=False, default=0)
    last_action = db.Column(db.String(64), nullable=False, default='created')
    update_time = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    operations = db.relationship(
        'InventoryOperation',
        backref='product',
        lazy='dynamic',
        cascade='all, delete-orphan',
    )
    gate_records = db.relationship(
        'GateRecord',
        backref='product',
        lazy='dynamic',
        cascade='all, delete-orphan',
    )

    @property
    def status_label(self):
        return PRODUCT_STATUS_LABELS.get(self.status_code, '未知狀態')

    def to_dict(self):
        return {
            'tag_id': self.tag_id,
            'product_name': self.product_name,
            'price': float(self.price),
            'status_code': self.status_code,
            'status_label': self.status_label,
            'last_action': self.last_action,
            'update_time': self.update_time.isoformat() if self.update_time else None,
        }


class InventoryOperation(db.Model):
    __tablename__ = 'inventory_operations'

    operation_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tag_id = db.Column(db.String(64), db.ForeignKey('products.tag_id'), nullable=False)
    action = db.Column(db.String(20), nullable=False)
    operator = db.Column(db.String(80), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    @property
    def action_label(self):
        return INVENTORY_ACTION_LABELS.get(self.action, self.action)

    def to_dict(self):
        return {
            'operation_id': self.operation_id,
            'tag_id': self.tag_id,
            'product_name': self.product.product_name if self.product else None,
            'action': self.action,
            'action_label': self.action_label,
            'operator': self.operator,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
        }


class GateRecord(db.Model):
    __tablename__ = 'gate_records'

    gate_record_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tag_id = db.Column(db.String(64), db.ForeignKey('products.tag_id'), nullable=False)
    gate_id = db.Column(db.String(40), nullable=False)
    result = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    @property
    def result_label(self):
        return GATE_RESULT_LABELS.get(self.result, self.result)

    def to_dict(self):
        return {
            'gate_record_id': self.gate_record_id,
            'tag_id': self.tag_id,
            'product_name': self.product.product_name if self.product else None,
            'gate_id': self.gate_id,
            'result': self.result,
            'result_label': self.result_label,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
        }
