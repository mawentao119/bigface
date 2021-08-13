# -*- coding: utf-8 -*-

__author__ = "苦叶子"
__modifier__ = 'charisma 2020-01-20'

"""
All Start Here!
"""

from auto.www.app import create_app
from auto.settings import HEADER
from utils.help import check_version

print(HEADER)

app = create_app('default')


if __name__ == '__main__':

    check_version()

    app.run(host="0.0.0.0", port=int("8080"), debug=True)
