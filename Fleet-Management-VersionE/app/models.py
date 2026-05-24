# coding=utf-8

from datetime import datetime

from . import db


STATUS_LABELS = {
    0: '庫存中',
    1: '已售出',
    2: '未授權',
}

GATE_RESULT_LABELS = {
    'authorized': '正常出貨',
    'unauthorized': '異常出貨',
}


class InventoryItem(db.Model):
    __tablename__ = 'inventory_items'

    serial_number = db.Column(db.String(64), primary_key=True)
    item_name = db.Column(db.String(120), nullable=False, index=True)
    color = db.Column(db.String(60), nullable=False, index=True)
    status_code = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    counter_logs = db.relationship(
        'CounterLog',
        backref='item',
        lazy='dynamic',
        cascade='all, delete-orphan',
    )
    gate_logs = db.relationship(
        'GateLog',
        backref='item',
        lazy='dynamic',
        cascade='all, delete-orphan',
    )

    @property
    def status_label(self):
        return STATUS_LABELS.get(self.status_code, f'未知狀態({self.status_code})')

    @property
    def status_tone(self):
        return {
            0: 'in-stock',
            1: 'sold',
            2: 'unauthorized',
        }.get(self.status_code, 'unknown')

    def to_dict(self):
        return {
            'serial_number': self.serial_number,
            'item_name': self.item_name,
            'color': self.color,
            'status_code': self.status_code,
            'status_label': self.status_label,
            'status_tone': self.status_tone,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class CounterLog(db.Model):
    __tablename__ = 'counter_logs'

    counter_log_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    serial_number = db.Column(
        db.String(64),
        db.ForeignKey('inventory_items.serial_number'),
        nullable=False,
        index=True,
    )
    previous_status = db.Column(db.Integer, nullable=False)
    new_status = db.Column(db.Integer, nullable=False)
    operator = db.Column(db.String(80), nullable=False)
    note = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    @property
    def previous_status_label(self):
        return STATUS_LABELS.get(self.previous_status, str(self.previous_status))

    @property
    def new_status_label(self):
        return STATUS_LABELS.get(self.new_status, str(self.new_status))

    def to_dict(self):
        return {
            'counter_log_id': self.counter_log_id,
            'serial_number': self.serial_number,
            'item_name': self.item.item_name if self.item else None,
            'color': self.item.color if self.item else None,
            'previous_status': self.previous_status,
            'previous_status_label': self.previous_status_label,
            'new_status': self.new_status,
            'new_status_label': self.new_status_label,
            'operator': self.operator,
            'note': self.note,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
        }


class GateLog(db.Model):
    __tablename__ = 'gate_logs'

    gate_log_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    serial_number = db.Column(
        db.String(64),
        db.ForeignKey('inventory_items.serial_number'),
        nullable=False,
        index=True,
    )
    result = db.Column(db.String(20), nullable=False)
    previous_status = db.Column(db.Integer, nullable=False)
    new_status = db.Column(db.Integer, nullable=False)
    note = db.Column(db.String(255), nullable=True)
    is_unread = db.Column(db.Boolean, nullable=False, default=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    @property
    def result_label(self):
        return GATE_RESULT_LABELS.get(self.result, self.result)

    @property
    def previous_status_label(self):
        return STATUS_LABELS.get(self.previous_status, str(self.previous_status))

    @property
    def new_status_label(self):
        return STATUS_LABELS.get(self.new_status, str(self.new_status))

    def to_dict(self):
        return {
            'gate_log_id': self.gate_log_id,
            'serial_number': self.serial_number,
            'item_name': self.item.item_name if self.item else None,
            'color': self.item.color if self.item else None,
            'result': self.result,
            'result_label': self.result_label,
            'previous_status': self.previous_status,
            'previous_status_label': self.previous_status_label,
            'new_status': self.new_status,
            'new_status_label': self.new_status_label,
            'note': self.note,
            'is_unread': self.is_unread,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
        }
