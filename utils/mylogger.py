import logging
import os
from datetime import datetime, date

"""Log Module of Project"""
def getlogger(name=__name__):

    starttime = date.strftime(datetime.now(),'%Y%m%d%H')

    path = os.path.join(os.getcwd(), "project", "works", "log")
    LogFile = path + "/app_"+starttime+".log"
    print("Writing Log to File:{}".format(LogFile))

    os.mkdir(path) if not os.path.exists(path) else None

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Create handlers
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler(LogFile)
    c_handler.setLevel(logging.INFO)
    f_handler.setLevel(logging.INFO)

    # Create formatters and add it to handlers
    c_format = logging.Formatter('%(name)s %(levelname)s (%(funcName)s:%(lineno)s) %(message)s')
    f_format = logging.Formatter('%(asctime)s %(name)s %(levelname)s (%(funcName)s:%(lineno)s) %(message)s')
    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)

    logger.addHandler(c_handler)
    logger.addHandler(f_handler)

    return logger