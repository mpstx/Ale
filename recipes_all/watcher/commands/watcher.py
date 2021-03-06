#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from os.path import join as join
from ale.base import Command
from ale.core import executeCommand, isCommandInstalled
from ale.utils import dirEntries
from aleconfig import alePath
import logging
import time
import pickle


class WatcherCommand(Command):

    name = 'watcher'
    shorthelp = 'monitors files matching a filespec for change and triggers command(s)'

    watchconfigfile = join(alePath('recipes_installed/watcher'), 'config.pickle')
    positiveSound = join(alePath('recipes_installed/watcher'), 'positive.wav')
    negativeSound = join(alePath('recipes_installed/watcher'), 'negative.wav')

    watchlist = {}

    def settitle(self, title):
        os.system('echo "\\033]0;%s\\007"' % title)

    def sound(self, file):
        player_name = 'afplay' if os.uname()[0] == 'Darwin' else 'aplay -q'
        os.system('%s %s' % (player_name, file))

    def notify(self, command, success):
        if success:
            self.sound(self.positiveSound)
            print 'Success. (%s)' % command
            self.settitle('%s %s' % (command, 'Succeeded'))
        else:
            self.sound(self.negativeSound)
            print 'ERROR. (%s) **************************************************** You need to fix this.' % command
            self.settitle('%s %s' % (command, 'Failed'))

    def execute(self, args=None):

        if args and len(args) == 3 and args[0] == 'add':
            filetype = args[1]
            command = args[2]
            self.addWatch(filetype, command)
            return

        if args and len(args) == 3 and args[0] == 'remove':
            filetype = args[1]
            command = args[2]
            self.removeWatch(filetype, command)
            return

        self.loadWatches()

        if args and len(args) == 1 and args[0] == 'list':
            print 'Stuff to watch:'
            for type in self.watchlist.iterkeys():
                for command in self.watchlist[type]:
                    logging.info('When *.%s changes, execute %s' % (type, command))
            return

        if args:
            print '''
Syntax: ale watcher [command]
'''
            print '  Optional Commands:'
            print '  list'
            print '  add <file_extension> <command_to_exec_on_change>'
            print '  remove <file_extension> <command_to_exec_on_change>'
            print '  help'
            return

        if len(self.watchlist.keys()) == 0:
            print 'No watches configured.   Run "ale watcher help" for help'
            return

        ignoreAle = lambda path: '.ale' in path

        def getFilesForType(type):
            return dirEntries('.', True, ignoreAle, type)

        filesForType = {}
        for type in self.watchlist.iterkeys():
            filesForType[type] = getFilesForType(type)

        def getLastTouch(files):
            lasttouch = 0.0
            for file in files:
                if os.path.getmtime(file) > lasttouch:
                    lasttouch = os.path.getmtime(file)
            return lasttouch

        logging.info('Watcher started.  (Run "ale watcher help" for help)')

        for type in self.watchlist.iterkeys():
            for command in self.watchlist[type]:
                logging.info('When *.%s changes, execute %s' % (type, command))

        for type in self.watchlist.iterkeys():
            logging.info('Monitoring %s .%s files for changes...' % (len(filesForType[type]), type))

        currenttouch = 0.0

        while True:
            for type in self.watchlist.iterkeys():
                newFilesForType = getFilesForType(type)
                snapshotTouch = getLastTouch(newFilesForType)
                
                if snapshotTouch > currenttouch or set(newFilesForType) != set(filesForType[type]): # detect deletions as a trigger
                    filesForType[type] = newFilesForType
                    for command in self.watchlist[type]:
                        self.settitle('running %s' % command)
                        result = executeCommand(command, [])
                        self.notify(command, result == 0)

                    currenttouch = snapshotTouch
                time.sleep(1)

        return 0  # error count (0=success).

    def install(self, args=None):
        if isCommandInstalled('pyflakes'):
            self.addWatch('py', 'pyflakes')

        if isCommandInstalled('test'):
            self.addWatch('py', 'test')

    def loadWatches(self):
        if os.path.exists(self.watchconfigfile):
            file = open(self.watchconfigfile, 'rb')
            self.watchlist = pickle.load(file)
            file.close()
        else:
            self.watchlist = {}

    def addWatch(self, fileextension, command):
        self.loadWatches()

        if not isCommandInstalled(command):
            logging.error('unrecognized command: %s' % command)
            return

        commandsfortype = self.watchlist[fileextension] if fileextension in self.watchlist else None
        if commandsfortype:
            self.watchlist[fileextension].append(command)
        else:
            self.watchlist[fileextension] = [command]

        file = open(self.watchconfigfile, 'wb')
        pickle.dump(self.watchlist, file)
        file.close()
        logging.info('Added watch for .%s -- execute %s on change.' % (fileextension, command))

    def removeWatch(self, fileextension, command):
        self.loadWatches()

        commandsfortype = self.watchlist[fileextension]
        if commandsfortype:
            self.watchlist[fileextension].remove(command)
            if len(self.watchlist[fileextension]) == 0:
                del self.watchlist[fileextension]

        file = open(self.watchconfigfile, 'wb')
        pickle.dump(self.watchlist, file)
        file.close()
        logging.info('Removed watch for .%s to execute %s' % (fileextension, command))


