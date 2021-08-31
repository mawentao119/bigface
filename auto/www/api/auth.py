# -*- coding: utf-8 -*-

__author__ = "苦叶子"

"""

modified: use DB not json.

"""
from flask import current_app, url_for, session
from flask_restful import Resource, reqparse
from werkzeug.security import check_password_hash
from utils.mylogger import getlogger

class Auth(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('username', type=str)
        self.parser.add_argument('password', type=str)
        self.log = getlogger(__name__)

    def get(self):
        args = self.parser.parse_args()
        username = args["username"]

        if username in session:
            session.pop(username, None)

        return {"status": "success", "msg": "登出成功", "url": url_for('routes.index')}, 201

    # chairs added: use DB
    def post(self):
        args = self.parser.parse_args()
        username = args["username"]
        password = args["password"]
        app = current_app._get_current_object()

        passwordHash = app.config["DB"].get_password(username)
        session['username'] = username
        self.log.info("登录请求: user: {} password xxx".format(username))

        if username == "Admin":
            if passwordHash and check_password_hash(passwordHash, password):
                app.config['DB'].insert_loginfo(username, 'login', username, 'x', 'success')
                return {"status": "success", "msg": "Admin登录成功", "url": url_for('routes.dashboard')}, 201
            else:
                app.config['DB'].insert_loginfo(username, 'login', username, password, 'fail')
                self.log.warning("登录失败: Admin:{}".format(password))
                return {"status": "Fail", "msg": "Admin登录失败", "url": url_for('routes.index')}, 201
        else:
            app.config['DB'].insert_loginfo(username, 'login', username, password, 'success')
            return {"status": "success", "msg": "登录成功", "url": url_for('routes.dashboard')}, 201

