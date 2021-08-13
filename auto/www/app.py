# -*- coding: utf-8 -*-

__author__ = "苦叶子"

"""
Modified by mawentao119@gmail.com
"""


from flask import Flask
from flask_apscheduler import APScheduler
from auto.configuration import config


scheduler = APScheduler()

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    scheduler.init_app(app)
    scheduler.start()

    # for blueprints
    from .blueprints import routes as routes_blueprint
    app.register_blueprint(routes_blueprint)

    from .api import api_bp as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api/v1')

    return app
