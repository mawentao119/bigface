import os
import json
from _pytest import config
from _pytest import main
from _pytest import runner
from utils.dbclass import DBcli
from utils.file import exists_path, make_nod, write_file, read_file, mk_dirs
from utils.mylogger import getlogger

log = getlogger(__name__)
db_cli = DBcli(os.environ["DB_FILE"])

def get_pytest_data(path):
    """
    pytest testcase finder
    :param app: app
    :param path: pytest '.py' file
    :return:
    """
    log.info("解析路径下的测试用例:{}".format(path))
    children = []
    conf = config.get_config(os.path.dirname(path))
    pm = conf.pluginmanager
    args = ["--co", path]
    conf = pm.hook.pytest_cmdline_parse(pluginmanager=pm, args=args)
    s = main.Session.from_config(conf)

    # conf._do_configure() :May be needed
    conf.hook.pytest_sessionstart(session=s)
    conf.hook.pytest_collection(session=s)

    for it in s.items:
        case_name = it.nodeid.split("::", maxsplit=1)[1]
        status = db_cli.get_casestatus(path, case_name)
        print("status:{} {} :{}".format(path,case_name,status))
        icons = 'icon-step'
        if status == 'FAIL':
            icons = 'icon-step_fail'
        if status == 'PASS':
            icons = 'icon-step_pass'
        children.append({
            "text": case_name, "iconCls": icons, "state": "open",
            "attributes": {
                "name": case_name, "category": "step", "key": path,
            },
            "children": []
        })
    return children

def debug_pytest_run(path):
    """
    editor界面调试运行 pytest 测试用例
    :param path: pytest file
    :return: output->str
    """
    log.info("界面执行pytest用例文件:{}".format(path))
    conf = config.get_config(os.path.dirname(path))
    pm = conf.pluginmanager
    args = [path]
    conf = pm.hook.pytest_cmdline_parse(pluginmanager=pm, args=args)
    s = main.Session.from_config(conf)

    conf.hook.pytest_sessionstart(session=s)
    conf.hook.pytest_collection(session=s)

    session = s
    reports = []
    for i, item in enumerate(session.items):
        nextitem = session.items[i + 1] if i + 1 < len(session.items) else None
        reports.append(runner.runtestprotocol(item=item, log=False, nextitem=nextitem))

    html = ""
    for r in reports:
        output = """
        <tr><td>{}</td> <td>{}</td> <td>{}</td> <td>{}</td></tr>
        <tr><td></td> <td>{}</td> <td>{}</td> <td>{}</td></tr>
        <tr><td></td> <td>{}</td> <td>{}</td> <td>{}</td></tr>
        """.format(r[0].head_line, r[0].when, r[0].outcome, r[0].longreprtext,
                                   r[1].when, r[1].outcome, r[1].longreprtext,
                                   r[2].when, r[2].outcome, r[2].longreprtext,)
        html += output

    head = """
    <html>
    <body>
    <p>{}</p>
    <table border="1">
    <tr>
        <th>Case Name</th>
        <th>Stage</th>
        <th>Result</th>
        <th>Info</th>
    </tr>
    """.format(path)
    tail = """
    </table>
    </body>
    </html>
    """

    return head + html + tail


def pytest_run(case_key, args="", user='', catigory=''):
    log.info("开始运行pytest用例：{}".format(case_key))
    username = user if user != '' else 'unknown'
    driver = catigory if catigory != '' else username

    project = os.environ["PROJECT_NAME"]
    output = os.environ["AUTO_HOME"] + "/jobs/%s/%s" % (username, project)

    if not exists_path(output):
        mk_dirs(output)

    (out, index) = reset_next_build_numb(output)
    log.info("out:{} , index:{}".format(out, index))

    mk_dirs(out) if not exists_path(out) else None

    from _pytest import config
    from _pytest import main
    from _pytest import runner

    conf = config.get_config(os.path.dirname(case_key))
    pm = conf.pluginmanager
    args = [case_key]
    print("pytest config args: {}".format(args))
    conf = pm.hook.pytest_cmdline_parse(pluginmanager=pm, args=args)
    s = main.Session.from_config(conf)

    conf.hook.pytest_sessionstart(session=s)
    conf.hook.pytest_collection(session=s)

    with open(out + "/cmd.txt", 'w') as f:
        f.write("{}|pytest|{}|--outputdir={}|{}\n".format(driver, ','.join(args),out,case_key))
    log.info("Write: {}/cmd.txt".format(out))

    reports = []
    for i, item in enumerate(s.items):
        log.info("name: {} ,fspath: {}".format(item.name, item.fspath))
        nextitem = s.items[i + 1] if i + 1 < len(s.items) else None
        reports.append(runner.runtestprotocol(item=item, log=False, nextitem=nextitem))

    db_cli.insert_loginfo(username, 'task', 'run', case_key, 'OK')

    html = ""
    for r in reports:
        output = """
            <tr><td>{}</td> <td>{}</td> <td>{}</td> <td>{}</td></tr>
            <tr><td></td> <td>{}</td> <td>{}</td> <td>{}</td></tr>
            <tr><td></td> <td>{}</td> <td>{}</td> <td>{}</td></tr>
            """.format(r[0].head_line, r[0].when, r[0].outcome, r[0].longreprtext,
                       r[1].when, r[1].outcome, r[1].longreprtext,
                       r[2].when, r[2].outcome, r[2].longreprtext, )
        html += output

    head = """
        <html>
        <body>
        <p>{}</p>
        <table border="1">
        <tr>
            <th>Case Name</th>
            <th>Stage</th>
            <th>Result</th>
            <th>Info</th>
        </tr>
        """.format(case_key)
    tail = """
        </table>
        </body>
        </html>
        """
    with open(out + "/report.html", 'w') as f:
        f.write(head+html+tail)
    with open(out + "/log.html", 'w') as f:
        f.write(head+html+tail)

    reset_last_status_pytest(reports, out, index)
    update_pycase_info(username, reports, out)


def reset_last_status_pytest(reports, output, index):
    log.info("设置用例结果：out:{},index:{}".format(output, index))
    fail = 0
    for r in reports:
        for i in r:
            if i.outcome == "failed":
                fail += 1

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


def update_pycase_info(username, reports, out):
    """
    更新pytest测试用例的结果到数据库，所有参数取call，放弃setup和teardown到数据
    :param reports: result reports
    :param username: username
    :param out: output dir
    :return: None
    """

    sucess_total = 0
    fail_total = 0
    duration = 0

    for r in reports:
        source = r[1].fspath   # fspath in report while fspath.strpath in session.items
        source = os.path.join(os.getcwd(), source)  # ref path in report while abs path in session.items
        name = r[1].nodeid.split("::", maxsplit=1)[1]
        if r[1].outcome == "passed":
            status = "PASS"
        else:
            status = "FAIL"
        if status == "PASS":
            success = 1
            fail = 0
            sucess_total += success
        else:
            success = 0
            fail = 1
            fail_total += fail
        duration += r[1].duration

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
                    '''.format(r[1].duration, status, "unknown", "unknown", "unknown", "", username, success, fail,
                               source, name)
        res = db_cli.runsql(sql)

        db_cli.insert_loginfo(username, 'case', 'run', source, status)

        if res.rowcount < 1:
            log.warning("Cannot find case:{}:{}, Insert it ...".format(source, name))
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
                                    '''.format(r[1].duration, status, "unknown", "unknown", "unknown", "", username,
                                               1, success, fail, source, name)
            res = db_cli.runsql(sql)
            if res.rowcount < 1:
                log.error("Add New Case:{}:{} Failed".format(source, name))

    source = ""
    with open(out + "/cmd.txt", 'r') as cf:
        line = cf.readline()
        source = line.split('|')[2]

    result = {
        "source": source,
        "success": sucess_total,
        "fail": fail_total,
        "duration": duration
    }
    with open(out + '/pytest_res.txt', 'w') as rf:
        rf.write(json.dumps(result))

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

    return (out,index)

