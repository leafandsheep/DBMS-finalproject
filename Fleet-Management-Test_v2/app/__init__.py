# coding=utf-8

from flask import Flask
from config import config
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.mysql import DECIMAL, TINYINT


#import SQLAlchemy
# use_native_unicode='utf8'
db = SQLAlchemy()


def create_app(config_name):
    app = Flask(__name__, instance_relative_config=True)
    # load default configuration
    app.config.from_object(config[config_name])
    app.config.from_pyfile('config.cfg', silent=True)
    config[config_name].init_app(app)
    # register Flask-SQLAlchemy
    db.init_app(app)
    # register the blueprint and set url_prefix

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .api import api as api_1_0_blueprint
    app.register_blueprint(api_1_0_blueprint, url_prefix='/api/v1.0')

    # from .api.gateway_use import gateway_use as gateway_use_blueprint
    # app.register_blueprint(gateway_use_blueprint)

    return app
