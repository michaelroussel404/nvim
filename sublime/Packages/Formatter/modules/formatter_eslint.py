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
INTERPRETERS = ['node']
EXECUTABLES = ['eslint', 'eslint.js']
MODULE_CONFIG = {
    'source': 'https://github.com/eslint/eslint',
    'name': 'ESLint',
    'uid': 'eslint',
    'type': 'beautifier',
    'syntaxes': ['js'],
    'exclude_syntaxes': None,
    "executable_path": "",
    'args': ['--resolve-plugins-relative-to', '/path/to/javascript/node_modules'],
    'config_path': {
        'default': 'eslint_rc.json'
    }
}


class EslintFormatter(common.Module):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_cmd(self):
        cmd = self.get_combo_cmd(runtime_type='node')
        if not cmd:
            return None

        path = self.get_config_path()
        if path:
            cmd.extend(['--config', path])

        cmd.extend(['--stdin', '--fix-dry-run', '--format=json'])

        log.debug('Current arguments: %s', cmd)
        cmd = self.fix_cmd(cmd)

        return cmd

    def format(self):
        cmd = self.get_cmd()
        if not self.is_valid_cmd(cmd):
            return None

        try:
            exitcode, stdout, stderr = self.exec_cmd(cmd)

            if exitcode > 1:
                log.error('File not formatted due to an error (exitcode=%d): "%s"', exitcode, stderr)
            else:
                obj = sublime.decode_value(stdout)[0]
                if 'output' in obj:
                    return obj.get('output', None)
                log.error('File not formatted due to an error (exitcode=%d): "%s"', exitcode, stderr)
                for i in obj.get('messages', []):
                    print(i)
        except OSError:
            log.error('An error occurred while executing the command: %s', ' '.join(cmd))

        return None
