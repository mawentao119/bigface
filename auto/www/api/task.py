# -*- coding: utf-8 -*-

__author__ = "苦叶子"
__modifier__ = "mawentao119@gmail.com"

"""

"""

from flask import current_app, session
from flask_restful import Resource, reqparse
import os
import time
from utils.mylogger import getlogger
import multiprocessing

from utils.file import remove_dir, get_splitext
from utils.run import robot_run, is_run, is_full, stop_robot, robot_debugrun, py_debugrun,bzt_debugrun
from utils.pytester import debug_pytest_run, pytest_run

class Task(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('method', type=str)
        self.parser.add_argument('category', type=str)
        self.parser.add_argument('project', type=str)
        self.parser.add_argument('suite', type=str)
        self.parser.add_argument('case', type=str)
        self.parser.add_argument('tags', type=str)
        self.parser.add_argument('conffile', type=str)
        self.parser.add_argument('apiuser', type=str)
        self.parser.add_argument('key', type=str)
        self.parser.add_argument('task_no', type=str)
        self.log = getlogger(__name__)
        self.app = current_app._get_current_object()

    def post(self):
        args = self.parser.parse_args()
        self.log.info("Request args:{}".format(args))

        if args["method"] == "runcasefile" or args["method"] == "editor_run":
            return self.run_case(args)
        elif args["method"] == "runpydir" or args["method"] == "runrfdir":
            return self.run_case(args)
        elif args["method"] == "debug_run":
            return self.debug_run(args)
        elif args["method"] == "debug_pytest":
            return self.debug_pytest(args)
        elif args["method"] == "runpass":
            return self.runpassfail(args,True)
        elif args["method"] == "runfail":
            return self.runpassfail(args,False)
        elif args["method"] == "runtags":
            return self.runtags(args)
        elif args["method"] == "runfile":
            return self.runfile(args)

        elif args["method"] == "rerun":
            return self.rerun_task(args)
        elif args["method"] == "rerunfail":
            return self.rerunfail_task(args)

        elif args["method"] == "stop":
            return stop_robot(self.app, args)

        elif args["method"] == "delete":
            delete_task_record(self.app, args)
            return {"status": "success", "msg": "删除成功."}
        else:
            return {"status": "fail", "msg": "Parameter 'method' Error:{}".format(args['method'])}

    def run_case(self, args):
        """
        使用 multiprocessing Process 进行后台任务的执行
        兼容问题：在 Mac上运行会引起 app 多次重启，只要调用就会重启
        在 centos 上运行不会，参见：https://docs.python.org/3/library/multiprocessing.html ：Contexts and start methods
        :param args:
        :return:
        """
        method = args['method']  # runcasefile , editor_run , runpydir ,runrfdir
        cases = args['key']
        case_name = os.path.basename(cases)
        user = session["username"]
        self.log.info("运行：method：{} , key: {}".format(method, cases))
        #multiprocessing.set_start_method('spawn')   # Todo : Mac兼容问题需要解决
        if os.path.isdir(cases):
            if method == "runpydir":

                if not is_run(self.app, case_name):
                    self.log.info("pytest_run: {}".format(cases))
                    p = multiprocessing.Process(target=pytest_run, args=(cases, '', user))
                    p.start()
                    self.app.config["AUTO_ROBOT"].append(
                        {"name": "%s" % case_name, "process": p})
                    return {"status": "success", "msg": "运行:" + case_name}
                else:
                    return {"status": "fail", "msg": "失败：超过最大进程数，请等待."}

            elif method == "runrfdir":
                if not is_run(self.app, case_name):
                    self.log.info("robot_run:{}".format(cases))
                    p = multiprocessing.Process(target=robot_run, args=(cases, '', user))
                    p.start()
                    self.app.config["AUTO_ROBOT"].append(
                        {"name": "%s" % case_name, "process": p})
                    return {"status": "success", "msg": "运行:" + case_name}
                else:
                    return {"status": "fail", "msg": "失败：超过最大进程数，请等待."}

            else:
                return {"status": "fail", "msg": "无法理解的参数:{}" + method}

        fext = get_splitext(cases)[1]
        if not is_run(self.app, case_name):
            if fext == ".robot":
                self.log.info("robot_run:{}".format(cases))
                p = multiprocessing.Process(target=robot_run, args=(cases, '', user))
            elif fext ==".py":
                self.log.info("pytest_run: {}".format(cases))
                p = multiprocessing.Process(target=pytest_run, args=(cases, '', user))
            else:
                return {"status": "fail", "msg": "暂不支持运行此类文件:{}" + fext}
            p.start()
            self.app.config["AUTO_ROBOT"].append(
                {"name": "%s" % case_name, "process": p})
            return {"status": "success", "msg": "运行:" + case_name}
        else:
            return {"status": "fail", "msg": "失败：超过最大进程数，请等待."}

    def runpassfail(self, args, passed=True):

        suites = []
        retry = 0
        if passed:
            sql = ''' SELECT distinct(info_key) FROM testcase WHERE info_key like '{}%' and run_status='PASS' ;
                  '''.format(args['key'])
        else:
            sql = ''' SELECT distinct(info_key) FROM testcase WHERE info_key like '{}%' and run_status='FAIL' ;
                  '''.format(args['key'])

        res = self.app.config['DB'].runsql(sql)
        for r in res:
            (s,) = r
            suites.append(s)

        self.log.info("runpassfail: total suites is :{}".format(len(suites)))
        runuser = session["username"]
        for key in suites:
            case_name = os.path.basename(key)
            if is_full(self.app):
                return {"status": "fail", "msg": "失败：超过最大进程数 MAX_PROCS ,请稍后尝试."}
            if not is_run(self.app, case_name):
                p = multiprocessing.Process(target=robot_run,
                                            args=(key, '', runuser))
                p.start()
                self.app.config["AUTO_ROBOT"].append(
                    {"name": "%s" % case_name, "process": p})

                time.sleep(0.2)

            else:
                retry += 1
        if retry > 0 :
            return {"status": "success", "msg": "运行:{} 用例冲突，需要重试.".format(retry)}
        else:
            return {"status": "success", "msg": "开始运行:" + args['key']}

    def runtags(self, args):
        arg_tags = args['tags']
        key = args['key']

        tags = arg_tags.replace('，',',').split(',')

        includ = []
        exclud = []

        for t in tags:
            if t.strip().startswith('-'):
                exclud.append(t.strip().replace('-',''))
            else:
                includ.append(t.strip().replace('+',''))

        includ_arg = ' -i '+ ' -i '.join(includ) if len(includ) > 0 else ''
        exclud_arg = ' -e '+ ' -e '.join(exclud) if len(exclud) > 0 else ''

        case_name = os.path.basename(key)
        runuser = session["username"]
        if not is_run(self.app, case_name):
            p = multiprocessing.Process(target=robot_run,
                                        args=(key, includ_arg + exclud_arg, runuser))
            p.start()
            self.app.config["AUTO_ROBOT"].append(
                {"name": "%s" % case_name, "process": p})
        else:
            return {"status": "fail", "msg": "请等待前面的任务运行完成."}

        return {"status": "success", "msg": "开始运行:" + case_name}

    def runfile(self, args):
        conffile = args['conffile'].strip()
        key = args['key']

        projectdir = os.environ["PROJECT_DIR"]
        conffile = conffile.replace('${ROBOT_DIR}',projectdir)
        conffile = conffile.replace('${PROJECT_DIR}', projectdir)
        conffile = conffile.replace('%{ROBOT_DIR}', projectdir)
        conffile = conffile.replace('%{PROJECT_DIR}', projectdir)

        if not conffile.strip().startswith('/'):
            conffile = os.path.join( key, conffile )

        if not os.path.isfile(conffile):
            return {"status": "fail", "msg": "无法找到配置文件:{}".format(conffile)}

        case_name = os.path.basename(key)
        runuser = session["username"]
        if not is_run(self.app, case_name):
            p = multiprocessing.Process(target=robot_run,
                                        args=(key, ' -A '+conffile, runuser))
            p.start()
            self.app.config["AUTO_ROBOT"].append(
                {"name": "%s" % case_name, "process": p})
        else:
            return {"status": "fail", "msg": "请等待前面的任务运行完成."}

        return {"status": "success", "msg": "开始运行:{}".format(conffile)}

    def debug_run(self, args):
        fext = os.path.splitext(args['key'])[1]

        is_api = False

        user = "unknown"
        if session.get("username"):
            user = session['username']
        if args.get('apiuser'):
            user = args['apiuser']
            is_api = True

        if fext == ".robot":
            result = robot_debugrun(self.app, args['key'], user, is_api)
            return {"data": decorate_robotout(result)}
        if fext == ".py":
            result = py_debugrun(self.app, args['key'], user, is_api)
            return {"data": decorate_pyout(result)}
        if fext == ".yaml":
            result = bzt_debugrun(self.app, args['key'], user, is_api)
            return {"data": decorate_pyout(result)}
        return {"data": "暂不支持运行此类文件 <{}> .".format(fext)}

    def debug_pytest(self, args):

        is_api = False
        user = "unknown"
        if session.get("username"):
            user = session['username']
        if args.get('apiuser'):
            user = args['apiuser']
            is_api = True

        fext = os.path.splitext(args['key'])[1]
        if not fext == ".py":
            return {"data": "pytest不支持运行此类文件:{}.".format(fext)}
        result = debug_pytest_run(args['key'], user, is_api)
        return {"data": decorate_pytestout(result)}

    def rerun_task(self, args):
        project = args['project']
        task_no = args['task_no']
        cmdfile = self.app.config["AUTO_HOME"] + "/jobs/%s/%s/%s/cmd.txt" % (session['username'], project,str(task_no))
        if not os.path.isfile(cmdfile):
            return {"status": "fail", "msg": "无法找到命令文件:{}".format(cmdfile)}

        cmdline = ''
        with open(cmdfile,'r') as f:
            cmdline = f.readline()

        cmdline = cmdline.strip()
        if cmdline == '':
            return {"status": "fail", "msg": "命令文件为空."}

        self.log.info("rerun_task CMD:"+cmdline)

        splits = cmdline.split('|')

        cases = splits[-1]    # driver|robot|args|output=xxx|cases
        args = splits[2]
        case_name = os.path.basename(cases)
        runuser = session["username"]
        if not is_run(self.app, case_name):
            p = multiprocessing.Process(target=robot_run,
                                        args=(cases, args, runuser))
            p.start()
            self.app.config["AUTO_ROBOT"].append(
                {"name": "%s" % case_name, "process": p})
        else:
            return {"status": "fail", "msg": "请等待前面的任务运行完成."}

        return {"status": "success", "msg": "重新运行 {}:{}".format(project,task_no)}

    def rerunfail_task(self, args):
        """
        重新执行失败suite ：-S --rerunfailedsuites output ，而不是 -R --rerunfailed output tests
        Rerun failed suite: See robot user guide : -S  not -R
        :param args:
        :return:
        """
        project = args['project']
        task_no = args['task_no']
        cmdfile = self.app.config["AUTO_HOME"] + "/jobs/%s/%s/%s/cmd.txt" % (session['username'], project,str(task_no))
        outfile = self.app.config["AUTO_HOME"] + "/jobs/%s/%s/%s/output.xml" % (session['username'], project,str(task_no))
        if not os.path.isfile(cmdfile):
            return {"status": "fail", "msg": "无法找到命令文件:{}".format(cmdfile)}
        if not os.path.isfile(outfile):
            return {"status": "fail", "msg": "无法找到历史结果文件:{}".format(outfile)}

        cmdline = ''
        with open(cmdfile,'r') as f:
            cmdline = f.readline()

        cmdline = cmdline.strip()
        if cmdline == '':
            return {"status": "fail", "msg": "命令文件为空."}

        splits = cmdline.split('|') # driver|robot|args|output=xxx|cases
        cases = splits[-1]
        args = splits[2] + ' -S ' + outfile
        case_name = os.path.basename(cases)

        self.log.info("rerunfail_task args:" + args)
        runuser = session["username"]
        if not is_run(self.app, case_name):
            p = multiprocessing.Process(target=robot_run,
                                        args=(cases, args, runuser))
            p.start()
            self.app.config["AUTO_ROBOT"].append(
                {"name": "%s" % case_name, "process": p})
        else:
            return {"status": "fail", "msg": "请等待前面的任务运行完成."}

        return {"status": "success", "msg": "运行场景失败用例 {}:{}".format(project,task_no)}

def delete_task_record(app, args):
    project = args['project']
    task_no = args['task_no']
    task_path = app.config["AUTO_HOME"] + "/jobs/%s/%s/%s" % (session['username'], project, str(task_no))

    if os.path.exists(task_path):
        remove_dir(task_path)


# For debug out, it is shown as html ,so we can decorate it for more readable.
def decorate_robotout(out):
    o = out.replace(' PASS ', '<b><font color="#00FF00">PASS</font></b>')
    o = o.replace(' ERROR ', '<b><font color="#FF0000">ERROR</font></b>')
    o = o.replace(' FAIL ', '<b><font color="#FF0000">FAIL</font></b>')
    o = o.replace('\n', '<BR>')
    return o


def decorate_pyout(out):
    o = out.replace('TypeError', '<b><font color="#FF0000">TypeError</font></b>')
    o = o.replace('\n', '<BR>')
    return o


def decorate_pytestout(out):
    o = out.replace('<td>passed</td>', '<td><font color="#00FF00">passed</font></td>')
    o = o.replace('<td>failed</td>', '<td><font color="#FF0000">failed</font></td>')
    o = o.replace('<td>skipped</td>', '<td><font color="#0000FF">skipped</font></td>')
    return o
