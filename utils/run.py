# -*- coding: utf-8 -*-

__author__ = "mawentao119@gmail.com"

"""

"""
import os
import codecs
from flask import current_app, session, url_for
import threading
from subprocess import run as subRun, PIPE ,STDOUT
import time
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import json

from robot.api import TestSuiteBuilder, ResultWriter, ExecutionResult    # done
from utils.file import exists_path, make_nod, write_file, read_file, mk_dirs, get_rand_name
from utils.dbclass import DBcli

from utils.mylogger import getlogger

log = getlogger(__name__)
db_cli = DBcli(os.environ["DB_FILE"])

# function for api run test case
def api_rf(args):

    case_file = args.get("key")
    if not case_file:
        return {"result": "ParameterError", "msg": "need parameter:key"}

    if case_file.find("${PROJECT_DIR}") != -1:
        case_file = case_file.replace("${PROJECT_DIR}", os.environ.get("PROJECT_DIR"))
    if case_file.find("${PROJECT}") != -1:
        case_file = case_file.replace("${PROJECT}", os.environ.get("PROJECT_DIR"))

    if not os.path.exists(case_file):
        return {"result": "ParameterError", "msg": "file not found:{}".format(case_file)}

    if not args.get("apiuser"):
        return {"result": "ParameterError", "msg": "need parameter:apiuser"}

    basedir = os.environ.get("API_RUN_DIR")
    if not basedir:
        return {"result": "SystemError", "msg": "cannot find ${API_RUN_DIR}"}

    case_style = True
    case = args.get("case")
    if not case:
        case_style = False

    user = args.get("apiuser")
    jobid = get_rand_name()
    outputdir = os.path.join(basedir, jobid)
    mk_dirs(outputdir) if not os.path.exists(outputdir) else None

    log.info("user:{} ,RF key:{}, case:{} ,outputdir:{}".format(user, case_file, case, outputdir))

    if case_style:
        ext_args = "--test " + case
    else:
        ext_args = ""

    cmd = 'robot ' + ext_args + ' --outputdir=' + outputdir + ' ' + case_file

    log.info("CMD:{}".format(cmd))
    with open(outputdir + "/cmd.txt", 'w') as f:
        f.write("{}|robot|{}|--outputdir={}|{}\n".format("api_rf", ext_args, outputdir, case_file))

    cp = subRun(cmd, shell=True, stdout=PIPE, stderr=STDOUT, text=True, timeout=7200)  # timeout: sec 2hrs

    with open(outputdir + "/debug.txt", 'w') as f:
        f.write(cp.stdout)

    db_cli.insert_loginfo(user, 'task', 'api_rf', case_file, 'OK')

    try:

        detail_result = ExecutionResult(outputdir + "/output.xml")

    except Exception as e:
        log.error("Open output.xml Exception:{},\n May robot run fail, console:{}".format(e, cp.stdout))
        return

    # Report and xUnit files can be generated based on the result object.
    ResultWriter(detail_result).write_results(report=outputdir + '/report.html', log=outputdir + '/log.html')
    logfile = os.path.join(jobid, "log.html")
    rptfile = os.path.join(jobid, "report.html")

    s = detail_result.suite

    #source = s.source
    success = 0
    fail = 0
    if os.path.isfile(s.source):
        for t in s.tests._items:
            tags = ",".join(t.tags)
            success += 1 if t.status == 'PASS' else 0
            fail += 1 if t.status == 'FAIL' else 0
        result = {"result": "[  PASSED  ]" if fail == 0 else "[  FAILED  ]",
                  "passed": success, "failed": fail,
                  "log": "/api_report/" + logfile, "report": "/api_report/" + rptfile}
        return result

    return {"result": "[  PASSED  ]", "msg": "Not a dir:{}".format(s.source)}

# This fun is for debug the test case, result is temporliy in /runtime dir
def robot_debugrun(app, cases, user="unknown", is_api=False):

    out = app.config['AUTO_TEMP']
    if not exists_path(out):
        mk_dirs(out)

    cmd = 'robot --outputdir='+out+' '+cases
    cp = subRun(cmd, shell=True, stdout=PIPE,stderr=STDOUT, text=True, timeout=300)  # timeout: sec

    app.config['DB'].insert_loginfo(user, 'case', 'debug', cases, 'OK')

    return cp.stdout

# This fun is for standard Run, Result will be recorded in Scheduler output.
def robot_run(case_key, args='', user='', catigory=''):

    username = user if user != '' else 'unknown'
    driver = catigory if catigory != '' else username

    project = os.environ["PROJECT_NAME"]
    output = os.environ["AUTO_HOME"] + "/jobs/%s/%s" % (username, project)

    if not exists_path(output):
        mk_dirs(output)

    (out, index) = reset_next_build_numb(output)

    mk_dirs(out) if not exists_path(out) else None

    cmd = 'robot ' + args + ' --outputdir=' + out + ' ' + case_key

    log.info("Robot_run CMD:{}".format(cmd))
    with open(out + "/cmd.txt", 'w') as f:
        f.write("{}|robot|{}|--outputdir={}|{}\n".format(driver, args,out,case_key))

    cp = subRun(cmd, shell=True, stdout=PIPE, stderr=STDOUT, text=True, timeout=7200)  # timeout: sec 2hrs

    with open(out + "/debug.txt", 'w') as f:
        f.write(cp.stdout)

    db_cli.insert_loginfo(username, 'task', 'run', case_key, 'OK')

    # Report and xUnit files can be generated based on the result object.
    # ResultWriter(result).write_results(report=out + '/report.html', log=out + '/log.html')
    try:

        detail_result = ExecutionResult(out + "/output.xml")

    except Exception as e:
        log.error("Open output.xml Exception:{},\n May robot run fail, console:{}".format(e, cp.stdout))
        return

    # detail_result.save(out + "/output_new.xml")
    reset_last_status(detail_result, output, index)

    # Report and xUnit files can be generated based on the result object.
    ResultWriter(detail_result).write_results(report=out + '/report.html', log=out + '/log.html')

    s = detail_result.suite
    dealwith_source(username, s)

    #send_robot_report(username, project, index, detail_result, out)

def robot_runOLD(app, username, project, case_key, output):
    if not exists_path(output):
        mk_dirs(output)

    suite = TestSuiteBuilder().build(case_key)

    (out, index) = reset_next_build_numb(output)

    result = suite.run(output_directory=out,
                       output=out + "/output.xml",
                       debugfile=out + "/debug.txt",
                       loglevel="TRACE")

    try:
        totalcases = result.statistics.total.total
        passed = result.statistics.total.passed
        failed = result.statistics.total.failed
        elapsedtime = result.suite.elapsedtime
        logres = "total:{},pass:{},fail:{},elapsedtime:{}".format(totalcases,passed,failed,elapsedtime)
        app.config['DB'].insert_loginfo(username,'task','run', case_key, logres)
    except Exception as e:
        log.error("robot_run Exception: {}".format(e))

    # Report and xUnit files can be generated based on the result object.
    # ResultWriter(result).write_results(report=out + '/report.html', log=out + '/log.html')
    detail_result = ExecutionResult(out + "/output.xml")

    # detail_result.save(out + "/output_new.xml")
    reset_last_status(detail_result, output, index)

    # Report and xUnit files can be generated based on the result object.
    ResultWriter(detail_result).write_results(report=out + '/report.html', log=out + '/log.html')

    s = detail_result.suite
    dealwith_source(username, s)

    send_robot_report(username, project, index, detail_result, out)

def dealwith_source(username ,s):

    source = s.source
    if os.path.isfile(s.source):

        db_cli.insert_loginfo(username,'suite','run',s.source,'OK')

        for t in s.tests._items:
            if 'HAND' in t.tags or 'Hand' in t.tags or 'hand' in t.tags:
                log.info("Do not record Hand case status:"+t.name)
                continue
            tags = ",".join(t.tags)
            success = 1 if t.status == 'PASS' else 0
            fail = 1 if t.status == 'FAIL' else 0
            sql = '''UPDATE testcase set ontime=datetime('now','localtime'),
                                       run_elapsedtime='{}',
                                       run_status='{}', 
                                       run_starttime='{}', 
                                       run_endtime='{}', 
                                       info_doc='{}', 
                                       info_tags='{}',
                                       run_user='{}',
                                       rcd_runtimes=rcd_runtimes+1,
                                       rcd_successtimes=rcd_successtimes+{},
                                       rcd_failtimes=rcd_failtimes+{}
                            where info_key='{}' and info_name='{}' ;
            '''.format(t.elapsedtime,t.status,t.starttime,t.endtime,t.doc,tags,username,success,fail,source,t.name)
            res = db_cli.runsql(sql)

            db_cli.insert_loginfo(username, 'case', 'run', source, t.status)

            if res.rowcount < 1 :
                log.warning("Cannot find case:{}:{}, Insert it ...".format(source,t.name))
                sql = '''INSERT INTO testcase(run_elapsedtime,
                                              run_status, 
                                              run_starttime, 
                                              run_endtime, 
                                              info_doc, 
                                              info_tags,
                                              run_user,
                                              rcd_runtimes,
                                              rcd_successtimes,
                                              rcd_failtimes,
                                              info_key,
                                              info_name) 
                         VALUES({},'{}','{}','{}','{}','{}','{}',{},{},{},'{}','{}');
                            '''.format(t.elapsedtime, t.status, t.starttime, t.endtime, t.doc, tags, username, 1,success,fail, source, t.name)
                res = db_cli.runsql(sql)
                if res.rowcount < 1 :
                    log.error("Add New Case:{}:{} Failed".format(source,t.name))

                db_cli.insert_loginfo(username,'case','create',source,'robot_run:'+t.name)
    else:
        for t in s.suites._items:
            dealwith_source(username, t)

def reset_next_build_numb(output):
    next_build_number = output + "/nextBuildNumber"
    index = 1
    data = "%d" % (index + 1)
    if not exists_path(next_build_number):
        make_nod(next_build_number)
    else:
        index = int(read_file(next_build_number)["data"])
        data = "%d" % (index + 1)
    write_file(next_build_number, data)

    out = output + "/%d" % index
    if not exists_path(output):
        mk_dirs(output)

    return (out, index)


def reset_last_status(result, output, index):
    stats = result.statistics
    fail = stats.total.failed

    last_fail = output + "/lastFail"
    last_passed = output + "/lastPassed"
    data = "%d" % index

    if fail != 0:
        if not exists_path(last_fail):
            make_nod(last_fail)

        write_file(last_fail, data)
    else:
        if not exists_path(last_passed):
            make_nod(last_passed)
        write_file(last_passed, data)

def remove_robot(app):
    lock = threading.Lock()
    lock.acquire()
    for p in app.config["AUTO_ROBOT"]:
        if not p["process"].is_alive():
            app.config["AUTO_ROBOT"].remove(p)
            break
    lock.release()


def stop_robot(app, args):
    lock = threading.Lock()
    lock.acquire()
    project = args['project']
    task_no = args['task_no']
    cmdfile = app.config["AUTO_HOME"] + "/jobs/%s/%s/%s/cmd.txt" % (session['username'], project, str(task_no))
    if not os.path.isfile(cmdfile):
        return {"status": "fail", "msg": "Cannot find command，Command File maybe deleted:{}".format(cmdfile)}

    cmdline = ''
    with open(cmdfile, 'r') as f:
        cmdline = f.readline()

    cmdline = cmdline.strip()
    if cmdline == '':
        return {"status": "fail", "msg": "Containt of Command file is null. "}

    log.info("stop_task CMD:" + cmdline)

    splits = cmdline.split('|')

    cases = splits[-1]                # driver|robot|args|output=xxx|cases
    name = os.path.basename(cases)

    for p in app.config["AUTO_ROBOT"]:
        if name == p["name"]:
            if p["process"].is_alive():
                p["process"].terminate()
                time.sleep(0.2)
                app.config["AUTO_ROBOT"].remove(p)
                break

    lock.release()

    return {"status": "success", "msg": "Stoped!"}


def is_run(app, name):
    remove_robot(app)
    for p in app.config["AUTO_ROBOT"]:
        if name == p["name"]:
            return True

    return False

def is_full(app):
    remove_robot(app)
    max = app.config['DB'].get_setting('MAX_PROCS')
    if max == 'unknown' or max == '' or (not max):
        max_procs = 20
    else:
        max_procs = int(max)
    return len(app.config["AUTO_ROBOT"]) > max_procs


def send_robot_report(username, name, task_no, result, output):
    app = current_app._get_current_object()
    build_msg = "<font color='green'>Success</font>"
    if result.statistics.total.failed != 0:
        build_msg = "<font color='red'>Failure</font>"

    report_url = url_for("routes.q_view_report",
                         _external=True,
                         username=username,
                         project=name,
                         task=task_no)
    msg = MIMEText("""Hello, %s<hr>
                Projct：%s<hr>
                No.: %s<hr>
                Status: %s<hr>
                Duration: %s毫秒<hr>
                ReportDetail: <a href='%s'>%s</a><hr>
                Log: <br>%s<hr><br><br>
                (This Mail is Auto-sent by System，Please do not response ！)""" %
                   (username,
                    result.statistics.suite.stat.name,
                    task_no,
                    build_msg,
                    result.suite.elapsedtime,
                    report_url, report_url,
                    codecs.open(output + "/debug.txt", "r", "utf-8").read().replace("\n", "<br>")
                    ),
                   "html", "utf-8")

    msg["Subject"] = Header("uniRobot Execution Report", "utf-8")

    try:
        user_path = app.config["AUTO_HOME"] + "/users/%s/config.json" % session["username"]
        user_conf = json.load(codecs.open(user_path, 'r', 'utf-8'))
        for p in user_conf["data"]:
            if p["name"] == name:
                if result.statistics.total.failed != 0:
                    msg["To"] = p["fail_list"]
                else:
                    msg["To"] = p["success_list"]
                break

        conf_path = app.config["AUTO_HOME"] + "/auto.json"
        config = json.load(codecs.open(conf_path, 'r', 'utf-8'))
        msg["From"] = config["smtp"]["username"]
        if config["smtp"]["ssl"]:
            smtp = smtplib.SMTP_SSL()
        else:
            smtp = smtplib.SMTP()

        # 连接至服务器
        smtp.connect(config["smtp"]["server"], int(config["smtp"]["port"]))
        # 登录
        smtp.login(config["smtp"]["username"], config["smtp"]["password"])
        # 发送邮件
        smtp.sendmail(msg["From"], msg["To"].split(","), msg.as_string().encode("utf8"))
        # 断开连接
        smtp.quit()
    except Exception as e:
        print("Send Mail Failed: %s" % e)


class RobotRun(threading.Thread):
    def __init__(self, name, output, lock, executor="auto"):
        threading.Thread.__init__(self)
        self.lock = lock
        self.project = name
        self.output = output
        self.executor = executor
        self.suite = None
        self.result = None

    def run(self):
        #lock = threading.Lock()

        # self.lock.acquire()
        if not exists_path(self.output):
            mk_dirs(self.output)

        self.suite = TestSuiteBuilder().build(self.project)

        (output, index) = self.reset_next_build_numb()

        self.setName(output)

        self.result = self.suite.run(output_directory=output,
                                     output=output + "/output.xml",
                                     debugfile=output + "/debug.txt",
                                     loglevel="TRACE")

        # self.reset_last_status(index)

        # Report and xUnit files can be generated based on the result object.
        # ResultWriter(self.result).write_results(report=output + '/report.html', log=output + '/log.html')

        # self.lock.release()

        # Generating log files requires processing the earlier generated output XML.
        # ResultWriter(self.output + '/output.xml').write_results()

        self.result = ExecutionResult(output + "/output.xml")

        self.reset_last_status(self.result, output, index)

        # Report and xUnit files can be generated based on the result object.
        ResultWriter(self.result).write_results(report=output + '/report.html', log=output + '/log.html')

    def reset_next_build_numb(self):

        next_build_number = self.output + "/nextBuildNumber"
        index = 1
        data = "%d" % (index + 1)
        if not exists_path(next_build_number):
            make_nod(next_build_number)
        else:
            index = int(read_file(next_build_number)["data"])
            data = "%d" % (index + 1)
        write_file(next_build_number, data)

        output = self.output + "/%d" % index
        if not exists_path(output):
            mk_dirs(output)

        return (output, index)

    def reset_last_status(self, index):
        stats = self.result.statistics
        fail = stats.total.failed

        lock = threading.Lock()

        lock.acquire()
        last_fail = self.output + "/lastFail"
        last_passed = self.output + "/lastPassed"
        data = "%d" % index

        if fail != 0:
            if not exists_path(last_fail):
                make_nod(last_fail)

            write_file(last_fail, data)
        else:
            if not exists_path(last_passed):
                make_nod(last_passed)
            write_file(last_passed, data)

        lock.release()


def py_debugrun(app, pyfile, user="unknown", is_api=False):
    cmd = 'python ' + pyfile
    cp = subRun(cmd, shell=True, stdout=PIPE, stderr=STDOUT, text=True, timeout=120)  # timeout: sec

    app.config['DB'].insert_loginfo(user, 'lib', 'debug', pyfile, 'OK')

    return cp.stdout


def bzt_debugrun(app, yamlfile, user="unknown", is_api=False):

    cmd = 'bzt ' + yamlfile
    cp = subRun(cmd, shell=True, stdout=PIPE, stderr=STDOUT, text=True, timeout=180)  # timeout: sec

    app.config['DB'].insert_loginfo(user, 'case', 'debug', yamlfile, 'OK')

    return cp.stdout
