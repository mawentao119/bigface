import json
from flask import current_app
from utils.file import write_file

from utils.mylogger import getlogger

class CaseTemplate(object):

    "测试设计模版基础类"

    def __init__(self, tname, tmdfile="", data={}):

        self.desc = "我是用来继承的，模版描述写在这里"
        self.tplname = tname
        self.tmdfile = tmdfile
        self.data = data

        self.app = current_app._get_current_object()

        # if isinstance(data, str):
        #     self.data = json.loads(str)
        # elif isinstance(data, dict):
        #     self.data = data
        # else:
        #     self.data = {}

        self.log = getlogger(self.tplname)

    def set_desc(self, desc):
        self.desc = desc
    def get_desc(self):
        return self.desc
    def data2str(self):
        return json.dumps(self.data)

    def create_model(self):
        print(">> Create model")

    def save_data(self):
        result = {"status": "success", "msg": "成功：保存成功."}
        self.log.info("Save Model:{}".format(self.tmdfile))

        if not write_file(self.tmdfile, self.data2str()):
            result["status"] = "fail"
            result["msg"] = "失败：保存失败"

        return result

    def gen_casetemplate(self):
        print(">> Gen Case Template ..")

    def gen_mancase(self):
        print(">> Gen Man Cases ..")

    def gen_autocase(self):
        print(">> Gen Auto Cases ..")

