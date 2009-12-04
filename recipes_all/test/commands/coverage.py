#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import logging
from os.path import join as join
from aleconfig import alePath
from ale.base import Command
from ale.core import isCommandInstalled
from subprocess import Popen
from ale.utils import relpath, getGaeLibs

class NoseCoverageCommand(Command):
    name = 'coverage'
    shorthelp = 'measure coverage of tests with nosetests+coverage'

    def execute(self, args=None):
        prevCwd = os.getcwd()
        noseroot = join(join(join(alePath('recipes_installed'), 'test'), 'pkgs'), 'nose-0.11.0')
        coverageroot = join(join(join(alePath('recipes_installed'), 'test'), 'pkgs'), 'coverage-3.2b3')

        arg = '.' if not args else args[0]

        command = join(join(noseroot, 'bin/'), 'nosetests')
        logging.info('Executing %s %s' % (relpath(command), arg))

        pythonpath = ':'.join([noseroot, coverageroot] + getGaeLibs())

        p = Popen([command, '--with-coverage', '--cover-erase', '--cover-inclusive', '--cover-exclude-package', 'nose,webob,urllib,google,ssl,wsgiref,urlparse,rfc822,mimetools,httplib,dummy_thread,cgi,calendar,base64,Cookie', arg], env={"PYTHONPATH": pythonpath})
        sts = os.waitpid(p.pid, 0)[1]

        return sts