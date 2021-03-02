import os
from utils.file import write_file,copy_file
from utils.model_base import CaseTemplate

class template(CaseTemplate):

    def __init__(self, tplname, tmdfile, data):
        CaseTemplate.__init__(self,tplname, tmdfile ,data)
        self.desc = "通过操作驱动，动作和状态转换模版"

    def create_model(self):
        self.log.info("通过模版{} ,创建文件：{}".format(self.tplname, self.tmdfile))

        tplfile = os.path.join(self.app.config["CASE_TEMPLATE_DIR"], self.tplname + '.tplt')

        user_path = self.tmdfile

        result = {"status": "success", "msg": "创建测试模型成功" +
                                              ":" + os.path.basename(user_path) + ":" + user_path}

        if not os.path.exists(tplfile):
            result["status"] = "fail"
            result["msg"] = "失败: 模版不存在{}".format(tplfile)
            return result

        if not os.path.exists(user_path):
            tplfile = os.path.join(self.app.config["CASE_TEMPLATE_DIR"], 'template1.tplt')
            self.log.info("Create Case Model from tempate file:{}".format(tplfile))
            copy_file(tplfile, user_path)
        else:
            result["status"] = "fail"
            result["msg"] = "失败: 文件已存在{}".format(user_path)

        return result

    def save_data(self):
        result = {"status": "success", "msg": "成功：保存模型成功."}
        self.log.info("Save Model:{}".format(self.tmdfile))

        if not write_file(self.tmdfile, self.data):
            result["status"] = "fail"
            result["msg"] = "失败：保存模型失败"

        return result

