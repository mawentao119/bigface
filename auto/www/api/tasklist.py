# -*- coding: utf-8 -*-

__author__ = "苦叶子"
__modifier__ = "mawentao119@gmail.com"

"""

"""

from flask import current_app, session, url_for
from flask_restful import Resource, reqparse
import json
import os
import codecs
import threading
from dateutil import tz

from robot.api import ExecutionResult

from utils.file import exists_path
from utils.run import remove_robot, robot_job
from ..app import scheduler
from utils.mylogger import getlogger
from utils.schedule import add_schedulejob

class TaskList(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('method', type=str)
        self.parser.add_argument('project', type=str)
        self.parser.add_argument('task_name', type=str)
        self.parser.add_argument('schedule_type', type=str)
        self.parser.add_argument('year', type=str)
        self.parser.add_argument('mon', type=str)
        self.parser.add_argument('day', type=str)
        self.parser.add_argument('hour', type=str)
        self.parser.add_argument('min', type=str)
        self.parser.add_argument('sec', type=str)
        self.parser.add_argument('week', type=str)
        self.parser.add_argument('day_of_week', type=str)
        self.parser.add_argument('start_date', type=str)
        self.parser.add_argument('end_date', type=str)
        self.log = getlogger("TaskList")
        self.app = current_app._get_current_object()

    def get(self):
        args = self.parser.parse_args()
        if args['method'] == 'get_tasklist':
            project = args["project"]
            return get_task_list(self.app, session['username'], project)
        if args['method'] == 'get_schedulejoblist':
            return get_schedulejob_list(self.app, args)

    def post(self):
        args = self.parser.parse_args()
        job_id = "%s_%s" % (session["username"], args["project"])
        if args["method"] == "get_projecttask":
            return get_projecttask(self.app)
        elif args["method"] == "start":
            result = {"status": "success", "msg": "Scheduler start success."}
            lock = threading.Lock()
            lock.acquire()
            job = scheduler.get_job(job_id)
            if job:
                scheduler.remove_job(job_id)
            cron = args["cron"].replace("\n", "").strip().split(" ")
            if args["cron"] != "* * * * * *" and len(cron) == 6:
                scheduler.add_job(id=job_id,
                                  name=args["project"],
                                  func=robot_job,
                                  args=(self.app, args["project"], session["username"]),
                                  trigger="cron",
                                  second=cron[0],
                                  minute=cron[1],
                                  hour=cron[2],
                                  day=cron[3],
                                  month=cron[4],
                                  day_of_week=cron[5])
            else:
                result["msg"] = "cron default * * * * * *, <br><br>Cannot start scheduler，Please modify cron setting."
            lock.release()
            return result

        elif args["method"] == "stop":
            lock = threading.Lock()
            lock.acquire()
            job = scheduler.get_job(job_id)
            if job:
                scheduler.remove_job(id=job_id)
            lock.release()
            return {"status": "success", "msg": "Stop task OK"}
        elif args["method"] == "edit":

            result = edit_cron(self.app, args["project"], args["cron"])
            if result:
                # job_id = "%s_%s" % (session["username"], args["project"])
                lock = threading.Lock()
                lock.acquire()
                job = scheduler.get_job(job_id)
                if job:
                    scheduler.remove_job(job_id)

                cron = args["cron"].replace("\n", "").strip().split(" ")
                if args["cron"] != "* * * * * *" and len(cron) == 6:
                    scheduler.add_job(id=job_id,
                                      name=args["project"],
                                      func=robot_job,
                                      args=(self.app, args["project"], session["username"]),
                                      trigger="cron",
                                      second=cron[0],
                                      minute=cron[1],
                                      hour=cron[2],
                                      day=cron[3],
                                      month=cron[4],
                                      day_of_week=cron[5])
                lock.release()

            return {"status": "success", "msg": "Edit cron info OK."}

        elif args["method"] == "add_schedulejob":
            user = session["username"]
            self.log.info("add_schedulejob, args:{}".format(args))

            splits = args["task_name"].split('_#')  # Project_#03Variables_#36
            if len(splits) != 3:
                return {"status": "fail", "msg": "任务名称的格式错误:{}".format(args["task_name"])}

            (project, task_name, task_no) = splits

            myargs = {'user': user,
                      'project':project,
                      'task_no':task_no,
                      'task_name': task_name,
                      'method': args['method'],
                      'schedule_type': args['schedule_type'],
                      'year': args['year'],
                      'mon': args['mon'],
                      'day': args['day'],
                      'hour': args['hour'],
                      'min': args['min'],
                      'sec': args['sec'],
                      'week': args['week'],
                      'day_of_week': args['day_of_week'],
                      'start_date': args['start_date'],
                      'end_date': args['end_date']}

            if self.app.config['DB'].add_chedulejob(myargs,'user'):
                return add_schedulejob(self.app, scheduler, myargs)
            else:
                return {"status": "fail", "msg": "Fail：添加调度任务失败，插入数据库失败。"}

def get_task_list(app, username, project):
    job_path = app.config["AUTO_HOME"] + "/jobs/%s/%s" % (username, project)
    next_build = 0
    task = []
    if exists_path(job_path):
        next_build = get_next_build_number(job_path)
        if next_build != 0:
            # 遍历所有任务结果
            # 判断最近一个任务状态
            icons = {
                "running": url_for('static', filename='img/running.gif'),
                "success": url_for('static', filename='img/success.png'),
                "fail": url_for('static', filename='img/fail.png'),
                "exception": url_for('static', filename='img/exception.png')}

            #if exists_path(job_path + "/%s" % (next_build - 1)):
            running = False
            lock = threading.Lock()
            lock.acquire()
            remove_robot(app)
            for p in app.config["AUTO_ROBOT"]:
                if p["name"] == project:
                    running = True
                    break
            lock.release()
            if running:
                task.append(
                   {
                       "status": icons["running"],
                       "name": "%s_#%s" % (project, next_build-1),
                       "success": "",
                       "fail": ""
                   }
                )
            last = 1
            if running:
                last = 2
            for i in range(next_build-last, -1, -1):
                if exists_path(job_path + "/%s" % i):
                    try:
                        driver = get_taskdriver(job_path + "/%s/cmd.txt" % i)
                        suite = ExecutionResult(job_path + "/%s/output.xml" % i).suite
                        stat = suite.statistics.critical
                        name = suite.name
                        if stat.failed != 0:
                            status = icons["fail"]
                        else:
                            status = icons['success']
                        task.append({
                            "task_no": i,
                            "status": status,
                            "name": "<a href='/view_report/%s/%s_log' target='_blank'>%s_#%s_log</a>" % (project, i, name, i),
                            "driver": driver,
                            "success": stat.passed,
                            "fail": stat.failed,
                            "starttime": suite.starttime,
                            "endtime": suite.endtime,
                            "elapsedtime": suite.elapsedtime,
                            "note": "<a href='/view_report/%s/%s_report' target='_blank'>%s_#%s_report</a>" % (project, i, name, i)
                        })
                    except:
                        status = icons["exception"]
                        if i == next_build-last:
                            status = icons["running"]
                        task.append({
                            "task_no": i,
                            "status": status,
                            "name": "%s_#%s" % (project, i),
                            "driver":driver,
                            "success": "-",
                            "fail": "-",
                            "starttime": "-",
                            "endtime": "-",
                            "elapsedtime": "-",
                            "note": "Abnormal"
                        })

    return {"total": next_build-1, "rows": task}

def get_schedulejob_list(app, args):

    joblist = []
    res = app.config['DB'].runsql('SELECT * from schedule_job;')
    for i in res:
        (user,project,task_no,task_name,method,schedule_type,
         year,mon,day,hour,min,sec,week,
         day_of_week,start_date,end_date,sponsor) = i

        joblist.append([user,project,task_name,task_no,method,schedule_type,
         year,mon,day,hour,min,sec,week,
         day_of_week,start_date,end_date,sponsor,'unScheduled',''])  #job_id = "{}#{}#{}".format(user,project,task_name)

    jobs = scheduler.get_jobs()

    jobids = [x.id for x in jobs]

    for j in joblist:
        id = j[0]+'#'+j[1]+'#'+j[2]
        if id in jobids:
            jb = scheduler.get_job(id)
            j[18] = jb.next_run_time
            j[17] = 'running' if j[18] is not None else 'pause'
            jobids.remove(id)

    for i in jobids:
        (u,p,t) = i.split('#')
        jb = scheduler.get_job(i)
        joblist.append(u,p,t,'','','','','','','','','','','','','','',
                      'running' if jb.next_run_time is not None else 'pause', jb.next_run_time)

    rlist = []
    for j in joblist:
        rlist.append(
            {
                "user": j[0],
                "project": j[1],
                "task_name": j[2],
                #"task_no": j[3],
                #"method": j[4],
                "schedule_type": j[5],
                "year": j[6],
                "mon": j[7],
                "day": j[8],
                "hour": j[9],
                "min": j[10],
                "sec": j[11],
                "week": j[12],
                "day_of_week": j[13],
                "start_date": j[14],
                "end_date": j[15],
                "sponsor": j[16],
                "status": j[17],
                "next_time": str(j[18])
            }
        )
    return {"total": 1, "rows": rlist}

def get_last_task(app, username, project):
    icons = {
        "running": url_for('static', filename='img/running.gif'),
        "success": url_for('static', filename='img/success.png'),
        "fail": url_for('static', filename='img/fail.png'),
        "exception": url_for('static', filename='img/exception.png')}
    job_path = app.config["AUTO_HOME"] + "/jobs/%s/%s" % (username, project)
    status = icons["running"]
    if exists_path(job_path):
        next_build = get_next_build_number(job_path)
        last_job = next_build-1
        if exists_path(job_path + "/%s" % last_job):
            try:
                suite = ExecutionResult(job_path + "/%s/output.xml" % last_job).suite
                stat = suite.statistics.critical
                if stat.failed != 0:
                    status = icons["fail"]
                else:
                    status = icons['success']
            except:
                status = icons["running"]
        else:
            status = icons["exception"]
    else:
        status = icons['success']

    return status


def get_projecttask(app):
    projects = app.config['DB'].get_allproject(session["username"])
    task_list = {"total": len(projects), "rows": []}
    for op in projects:
        p = op.split(':')[1]     # projects = ["owner:project","o:p"]
        task = {
            # "status": status,
            "project": p,
            # "last_success": get_last_pass(job_path + "/lastPassed"),
            # "last_fail": get_last_fail(job_path + "/lastFail"),
            "enable": "Enalble",
            "next_time": get_next_time(app, p),
            "cron": "* * * * * *",
            "status": get_last_task(app, session["username"], p)
        }

        task_list["rows"].append(task)
    return task_list

def get_last_pass(job_path):
    passed = "无"
    passed_path = job_path + "lastPassed"
    if exists_path(passed_path):
        f = codecs.open(passed_path, "r", "utf-8")

        passed = f.read()

        f.close()

    return passed


def get_last_fail(job_path):
    fail = "无"
    fail_path = job_path + "lastFail"
    if exists_path(fail_path):
        f = codecs.open(fail_path, "r", "utf-8")

        fail = f.read()

        f.close()

    return fail


def get_next_build_number(job_path):
    next_build_number = 1
    next_path = job_path + "/nextBuildNumber"
    if exists_path(next_path):
        f = codecs.open(next_path, "r", "utf-8")

        next_build_number = int(f.read())

        f.close()

    return next_build_number


def get_next_time(app, name):
    job = scheduler.get_job("%s_%s" % (session["username"], name))
    if job:
        to_zone = tz.gettz("CST")
        return job.next_run_time.astimezone(to_zone).strftime("%Y-%m-%d %H:%M:%S")
    else:
        return "-"


def edit_cron(app, name, cron):
    user_path = app.config["AUTO_HOME"] + "/users/" + session["username"]
    if os.path.exists(user_path):
        config = json.load(codecs.open(user_path + '/config.json', 'r', 'utf-8'))
        index = 0
        for p in config["data"]:
            if p["name"] == name:
                config["data"][index]["cron"] = cron
                break
            index += 1

        json.dump(config, codecs.open(user_path + '/config.json', 'w', 'utf-8'))

        return True

    return False

def get_projecttaskdir(app, project):
    #TODO : 适配多用户公用project
    projecttaskdir = app.config["AUTO_HOME"] + "/jobs/" + session["username"] + "/%s" % (project)
    return projecttaskdir

def get_taskdriver(cmdfile):
    if not os.path.exists(cmdfile):
        return 'Unknown'
    else:
        with open(cmdfile, 'r') as f:
            ln = f.readline().strip()
            splits = ln.split('|')
            return splits[0] if len(splits) > 1 else 'Unknown'
