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
    
    def get_group_actions(self):
        # 提取组的action
        self.log.info("提取组的action")
        group_actions = {}
        for g in self.groups:
            group_actions[g.get("key","none")] = g.get("action","none")
        
        return group_actions

    def get_caselist(self):

        self.get_groupsandnodes()

        groups = {}
        self.log.info("根据Group进行分组...")
        for node in self.nodes:
            nd = {"group":"unknown","nodes":[]}
            nodegroup = node.get("group")
            if nodegroup in groups.keys():
                groups[nodegroup].append(node)
            else:
                groups[nodegroup] = [node]

        # 去除not enable 的Group
        self.log.info("去除not enable 的Group")
        for g in self.groups:
            enabled = g.get("enable",True)
            if not enabled:
                self.log.info("从分组中删除非 enable 的Group key:{}, {}".format(g.get("key"),g.get('text')))
                groups.pop(g.get("key")) 
      
        # 提取每组关键字， groupnumber::text
        self.log.info("提取每组关键字 groupkey::nodekey::nodetext")
        groups_keywords = []
        for gs in groups.values():
            groupkeywords=[]
            for n in gs:
                kw = "{}::{}::{}".format(str(n.get("group",0)), str(n.get("key",0)), n.get("text")) # groupkey::nodekey::nodetext
                groupkeywords.append(kw)
            groups_keywords.append(groupkeywords)

        # 生成测试用例列表，作为各种输出模式的数据文件
        self.log.info("生成测试用例列表，作为各种输出模式的数据文件")
        caselist = []
        for case in product(*groups_keywords):
            caselist.append(case)

        self.check_properties(caselist)

        return caselist

    # 删除不具共同属性的用例
    def check_properties(self, caselist):
        ## caselist:  [(g::n::x,g::n::x,g::n::x)(g::n::x)()]
        badcases = []
        for case in caselist:
            case_property = []
            for step in case:
                (gkey, nkey, text) = step.split("::")
                stet_property = self.get_nodeproperty(nkey)
                if len(stet_property) > 0 :
                    case_property.append(stet_property)
            
            if len(case_property) < 2 :
                continue
            fst = case_property[0]
            for cp in case_property[1:]:
                fst &= cp
            if len(fst) == 0:
                badcases.append(case)
        
        for case in badcases:
            self.log.info("删除不具共同属性用例:{}".format(case))
            caselist.remove(case)

    def get_nodeproperty(self, nodekey):
        node_property = set()
        for n in self.nodes:
            if n.get("key") == int(nodekey):
                ps = n.get("properties")
                if ps:
                    for p in ps.split(','):
                        node_property.add(p.strip())
        #self.log.info("取得节点{}的属性为:{}".format(nodekey,node_property))
        return node_property

    def gen_autocase(self):
        #################################### 自动化用例 ####################################
        outputfile = os.path.splitext(self.tmdfile)[0] + '.robot'

        with open(outputfile, mode='w', encoding="utf8") as ff:
            ff.write("*** Settings ***\n\n\n*** Variables ***\n\n\n*** Test Cases ***\n")

        caselist = self.get_caselist()
        group_actions = self.get_group_actions()
        with open(outputfile, mode='a', encoding="utf8") as ff:
            for case in caselist:
                casename=""
                for step in case:
                    casename += '_'
                    (gkey, nkey, text) = step.split("::")
                    casename += "{}x{}".format(gkey,nkey)

                ff.write("T{} \n".format(casename))

                for step in case:
                    (gkey, nkey, text) = step.split("::")
                    ff.write("    {}    {} \n".format(group_actions[int(gkey)],text))
                
                ff.write("    check    用例返回成功\n")
                ff.write("  \n")
        

        return {"status": "success", "msg": "生成文件：{}.".format(outputfile)}
    def gen_casetemplate(self):
        self.log.info("生成用例模版")
        return {"status": "success", "msg": "生成文件：{}.".format(self.tmdfile)}
    def gen_mancase(self):
        #################################### 手工用例 ####################################
        outputfile = os.path.splitext(self.tmdfile)[0] + '.txt'
        caselist = self.get_caselist()
        group_actions = self.get_group_actions()

        casenum = 0
        with open(outputfile, 'w') as ff:
            for case in caselist:
                casename=""
                for step in case:
                    casename += '_'
                    (gkey, nkey, text) = step.split("::")
                    casename += "{}x{}".format(gkey,nkey)

                ff.write("T{} \n".format(casename))
                ff.write("  输入：\n")

                for step in case:
                    (gkey, nkey, text) = step.split("::")
                    ff.write("    {}::{} \n".format(group_actions[int(gkey)],text))
                
                ff.write("  输出: \n")
                ff.write("    用例返回成功\n")
                ff.write("  \n")
                casenum += 1

        return {"status": "success", "msg": "用例数:{},文件：{}.".format(casenum,outputfile)}

