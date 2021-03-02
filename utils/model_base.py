import os, json
from flask import current_app
from utils.file import write_file
from utils.mylogger import getlogger

class CaseTemplate(object):

    "测试设计模版基础类"

    def __init__(self, tname, tmdfile="", data=None):

        self.desc = "我是用来继承的，模版描述写在这里"
        self.tplname = tname
        self.tmdfile = tmdfile

        self.app = current_app._get_current_object()

        if isinstance(data, str):
            self.data = data
        elif isinstance(data, dict):
            self.data = json.dumps(data)
        else:
            self.data = ""

        self.log = getlogger(self.tplname)

    def set_desc(self, desc):
        self.desc = desc
    def get_desc(self):
        return self.desc

    def create_model(self):
        print(">> Create model")

    def save_data(self):
        result = {"status": "success", "msg": "成功：保存成功."}
        self.log.info("Save Model:{}".format(self.tmdfile))

        if not write_file(self.tmdfile, self.data):
            result["status"] = "fail"
            result["msg"] = "失败：保存失败"

        return result

    def gen_caseTemplate(self):
        print(">> Gen Case Template ..")

    def gen_manCases(self):
        print(">> Gen Man Cases ..")

    def gen_autoCases(self):
        print(">> Gen Auto Cases ..")

