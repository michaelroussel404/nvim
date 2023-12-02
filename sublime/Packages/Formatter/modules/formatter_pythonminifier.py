#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# @rev          74a48aa645ba5e1955cd3e50c8e141a300ddc6f5 (74a48aa)
# @tree         0de149c628a1cd9f2ad0786bc9863e7125aa41ad (0de149c)
# @date         2023-11-27 05:08:37 +0100
# @author       bitst0rm <bitst0rm@users.noreply.github.com>
# @copyright    Copyright (c) 2019-present, Duc Ng. (bitst0rm)
# @link         https://github.com/bitst0rm
# @license      The MIT License (MIT)

import logging
import sublime
from ..core import common

log = logging.getLogger(__name__)
INTERPRETERS = ['python3', 'python']
EXECUTABLES = ['pyminify']
MODULE_CONFIG = {
    'source': 'https://github.com/dflook/python-minifier',
    'name': 'Python Minifier',
    'uid': 'pythonminifier',
    'type': 'minifier',
    'syntaxes': ['python'],
    'exclude_syntaxes': None,
    "executable_path": "",
    'args': None,
    'config_path': {
        'default': 'python_minifier_rc.json'
    }
}


class PythonminifierFormatter(common.Module):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_cmd(self):
        cmd = self.get_combo_cmd(runtime_type='python')
        if not cmd:
            return None

        path = self.get_config_path()
        if path:
            params = [
                '--no-combine-imports',
                '--no-remove-pass',
                '--remove-literal-statements',
                '--no-remove-annotations',
                '--no-remove-variable-annotations',
                '--no-remove-return-annotations',
                '--no-remove-argument-annotations',
                '--remove-class-attribute-annotations',
                '--no-hoist-literals',
                '--no-rename-locals',
                '--preserve-locals',
                '--rename-globals',
                '--preserve-globals',
                '--no-remove-object-base',
                '--no-convert-posargs-to-args',
                '--no-preserve-shebang',
                '--remove-asserts',
                '--remove-debug',
                '--no-remove-explicit-return-none',
                '--no-remove-builtin-exception-brackets'
            ]

            with open(path, 'r', encoding='utf-8') as file:
                data = file.read()
            json = sublime.decode_value(data)

            for k, v in json.items():
                no_param = '--no-' + k
                param = '--' + k
                if no_param in params and isinstance(v, bool) and not v:
                        cmd.extend([no_param])
                if param in params:
                    if isinstance(v, bool) and v:
                        cmd.extend([param])
                    if isinstance(v, list) and v:
                        cmd.extend([param, ', '.join(v)])

        cmd.extend(['-'])

        log.debug('Current arguments: %s', cmd)
        cmd = self.fix_cmd(cmd)

        return cmd

    def format(self):
        cmd = self.get_cmd()
        if not self.is_valid_cmd(cmd):
            return None

        try:
            exitcode, stdout, stderr = self.exec_cmd(cmd)

            if exitcode > 0:
                log.error('File not formatted due to an error (exitcode=%d): "%s"', exitcode, stderr)
            else:
                return stdout
        except OSError:
            log.error('An error occurred while executing the command: %s', ' '.join(cmd))

        return None
