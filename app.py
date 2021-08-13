# -*- coding: utf-8 -*-

__author__ = "苦叶子"
__modifier__ = 'charisma 2020-01-20'

"""
All Start Here!
"""

#from flask_script import Manager

from auto.www.app import create_app
from auto.settings import HEADER
from utils.help import check_version

print(HEADER)

app = create_app('default')
#manager = Manager(app)


if __name__ == '__main__':

    check_version()

    #manager.run()
    app.run(debug=True)
