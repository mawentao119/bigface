import os,json
from utils.file import write_file,copy_file
from utils.model_base import CaseTemplate
from itertools import product

class template(CaseTemplate):

    def __init__(self, tplname, tmdfile, data):
        CaseTemplate.__init__(self,tplname, tmdfile ,data)
        self.desc = "数据驱动及多输入节点状态,每个输入作为一组输入"
        self.groups = []
        self.nodes = []

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
            copy_file(tplfile, user_path)
        else:
            result["status"] = "fail"
            result["msg"] = "失败: 文件已存在{}".format(user_path)



        return result

    def save_data(self):
        result = {"status": "success", "msg": "成功：保存模型成功."}
        self.log.info("Save Model:{}".format(self.tmdfile))

        if not write_file(self.tmdfile, self.data2str()):
            result["status"] = "fail"
            result["msg"] = "失败：保存模型失败"

        return result

    def get_groupsandnodes(self):
        
        self.log.info("取得Groups 和 Nodes ")
        self.groups = []
        self.nodes = []

        mod = json.load(open(self.tmdfile, encoding='utf-8'))
        for node in mod["nodeDataArray"]:
            isGroup = node.get("isGroup",None)
            if isGroup:
                self.groups.append(node)
            else:
                self.nodes.append(node)

    def gen_autocase(self):

        self.get_groupsandnodes()
        outputfile = os.path.splitext(self.tmdfile)[0] + '.robot'

        self.log.info("自动化用例,input：{}, output:{}".format(self.tmdfile,outputfile))

        with open(outputfile, 'w') as ff:
            ff.write("*** Settings *** \n")
            ff.write("*** Variables *** \n")
            ff.write("*** Test Cases *** \n")

        groups = {}
        
        for node in self.nodes:
            nd = {"group":"unknown","nodes":[]}
            nodegroup = node.get("group")
            if nodegroup in groups.keys():
                groups[nodegroup].append(node)
            else:
                groups[nodegroup] = [node]
        
        groups_keywords = []
        for gs in groups.values():
            groupkeywords=[]
            for n in gs:
                groupkeywords.append(n.get("text"))
            groups_keywords.append(groupkeywords)

        for kw in product(*groups_keywords):
            i = 1
            with open(outputfile, 'a') as ff:
                ff.write("TestCase_{} \n".format(i))
                ff.write("    [Documentation]  {} \n".format(kw))
                ff.write("    INPUT  {} \n".format(kw))
                ff.write("    EXPECT   SUCESS \n")
            i = i + 1

        return {"status": "success", "msg": "生成文件：{}.".format(outputfile)}
    def gen_casetemplate(self):
        self.log.info("生成用例模版")
        return {"status": "success", "msg": "生成文件：{}.".format(self.tmdfile)}
    def gen_mancase(self):

        self.log.info("生成手工用例")
        return {"status": "success", "msg": "生成文件：{}.".format(self.tmdfile)}

