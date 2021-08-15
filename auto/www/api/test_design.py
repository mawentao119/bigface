# -*- coding: utf-8 -*-

__author__ = "mawentao119@gmail.com"

"""

"""

import logging
from flask import current_app, session, request
from flask_restful import Resource, reqparse
from utils.model_design import gen_casefile, save_model, create_model


class TestDesign(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('method', type=str)
        self.parser.add_argument('name', type=str)
        self.parser.add_argument('project_name', type=str)
        self.parser.add_argument('suite_name', type=str)
        self.parser.add_argument('category', type=str)
        self.parser.add_argument('key', type=str)
        self.parser.add_argument('data', type=str)

        self.app = current_app._get_current_object()
        self.log = logging.getLogger("TestDesign")

    def get(self):
        # TODO
        result = {"status": "success", "msg": "读取文件成功."}
        return result, 201

    def post(self):
        args = self.parser.parse_args()
        if args["key"]:
            args["key"] = args["key"].replace("--", "/")
        self.log.debug("Post args:{}".format(args))
        method = args["method"].lower()
        if method == "create":
            result = self.__create(args)
        elif method == "save":
            result = self.__save(args)
        elif method == "casetemplate":
            result = self.__gen_casefile(args)
        elif method == "handcase":
            result = self.__gen_casefile(args)
        elif method == "autocase":
            result = self.__gen_casefile(args)
        else:
            print(request.files["files"])

        return result, 201

    def __create(self, args):

        result = create_model(args)

        self.app.config['DB'].insert_loginfo(
            session['username'], 'model', 'create', args["key"], result['status'])

        return result

    def __save(self, args):

        result = save_model(args)

        self.app.config['DB'].insert_loginfo(
            session['username'], 'model', 'edit', args["key"], result['status'])

        return result

    def __gen_casefile(self, args):

        result = gen_casefile(args)

        return result
