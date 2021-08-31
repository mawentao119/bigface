# -*- coding: utf-8 -*-

__author__ = "mawentao119@gmail.com"

"""
Model based test design
"""
import os, codecs, importlib
import json
from utils.mylogger import getlogger

log = getlogger(__name__)

def show_ui(tmdfile):
    "找到 模版的 html ，解析出 tmd 文件的数据内容"
    data = ""
    html = "default.html"

    log.info("处理用例文件：{}".format(tmdfile))

    if not os.path.exists(tmdfile):
        log.error("文件不存在：{}".format(tmdfile))
        return {"html": html, "data": data}

    f = codecs.open(tmdfile, 'r', "utf-8")
    data = f.read()
    f.close()

    mod = json.load(open(tmdfile, encoding='utf-8'))

    tplname = mod.get("modelData").get("templateName")
    if tplname:
        html = "case_template/" + tplname + '.html'
    else:
        log.error("在模型中没有找到 templateName ,无法渲染:{}".format(tmdfile))
        html = "default.html"

    log.info("Html 模版文件：{}".format(html))

    return {"html": html, "data": data}

def create_model(args):

    tplname = args['category']
    tmdfile = args["key"] + '/' + args['name'] + '.tmd'

    des = 'utils.case_template.' + tplname
    t = importlib.import_module(des)
    tmp = t.template(tplname, tmdfile, {})

    result = tmp.create_model()

    return result

def save_model(args):

    result = {"status": "success", "msg": "成功：保存成功."}

    user_path = args["key"]
    data = json.loads(args["data"])

    tplname = data.get("modelData").get("templateName")
    log.info("模版名：{} 文件：{}".format(tplname,user_path))

    if tplname:
        des = 'utils.case_template.'+tplname
        t = importlib.import_module(des)
        tmp = t.template(tplname, user_path, data)
        result = tmp.save_data()
    else:
        result["status"] = "fail"
        result["msg"] = "失败：保存的数据中无法找到modelData.templateName"

    return result

def gen_casefile(args):

    method = args["method"]
    tmdfile = args["key"]

    mod = json.load(open(tmdfile, encoding='utf-8'))

    tplname = mod.get("modelData").get("templateName")

    des = 'utils.case_template.'+tplname
    t = importlib.import_module(des)
    tmp = t.template(tplname, tmdfile, {})


    if method == "handcase":
        return tmp.gen_mancase()
    if method == "autocase":
        return tmp.gen_autocase()
    if method == "casetemplate":
        return tmp.gen_casetemplate()
