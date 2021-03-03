import os,json
from utils.file import write_file,copy_file
from utils.model_base import CaseTemplate

def output_path(ps, casenum, method, output_file):
    "将每条链路，附带上属性及描述，写输出文件"
    if len(ps) == 0:
        print("路径为空，请检查模型文件")
        return

    casename = ''
    line = ''

    for p in ps:
        casename += '_' + str(p.get("key"))
        line += '>' + p.get("text") + ":" + p.get("end").get("text")

    with open(output_file, 'a') as ff:
        ff.write("T" + str(casenum) + casename + '\n')

        if method == 'casetemplate':
            ff.write("    [用例描述]{} \n".format(line))
        else:
            ff.write("    [Documentation]    {}\n".format(line))

        if method == 'casetemplate':
            for p in ps:
                ff.write("    Do:{}[{}] {}\n".format(p.get("text"), p.get(
                    "parameters"), "#"+p.get("description") if p.get("description") else ''))
                ff.write("    Chk:{}[{}] {}\n".format(p.get("end").get("text"), p.get("end").get(
                    "properties"), "#"+p.get("end").get("description") if p.get("end").get("description") else ''))
        elif method == 'handcase':
            ff.write("    [Tags]    Hand\n")
            for p in ps:
                ff.write("    {}    [{}] {}\n".format(p.get("text"), p.get(
                    "parameters"), "#"+p.get("description") if p.get("description") else ''))
                ff.write("    检查结果    {}[{}] {}\n".format(p.get("end").get("text"), p.get("end").get(
                    "properties"), "#"+p.get("end").get("description") if p.get("end").get("description") else ''))
        else:   # 'autocase'
            ff.write("    [Tags]    Auto\n")
            for p in ps:
                ff.write("    {}    [{}] {}\n".format(p.get("text"), p.get(
                    "parameters"), "#"+p.get("description") if p.get("description") else ''))
                ff.write("    检查结果    {}[{}] {}\n".format(p.get("end").get("text"), p.get("end").get(
                    "properties"), "#"+p.get("end").get("description") if p.get("end").get("description") else ''))

        ff.write("\n")

    return

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

        if not write_file(self.tmdfile, self.data2str()):
            result["status"] = "fail"
            result["msg"] = "失败：保存模型失败"

        return result

    def gen_modelgraph(self):
        "json数据 图形化：有向无环图"
        mod = json.load(open(self.tmdfile, encoding='utf-8'))

        # 让 link 的 end 指向 具体 node
        for link in mod["linkDataArray"]:
            link["end"] = None
            for node in mod["nodeDataArray"]:
                if link["to"] == node["id"]:
                    link["end"] = node

        # 让 node 具有 outlinks
        for node in mod["nodeDataArray"]:
            node["outlinks"] = []
            for link in mod["linkDataArray"]:
                if link["from"] == node["id"]:
                    node["outlinks"].append(link)

        self.log.info("完成模型数据图形化：{}".format(self.tmdfile))
        return mod

    def walk_model(self, method, output_file):
        "遍历图形， 生成每条执行路线"

        mod = self.gen_modelgraph()

        startnode = None
        for node in mod["nodeDataArray"]:
            if node["id"] == -1:
                startnode = node
                break

        if (not startnode):
            self.log.error("找不到Start节点（id为-1）")
            return None

        links = []
        casenum = 1

        def find_paths(node):
            nonlocal links
            nonlocal casenum
            if node["outlinks"] == []:
                output_path(links, casenum, method, output_file)
                casenum += 1
                links.remove(links[-1]) if len(links) > 0 else None
                return
            for l in node["outlinks"]:
                links.append(l)
                find_paths(l["end"])
            links.remove(links[-1]) if len(links) > 0 else None

        return find_paths(startnode)

    def gen_autocase(self):
        outputfile = os.path.splitext(self.tmdfile)[0] + '.robot'

        with open(outputfile, 'w') as ff:
            ff.write("*** Settings *** \n")
            ff.write("*** Variables *** \n")
            ff.write("*** Test Cases *** \n")

        res = self.walk_model("autocase", outputfile)
        return {"status": "success", "msg": "生成文件：{}.".format(outputfile)}
    def gen_casetemplate(self):
        outputfile = os.path.splitext(self.tmdfile)[0] + '.tplt'
        res = self.walk_model("casetemplate", outputfile)
        return {"status": "success", "msg": "生成文件：{}.".format(outputfile)}
    def gen_mancase(self):
        outputfile = os.path.splitext(self.tmdfile)[0] + '.txt'
        res = self.walk_model("handcase", outputfile)
        return {"status": "success", "msg": "生成文件：{}.".format(outputfile)}