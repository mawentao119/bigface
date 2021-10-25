# -*- coding: utf-8 -*-

__author__ = "苦叶子"
__modifier__ = 'charisma 2020-01-20'

"""
All Start Here!
"""

from auto.www.app import create_app
from auto.settings import HEADER
from utils.help import check_version
from utils.mylogger import getlogger

print(HEADER)

app = create_app('default')

import argparse
import shlex
import logging

logging = getlogger(__name__)

__version__ = "0.5.0.0"

app.config["SECRET_KEY"] = "secret!"
app.config["fd"] = None
app.config["child_pid"] = None

def main():
    parser = argparse.ArgumentParser(
        description=(
            "A fully functional terminal in your browser. "
            "https://github.com/cs01/pyxterm.js"
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("-p", "--port", default=5000, help="port to run server on")
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="host to run server on (use 0.0.0.0 to allow access from other hosts)",
    )
    parser.add_argument("--debug", action="store_true", help="debug the server")
    parser.add_argument("--version", action="store_true", help="print version and exit")
    parser.add_argument(
        "--command", default="bash", help="Command to run in the terminal"
    )
    parser.add_argument(
        "--cmd-args",
        default="",
        help="arguments to pass to command (i.e. --cmd-args='arg1 arg2 --flag')",
    )
    args = parser.parse_args()
    if args.version:
        print(__version__)
        exit(0)
    app.config["cmd"] = [args.command] + shlex.split(args.cmd_args)
    logging.info(f"serving on http://127.0.0.1:{args.port}")
    app.run(debug=args.debug, port=args.port, host=args.host)


if __name__ == "__main__":
    check_version()
    main()
