# -*- coding: utf-8 -*-

__author__ = "苦叶子"
__modifier__ = "charis"
"""
解析robot.libdoc生成的xml，生成高亮及自动完成。
增加 调用生成 用户resource关键字的能力

Parse xml which generated by robot.libdoc, output auto-complet and highlight.
Generate Keywords of resource file which imported in robot case file.

"""

import os
import codecs
import xml.etree.ElementTree as ET
from robot.api import TestSuiteBuilder
from robot.running.builder import ResourceFileBuilder  # ResourceFileBuilder().build(rs) for i in rsf.imports._items:
from utils.file import mk_dirs, copy_file, get_projectnamefromkey
from utils.mylogger import getlogger
from subprocess import run as subRun, PIPE ,STDOUT

log = getlogger("parsing")

USER_KEYS = {
    "web": ["BuiltIn", "Collections", "DateTime", "String", "Screenshot", "SeleniumLibrary"],
    "app": ["BuiltIn", "Collections", "DateTime", "String", "Screenshot", "AppiumLibrary"],
    "http": ["BuiltIn", "Collections", "DateTime", "String", "RequestsLibrary"],
    "all": ["BuiltIn", "Collections", "DateTime",
            "OperatingSystem", "Process", "String", "Screenshot", "Telnet",
            "AppiumLibrary", "RequestsLibrary", "SeleniumLibrary", "SSHLibrary", "DatabaseLibrary"
            ]
}

ROBOT_BUILTIN_KEYWORDS = ["'Tags'","'Setup'","'Teardown'","'Template'","'Timeout'","'Arguments'","'Return'","'Library'","'Resource'","'Variables'","'Documentation'","'Metadata'","'FOR'","'IN'","'IN RANGE'","'IN ENUMERATE'","'IN ZIP'","'END'","'Suite Setup'","'Suite Teardown'","'Force Tags'","'Default Tags'","'Test Setup'","'Test Teardown'","'Test Template'","'Test Timeout'","'Task Setup'","'Task Teardown'","'Task Template'","'Task Timeout'"]
# TODO : define differrent keywords dirs for different types of file: robot, yaml etcs.


def get_resource_list(key):
    ext = os.path.splitext(key)[1]
    resources = []
    if ext == '.robot':
        resources += get_robotcase_res(key)
        return resources
    if ext == '.resource':
        resources += get_robotress_res(key)
        return resources

def get_robotress_res(resfile):

    ''' if resfile.endswith('.py'):
        return [] '''  # py resource also can work. No need pass.
    project = get_projectnamefromkey(resfile)
    projectdir = os.environ["PROJECT_DIR"]
    cwd = os.getcwd() + "/keyword/" + project
    if not os.path.exists(cwd):
        mk_dirs(cwd)

    try:
        ress = ResourceFileBuilder().build(resfile)
    except SyntaxError as e:
        log.error("Exception:ResourceFileBuilder().build:{} {}".format(resfile,e))
        return []
    except Exception as e:
        log.error("Exception:ResourceFileBuilder().build:{} {}".format(resfile,e))
        return []

    resources = []
    for i in ress.imports._items:
        rsfile = i.name  # Full path of file
        if rsfile.find("%{ROBOT_DIR}") != -1:
            rsfile = rsfile.replace("%{ROBOT_DIR}", projectdir)
        if rsfile.find("%{PROJECT_DIR}") != -1:
            rsfile = rsfile.replace("%{PROJECT_DIR}", projectdir)

        basename = os.path.basename(rsfile)  # Lib name without path
        fpre = basename.split('.')[0]  # BuildIn or UserRes without '.resource' or '.robot'
        xmlfile = cwd + "/%s.xml" % fpre

        if not os.path.exists(rsfile) and (
                rsfile.find('/') != -1 or rsfile.find('.robot') != -1 or rsfile.find('.resource') != -1):
            log.error("找不到资源文件:{} !".format(rsfile))
            continue

        if os.path.exists(rsfile):
            res = generate_resource_xml(rsfile, xmlfile) if not os.path.exists(xmlfile) else None
            resources.append(fpre) if os.path.exists(xmlfile) else log.error(
                "生成资源失败 XML :{},INFO:{}".format(xmlfile, res))
        else:
            res = generate_resource_xml(fpre, xmlfile) if not os.path.exists(xmlfile) else None
            resources.append(fpre) if os.path.exists(xmlfile) else log.error(
                "生成资源失败 XML :{},INFO:{}".format(xmlfile, res))

        if rsfile.endswith('.robot') or rsfile.endswith('.resource'):
            resources += get_robotress_res(rsfile)

    return resources

def get_robotcase_res(casefile):
    project = get_projectnamefromkey(casefile)
    projectdir = os.environ["PROJECT_DIR"]
    cwd = os.getcwd() + "/keyword/" + project
    if not os.path.exists(cwd):
        mk_dirs(cwd)

    try:
        suite = TestSuiteBuilder().build(casefile)
    except SyntaxError as e:
        log.error("Exception:TestSuiteBuilder().build:{} {}".format(casefile, e))
        return []
    except Exception as e:
        log.error("Exception:TestSuiteBuilder().build:{} {}".format(casefile, e))
        return []

    resources = []
    for i in suite.resource.imports:
        rsfile = i.name                    # Full path of file

        if rsfile.find("%{ROBOT_DIR}") != -1:
            rsfile = rsfile.replace("%{ROBOT_DIR}", projectdir)
        if rsfile.find("%{PROJECT_DIR}") != -1:
            rsfile = rsfile.replace("%{PROJECT_DIR}", projectdir)
        if rsfile.startswith('.'):
            dir = os.path.dirname(casefile)
            rsfile = os.path.join(dir, rsfile)

        basename = os.path.basename(rsfile)    # Lib name without path
        fpre = basename.split('.')[0]          # BuildIn or UserRes without '.resource' or '.robot'
        xmlfile = cwd + "/%s.xml" % fpre

        if not os.path.exists(rsfile) and (rsfile.find('/') != -1 or rsfile.find('.robot') != -1 or rsfile.find('.resource') != -1):
            log.error("找不到资源文件:{} !".format(rsfile))
            continue

        if os.path.exists(rsfile):
            res = generate_resource_xml(rsfile, xmlfile) if not os.path.exists(xmlfile) else None
            resources.append(fpre) if os.path.exists(xmlfile) else log.error(
                "生成资源文件失败 XML:{},INFO:{}".format(xmlfile, res))
        else:
            res = generate_resource_xml(fpre, xmlfile) if not os.path.exists(xmlfile) else None
            resources.append(fpre) if os.path.exists(xmlfile) else log.error(
                "生成资源文件失败 XML:{},INFO:{}".format(xmlfile, res))

        if rsfile.endswith('.robot') or rsfile.endswith('.resource'):
            resources += get_robotress_res(rsfile)

    return resources

def parser_robot_keyword_list(key):
    project = get_projectnamefromkey(key)
    cwd = os.getcwd() + "/keyword/" + project

    resources = ["BuiltIn"] + get_resource_list(key)
    resources = list(set(resources))
    resources.sort()

    keyword_list = []
    for k in resources:
        path = cwd + "/%s.xml" % k
        if not os.path.exists(path):
            generate_resource_xml(k, cwd + "/%s.xml" % k)
        tree = ET.parse(path)
        root = tree.getroot()
        name = root.attrib["name"]

        children = []
        for kw in root.iter("kw"):
            # 关键字
            keyword = kw.attrib["name"]

            # 关键字参数
            params = ""
            doc_params = []
            for arg in kw.iter("arg"):
                params += "\t[" + arg.text + "]"
                doc_params.append(arg.text)
            params += "\n"
            if len(doc_params) == 0:
                doc_params = "无"

            # 使用说明
            doc = kw.find("doc").text
            if doc is not None:
                doc_help = doc .replace("\n", "<br>").replace("\r\t", "<br>")
            else:
                doc_help = doc

            children.append({
                "id": keyword,
                "text": keyword,
                "iconCls": "icon-keyword",
                "attributes": {
                    "keyword": keyword,
                    "category": "keyword",
                    "params": params,
                    "doc": "<p>KeyWord: %s<br><br/>Lib: %s<br><br>Param: <br>%s<br><br>文档:<br>%s</p>" % (keyword, k, " | ".join(doc_params), doc_help)
                }
            })

        keyword_list.append({
            "id": name,
            "text": name,
            "state": "closed",
            "iconCls": "icon-keyword-list",
            "attributes": {"category": name},
            "children": children
        })

    return keyword_list


def parser(doc_dir):

    for k in USER_KEYS["all"]:
        keyword_list = []
        path = doc_dir + "/%s.xml" % k
        tree = ET.parse(path)
        root = tree.getroot()
        name = root.attrib["name"]

        for kw in root.iter("kw"):
            # 关键字
            keyword_list.append("'" + kw.attrib["name"] + "'")

        print("rf_" + name + "=[" + ",".join(keyword_list))

def generate_high_light(doc_dir):

    ''' This is new fun, Invoked by project.get ,then loaded in editor.html. '''

    log.info("生成高亮显示 js ...")
    project = get_projectnamefromkey(doc_dir)
    kwd = os.getcwd() + "/keyword/" + project
    jsd = os.getcwd() + "/auto/www/static/js/" + project
    if not os.path.exists(jsd):
        mk_dirs(jsd)
    if not os.path.exists(kwd):
        mk_dirs(kwd)

    ff = codecs.open(jsd + "/highlight.js", "w", "utf-8")
    keyword_list = []
    keys = os.listdir(kwd)
    for k in keys:
        if not k.endswith('.xml'):
            continue
        path = kwd + "/" + k
        tree = ET.parse(path)
        root = tree.getroot()
        name = root.attrib["name"]

        for kw in root.iter("kw"):
            # 关键字
            keyword_list.append("'" + kw.attrib["name"] + "'")

        keyword_list = list(set(keyword_list))
        keyword_list.sort(key=len, reverse=True)

    keywords = "var high_light=" + "[" + ",".join(keyword_list) + "];"
    ff.write(keywords)
    ff.close()


def generate_auto_complete(doc_dir):  # This is new fun, Invoked by project.get ,then loaded in editor.html.

    log.info("生成自动完成 js ...")

    project = get_projectnamefromkey(doc_dir)
    kwd = os.getcwd() + "/keyword/" + project
    jsd = os.getcwd() + "/auto/www/static/js/" + project
    if not os.path.exists(jsd):
        mk_dirs(jsd)
    if not os.path.exists(kwd):
        mk_dirs(kwd)

    ff = codecs.open(jsd + "/autocomplete.js", "w", "utf-8")
    keyword_list = []
    keys = os.listdir(kwd)
    for k in keys:
        if not k.endswith('.xml'):
            continue
        path = kwd + "/" + k
        tree = ET.parse(path)
        root = tree.getroot()
        name = root.attrib["name"]

        for kw in root.iter("kw"):
            # 关键字
            word = "'" + kw.attrib["name"]

            # 关键字参数
            for arg in kw.iter("arg"):
                word += "\t[" + arg.text.replace("'","") + "]"

            word += "'"

            keyword_list.append(word)
            keyword_list = list(set(keyword_list))
            keyword_list.sort(key=len, reverse=False)
            keyword_list = ROBOT_BUILTIN_KEYWORDS + keyword_list
    kewords = "var auto_complete=" + "[" + ",".join(keyword_list) + "];"
    ff.write(kewords)
    ff.close()

def generate_high_light_org(doc_dir):  # This is original fun, I don't think it is good to load all KEYS.
    ff = codecs.open(os.getcwd() + "/auto/www/static/js/highlight.js", "w", "utf-8")
    keyword_list = []
    keys = os.listdir(doc_dir)
    for k in keys:
        if not k.endswith('.xml'):
            continue
        path = doc_dir + "/" + k
        tree = ET.parse(path)
        root = tree.getroot()
        name = root.attrib["name"]

        for kw in root.iter("kw"):
            # 关键字
            keyword_list.append("'" + kw.attrib["name"] + "'")
    kewords = "var high_light=" + "[" + ",".join(keyword_list) + "];"
    ff.write(kewords)
    ff.close()


def generate_auto_complete_org(doc_dir):  # This is original fun, I don't think it is good to load all KEYS.
    ff = codecs.open(os.getcwd() + "/auto/www/static/js/autocomplete.js", "w", "utf-8")
    keyword_list = []
    for k in USER_KEYS["all"]:
        path = doc_dir + "/%s.xml" % k
        tree = ET.parse(path)
        root = tree.getroot()
        name = root.attrib["name"]

        for kw in root.iter("kw"):
            # 关键字
            word = "'" + kw.attrib["name"]

            # 关键字参数
            for arg in kw.iter("arg"):
                word += "\t[" + arg.text + "]"

            word += "'"

            keyword_list.append(word)

    kewords = "var auto_complete=" + "[" + ",".join(keyword_list) + "];"
    ff.write(kewords)
    ff.close()

def generate_resource_xml(srcfile, desfile):

    if not os.path.isfile(srcfile) and srcfile.endswith('.resource'):
        log.warning("无法生成 xml file of "+srcfile)
        return ''

    log.info("生成 xml file of :"+srcfile)

    try:
        cmd = 'python -m robot.libdoc -f xml ' + srcfile + ' ' + desfile
        cp = subRun(cmd, shell=True, stdout=PIPE, stderr=STDOUT, text=True, timeout=180)  # timeout: sec
    except SyntaxError as e:
        log.error("生成资源文件异常:{} {}".format(srcfile,e))
        return ''
    except Exception as e:
        log.error("生成资源文件异常:{} {}".format(srcfile,e))
        return ''

    return cp.stdout

def prepare_editorjs(key):
    project = get_projectnamefromkey(key)
    jsd = os.getcwd() + "/auto/www/static/js/" + project
    desd = os.getcwd() + "/auto/www/static/js"
    copy_file(jsd + '/highlight.js' , desd + '/highlight.js') if os.path.exists(jsd + '/highlight.js') else None
    copy_file(jsd + '/autocomplete.js', desd + '/autocomplete.js') if os.path.exists(jsd + '/autocomplete.js') else None

def update_resource(path):
    '''when update,rename,delete resource file, xml file should be updated.'''
    if not path.endswith('.resource'):
        log.error("更新资源文件应该已resource为后缀: "+path)
        return
    project = get_projectnamefromkey(path)

    fname = os.path.basename(path).split('.')[0]
    kwd = os.getcwd() + "/keyword/" + project

    kwdfile = kwd + '/' + fname + '.xml'
    os.remove(kwdfile) if os.path.isfile(kwdfile) else None

    generate_resource_xml(path, kwdfile)
    generate_high_light(path)
    generate_auto_complete(path)


if __name__ == "__main__":
    path = "/Users/tester/PycharmProjects/uniRobotDev/.beats/workspace/tbdsadmin/RobotTbds"
    generate_high_light(path)
    generate_auto_complete(path)
