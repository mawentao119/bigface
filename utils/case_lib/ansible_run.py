# -*- coding: utf-8 -*-

__author__ = "chairsma"

import os
import json
import ast
from uuid import uuid4
from yaml import safe_load

import ansible_runner
from ansible_runner.utils import dump_artifact
from ansible_runner.exceptions import AnsibleRunnerException

from robot.api import logger

AN_DIR = os.path.join(os.environ["PROJECT_DIR"], 'ansible')
SPACE_DIR = os.environ["SPACE_DIR"]
RESERVE_ARTIFACTS = 10
TEMP_DIR = os.environ["AUTO_TEMP"]


def get_inventory_json(inventory=os.path.join(AN_DIR, 'inventory/hosts')):
    inventorys = [inventory]
    json_res, error = ansible_runner.get_inventory('list', inventorys, 'json')
    return json_res


def run_play(desc="", **kwargs):         # "desc" is just for comment in testcase ,useless here.
    vargs = _prepare_parameters(kwargs)
    res = None
    try:
        res = ansible_runner.run(**vargs)
        logger.info("结果目录：{}".format(res.config.artifact_dir))
    except Exception as e:
        logger.error("执行异常：{}".format(e))
    if res.rc != 0:
        logger.info("执行失败：{}".format(res.stderr.name))
    return res.rc


def _prepare_parameters(vargs):
    if not vargs.get('private_data_dir'):
        vargs['private_data_dir'] = AN_DIR
    logger.info("运行HOME: {}".format(vargs.get('private_data_dir')))

    if not vargs.get('artifact_dir'):
        vargs['artifact_dir'] = SPACE_DIR
    logger.info("artifacts目录: {}".format(vargs.get('artifact_dir')))

    if not vargs.get('rotate_artifacts'):
        vargs['rotate_artifacts'] = RESERVE_ARTIFACTS

    if vargs.get('role'):
        if vargs.get('playbook'):
            logger.error("参数错误：role 和 playbook 不可以同时使用")

        role = {'name': vargs.get('role')}
        if vargs.get('role_vars'):
            role_vars = {}
            for item in vargs['role_vars'].split():
                key, value = item.split('=')
                try:
                    role_vars[key] = ast.literal_eval(value)
                except Exception:
                    role_vars[key] = value
            role['vars'] = role_vars

        envvars_path = os.path.join(vargs.get('private_data_dir'), 'env/envvars')
        envvars_exists = os.path.exists(envvars_path)

        play = [{'hosts': vargs.get('hosts', "all"),
                 'gather_facts': vargs.get('role_skip_facts', False),
                 'roles': [role]}]

        filename = str(uuid4().hex)
        playbook = dump_artifact(json.dumps(play), TEMP_DIR, "play_" + filename)
        vargs["playbook"] = playbook
        logger.info('使用playbook: %s' % playbook)

        if vargs.get('inventory'):
            inventory_file = os.path.join(vargs.get('private_data_dir'), 'inventory', vargs.get('inventory'))
            if not os.path.exists(inventory_file):
                raise AnsibleRunnerException('location specified by --inventory does not exist')
            logger.info('使用inventory: %s' % inventory_file)

        roles_path = vargs.get('roles_path') or os.path.join(vargs.get('private_data_dir'), 'roles')
        roles_path = os.path.abspath(roles_path)
        logger.info('使用 ANSIBLE_ROLES_PATH : %s' % roles_path)

        envvars = {}
        if envvars_exists:
            with open(envvars_path, 'rb') as f:
                tmpvars = f.read()
                new_envvars = safe_load(tmpvars)
                if new_envvars:
                    envvars = new_envvars

        envvars['ANSIBLE_ROLES_PATH'] = roles_path
        vargs["envvars"] = envvars

    return vargs


if __name__ == '__main__':
    # res = get_inventory_json()
    arg = {
        "private_data_dir": "/Users/mawentao/PycharmProjects/bigface/project/DollarKV_test/ansible",
        "inventory": "hosts",
        "play_book": "test.yml"
    }

    ss = run_play(playbook="test.yml")

    ss = run_play(role="testrole", hosts="cache1*")

