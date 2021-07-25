# -*- coding: utf-8 -*-

__author__ = "mawentao119@gmail.com"

"""
Init the App
init Admin and DemoProject
"""
import logging
import os
from utils.dbclass import TestDB

class Config:

    SSL_REDIRECT = False

    SECRET_KEY = 'QWERTYUIOPASDFGHJ'
    # logging level
    LOGGING_LEVEL = logging.INFO
    SHOW_DIR_DETAIL = False

    APP_DIR = os.getcwd()    # ...../bigface

    SERVICE_DIR = os.path.join(APP_DIR, "project")
    AUTO_HOME = os.path.join(SERVICE_DIR, "works")
    DB_DIR    = os.path.join(AUTO_HOME, "DBs")
    SPACE_DIR = os.path.join(AUTO_HOME, "workspace")
    AUTO_TEMP = os.path.join(AUTO_HOME, "runtime")

    CASE_TEMPLATE_DIR = os.path.join(APP_DIR, 'auto/www/templates/case_template')

    os.mkdir(AUTO_HOME) if not os.path.exists(AUTO_HOME) else None
    os.mkdir(DB_DIR) if not os.path.exists(DB_DIR) else None
    os.mkdir(SPACE_DIR) if not os.path.exists(SPACE_DIR) else None
    os.mkdir(os.path.join(SPACE_DIR, 'Admin')) if not os.path.exists(
        os.path.join(SPACE_DIR, 'Admin')) else None
    os.mkdir(os.path.join(SPACE_DIR,'Admin/DemoProject')) if not \
        os.path.exists(os.path.join(SPACE_DIR,'Admin/DemoProject')) else None
    os.mkdir(os.path.join(SPACE_DIR, 'Admin/DemoProject/templates')) if not os.path.exists(
        os.path.join(SPACE_DIR, 'Admin/DemoProject/templates')) else None
    os.mkdir(AUTO_TEMP) if not os.path.exists(AUTO_TEMP) else None

    DB = TestDB(AUTO_HOME)
    PROJECT_DIR = DB.get_project_dir()
    PROJECT_NAME = DB.get_project_name()

    os.environ["ROBOT_DIR"] = PROJECT_DIR
    os.environ["PROJECT_DIR"] = PROJECT_DIR
    os.environ["PROJECT_NAME"] = PROJECT_NAME


    AUTO_ROBOT = []    # Process list of running tasks, only for hand running ,not for schceduled jobs. MAX: setting:MAX_PROCS

    ##dbfile = DB.get_dbfilename()
    ##url = 'sqlite:///' + dbfile
    ##SCHEDULER_JOBSTORES = {
    ##    'default': SQLAlchemyJobStore(url = "sqlite:////Users/tester/PycharmProjects/uniRobotDev/work/DBs/schedule.db")
    ##}
    ##print("*************url:{}".format('sqlite:///' + dbfile))
    #SCHEDULER_EXECUTORS = {
    #    'default': {'type': 'threadpool', 'class': 'apscheduler.executors.pool:ThreadPoolExecutor', 'max_workers': 20},
    #    'processpool': ProcessPoolExecutor(max_workers=5)
    #}
    SCHEDULER_JOB_DEFAULTS = {
        'coalesce': False,
        'max_instances': 3
    }
    SCHEDULER_TIMEZONE = "Asia/Shanghai"

    SCHEDULER_API_ENABLED = True

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        # 发送服务启动初始化时错误信息给管理员： Send Error info to Admin
        import logging
        from logging.handlers import SMTPHandler
        credentials = None
        secure = None
        if getattr(cls, 'MAIL_USERNAME', None) is not None:
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, 'MAIL_USE_TLS', None):
                secure = ()

        mail_handler = SMTPHandler(
            mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
            fromaddr=cls.FLASKY_MAIL_SENDER,
            toaddrs=[cls.FLASKY_ADMIN],
            subject=cls.FLASKY_MAIL_SUBJECT_PREFIX + ' AutoLine Startup Error',
            credentials=credentials,
            secure=secure)

        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,

    "default": DevelopmentConfig
}
