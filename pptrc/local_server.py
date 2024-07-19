# -*- coding: utf-8 -*-
# @Time    : 2024/4/15 上午11:12 上午11:12
# @Author  : Zr
# @Comment :
import logging
import os
import subprocess
from logging import CRITICAL, FATAL, ERROR, WARNING, WARN, INFO, DEBUG, NOTSET
from .log import getFileLogger


def _cmd(cmd, args=None, cwd=None):
    if type(args) is list:
        args = ' '.join(args)

    ret = subprocess.run(f"{cmd} {args or ''}", cwd=cwd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    stdout = ret.stdout.decode('utf8', errors='ignore')
    stderr = ret.stderr.decode('utf8', errors='ignore')

    return ret.returncode, stdout, stderr


class LocalPPTRSMgr():
    def __init__(self, host='0.0.0.0', port=9999, log_level="debug", log_file=None):

        self._pptrs_path = os.path.join(os.path.dirname(__file__), 'js')
        self._port = port
        self._host = host
        self._script = 'stub.js'
        self._log_file = log_file
        self._logger = getFileLogger(file=self._log_file, level=log_level)

        if not os.path.exists(self._pptrs_path):
            raise RuntimeError(f'pptrc server[javascript] not foud in {os.getcwd()}')

        returncode, stdout, stderr = _cmd("node -v")
        if returncode != 0:
            raise RuntimeError('node not found in system.')

        returncode, stdout, stderr = _cmd("pm2 -v")
        if returncode != 0:
            self._logger.info('pm2 not found in system.\ninstalling pm2...')
            returncode, stdout, stderr = _cmd("npm i -g pm2")
            if returncode != 0:
                raise RuntimeError('npm install pm2 failed, pls install manual by: npm i -g pm2')

        # install
        _node_modules_path = os.path.join(self._pptrs_path, 'node_modules')
        if not os.path.exists(_node_modules_path):
            self._logger.info('node_modules not found, installing js packages...')
            returncode, stdout, stderr = _cmd("npm i", cwd=self._pptrs_path)
            if returncode != 0:
                os.removedirs(_node_modules_path)
                raise RuntimeError('npm install failed.')

    def _pm2_run(self, action, name, script=None, args=None, cwd=None, log_file=None):
        if args:
            if type(args) is list:
                args = ' '.join(args)

            args = f' -- {args}'

        if action == 'start':
            name = f'-n {name}'

        if log_file:
            log_file = f'-l {log_file}'

        cmd = f"pm2 {action} {name} {log_file or ''} {script or ''} {args or ''}"

        returncode, stdout, stderr = _cmd(cmd, cwd=cwd)

        self._logger.debug(f"\n\n>>>>>{cmd}")

        if stdout.strip('\n'):
            self._logger.debug(f'\n\n>>>>>{stdout}')

        if stderr.strip('\n'):
            self._logger.debug(f'\n\n>>>>>{stderr}')

        return returncode, stdout, stderr

    def start(self, id=None):
        if not id:
            id = f'{self._port}'

        if self._logger.level in [logging.CRITICAL, logging.FATAL]:
            _log_level = 'FATAL'
        elif self._logger.level in [logging.WARNING, logging.WARN]:
            _log_level = 'WARN'
        elif self._logger.level == logging.NOTSET:
            _log_level = 'OFF'
        elif self._logger.level == logging.DEBUG:
            _log_level = 'DEBUG'
        elif self._logger.level == logging.INFO:
            _log_level = 'INFO'
        elif self._logger.level == logging.ERROR:
            _log_level = 'ERROR'
        else:
            _log_level = 'DEBUG'

        _args = [self._host, str(self._port), _log_level]
        if self._log_file:
            _args.append(self._log_file)

        return \
            self._pm2_run('start', name=id, script=self._script, args=_args,
                          cwd=self._pptrs_path)[
                0]

    def stop(self, id=None):
        if not id:
            id = f'{self._port}'

        return self._pm2_run('stop', name=id, cwd=self._pptrs_path)[0]

    def delete(self, id=None):
        if not id:
            id = f'{self._port}'
        return self._pm2_run('delete', name=id, cwd=self._pptrs_path)[0]

    def restart(self, id=None):
        if not id:
            id = f'{self._port}'

        if not self.exists(id):
            return self.start(id)

        return self._pm2_run('restart', name=id, cwd=self._pptrs_path)[0]

    def exists(self, id=None):
        if not id:
            id = f'{self._port}'

        returncode, stdout, stderr = self._pm2_run('pid', name=id, cwd=self._pptrs_path)
        stdout = stdout.strip('\n')
        if not stdout:
            return False
        else:
            return True
