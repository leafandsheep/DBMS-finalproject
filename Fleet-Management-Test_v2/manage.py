# coding=utf-8

import os

from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager, Shell

from app import create_app, db
from app.models import GateRecord, InventoryOperation, Product

app = create_app(os.getenv('FLASK_CONFIG', 'default'))
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return {
        'app': app,
        'db': db,
        'Product': Product,
        'InventoryOperation': InventoryOperation,
        'GateRecord': GateRecord,
    }


@manager.command
def initdb():
    with app.app_context():
        db.create_all()
    print('Database tables created.')


manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


if __name__ == '__main__':
    manager.run()
