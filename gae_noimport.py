#!/usr/bin/env python
#
# Copyright 2009 Jason Stitt
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
#----------------------------------------------------------------------------#
#
# PURPOSE: Print a list of functions/values in Python standard libraries that
# cannot be accessed on Google App Engine. Does not test names that begin with
# underscores. Does not test whether functions work, only whether they can
# be imported/accessed. Due to the need for introspection, does not test
# contents of modules not available on the local machine. For best results,
# run under Python 2.5 (what GAE uses).
#
# REQUIREMENTS: You must have the GAE SDK installed and its dev_appserver.py
# must be on your path and executable. You need to be on a *nix platform.
#
#----------------------------------------------------------------------------#

import sys
import os
from os import path
from time import time
from tempfile import mkdtemp
from subprocess import Popen, PIPE
from urllib import urlopen
from shutil import rmtree
from signal import SIGKILL

PORT = 15111 # arbitrary, probably no conflicts

def main():
    modules, failed = import_modules(PYTHON_2_5_MODULES)
    sys.stderr.write("\n".join(("Not found locally: %s" % name for name in failed)) + "\n")
    sys.stdout.write(fetch(modules))

def fetch(modules):
    """ Start an appengine development server locally and return the result
    it prints: a string containing one name per line, representing modules,
    functions, fields, and classes that cannot be imported on GAE. """
    
    appdir = makeapp(modules)
    try:
        server_proc = runserver(PORT, appdir)
        try:
            output = urlopen('http://localhost:%d/' % PORT).read()
            return output
        finally:
            os.kill(server_proc.pid, SIGKILL)
    finally:
        rmtree(appdir)

def import_modules(module_names):
    """ Import a list of modules by name, returning two lists: one containing
    references to imported modules, and the other containing names of modules
    that could not be imported. """
    
    modules = []
    failed = []
    for name in module_names:
        try:
            __import__(name)
            modules.append(sys.modules[name])
        except ImportError:
            failed.append(name)
    return modules, failed

def makeapp(modules):
    """ Create a temporary directory, place within it an app.py and app.yaml
    constituting a GAE application, and return the path to the directory. """
    
    appdir = mkdtemp()
    open(path.join(appdir, 'app.yaml'), 'w').write(APP_YAML)
    
    app_py_lines = [APP_PY_START]
    for module in modules:
        args = {
            'module_name': module.__name__,
            'attrs': str([x for x in dir(module) if not x.startswith('_')]),
            }
        app_py_lines.append(APP_PY_CHUNK % args)
    open(path.join(appdir, 'app.py'), 'w').write('\n'.join(app_py_lines))
        
    return appdir

def runserver(port, appdir, timeout=30):
    """ Runs the dev_appserver.py script from the GAE SDK with the specified
    port and application directory and returns a Popen object, after blocking
    until the server has printed a message indicating the server is fully
    up and running. Raises OSError if this is not done within the timeout. """
    
    start_time = time()
    server_proc = Popen(['dev_appserver.py', '-p', str(port), appdir], stderr=PIPE)
    started = False
    while time() < start_time + timeout:
        line = server_proc.stderr.readline()
        if not line:
            break
        elif "Running application" in line:
            started = True
            break
    if not started:
        if server_proc.pid:
            os.kill(server_proc.pid, SIGKILL)
        raise OSError("Could not start de_appserver.py successfully")
    return server_proc
    
#----------------------------------------------------------------------------#

APP_YAML = """\
application: gaenoimport
version: 1
runtime: python
api_version: 1

handlers:
- url: /.*
  script: app.py
"""

APP_PY_START = """\
print "Content-Type: text/plain"
print ""

def print_notallowed(module, module_name, attr_names):
    for name in attr_names:
        try:
            x = getattr(module, name)
        except AttributeError:
            print module_name + '.' + name

"""

APP_PY_CHUNK = """\
try:
    import %(module_name)s
    print_notallowed(%(module_name)s, '%(module_name)s', %(attrs)s)
except ImportError:
    print "%(module_name)s.*"
"""

# Python 2.5 is used by GAE
# List adapted from http://www.python.org/doc/2.5/modindex.html
PYTHON_2_5_MODULES = \
['aepack', 'aetools', 'aetypes', 'aifc', 'AL', 'al', 'anydbm', 'applesingle',
'array', 'asynchat', 'asyncore', 'atexit', 'audioop', 'autoGIL', 'base64',
'BaseHTTPServer', 'Bastion', 'binascii', 'binhex', 'bisect', 'bsddb',
'buildtools', 'bz2', 'calendar', 'cd', 'cfmfile', 'cgi', 'CGIHTTPServer',
'cgitb', 'chunk', 'cmath', 'cmd', 'code', 'codecs', 'codeop', 'collections',
'ColorPicker', 'colorsys', 'commands', 'compileall', 'compiler',
'compiler.ast', 'compiler.visitor', 'ConfigParser', 'contextlib', 'Cookie',
'cookielib', 'copy', 'copy_reg', 'cPickle', 'cProfile', 'crypt', 'cStringIO',
'csv', 'ctypes', 'curses', 'curses.ascii', 'curses.panel', 'curses.textpad',
'curses.wrapper', 'datetime', 'dbhash', 'dbm', 'decimal', 'DEVICE', 'difflib',
'dircache', 'dis', 'dl', 'doctest', 'DocXMLRPCServer', 'dumbdbm',
'dummy_thread', 'dummy_threading', 'EasyDialogs', 'email', 'email.charset',
'email.encoders', 'email.errors', 'email.generator', 'email.header',
'email.iterators', 'email.message', 'email.mime', 'email.mime.audio',
'email.mime.base', 'email.mime.image', 'email.mime.message',
'email.mime.multipart', 'email.mime.nonmultipart', 'email.mime.text',
'email.parser', 'email.utils', 'encodings.idna', 'errno', 'exceptions',
'fcntl', 'filecmp', 'fileinput', 'findertools', 'FL', 'fl', 'flp', 'fm',
'fnmatch', 'formatter', 'fpectl', 'fpformat', 'FrameWork', 'ftplib',
'functools', 'gc', 'gdbm', 'gensuitemodule', 'getopt', 'getpass', 'gettext',
'GL', 'gl', 'glob', 'gopherlib', 'grp', 'gzip', 'hashlib', 'heapq', 'hmac',
'hotshot', 'hotshot.stats', 'htmlentitydefs', 'htmllib', 'HTMLParser',
'httplib', 'ic', 'icopen', 'imageop', 'imaplib', 'imgfile', 'imghdr', 'imp',
'inspect', 'itertools', 'jpeg', 'keyword', 'linecache', 'locale', 'logging',
'mailbox', 'mailcap', 'marshal', 'math', 'md5', 'mhlib', 'mimetools',
'mimetypes', 'MimeWriter', 'mimify', 'MiniAEFrame', 'mmap', 'modulefinder',
'msilib', 'msvcrt', 'multifile', 'mutex', 'Nav', 'netrc', 'new', 'nis',
'nntplib', 'operator', 'optparse', 'os', 'os.path', 'ossaudiodev', 'parser',
'pdb', 'pickle', 'pickletools', 'pipes', 'PixMapWrapper', 'pkgutil',
'platform', 'popen2', 'poplib', 'posix', 'posixfile', 'pprint', 'profile',
'pstats', 'pty', 'pwd', 'py_compile', 'pyclbr', 'pydoc', 'Queue', 'quopri',
'random', 're', 'readline', 'repr', 'resource', 'rexec', 'rfc822', 'rgbimg',
'rlcompleter', 'robotparser', 'runpy', 'sched', 'ScrolledText', 'select',
'sets', 'sgmllib', 'sha', 'shelve', 'shlex', 'shutil', 'signal',
'SimpleHTTPServer', 'SimpleXMLRPCServer', 'smtpd', 'smtplib', 'sndhdr',
'socket', 'SocketServer', 'spwd', 'sqlite3', 'stat', 'statvfs', 'string',
'StringIO', 'stringprep', 'struct', 'subprocess', 'sunau', 'symbol', 'sys',
'syslog', 'tabnanny', 'tarfile', 'telnetlib', 'tempfile', 'termios', 'test',
'test.test_support', 'textwrap', 'thread', 'threading', 'time', 'timeit',
'Tix', 'Tkinter', 'token', 'tokenize', 'trace', 'traceback', 'tty', 'turtle',
'types', 'unicodedata', 'unittest', 'urllib', 'urllib2', 'urlparse',
'UserDict', 'UserList', 'UserString', 'uu', 'uuid', 'videoreader', 'W',
'warnings', 'wave', 'weakref', 'webbrowser', 'whichdb', 'winsound', 'wsgiref',
'wsgiref.handlers', 'wsgiref.headers', 'wsgiref.simple_server',
'wsgiref.util', 'wsgiref.validate', 'xdrlib', 'xml.dom', 'xml.dom.minidom',
'xml.dom.pulldom', 'xml.etree.ElementTree', 'xml.parsers.expat', 'xml.sax',
'xml.sax.handler', 'xml.sax.saxutils', 'xml.sax.xmlreader', 'xmlrpclib',
'zipfile', 'zipimport', 'zlib', 'distutils.bcppcompiler',
'distutils.ccompiler', 'distutils.command.bdist_rpm',
'distutils.command.bdist_wininst', 'distutils.command.sdist',
'distutils.command.build_clib', 'distutils.command.bdist',
'distutils.command.bdist_dumb', 'distutils.command.bdist_packager',
'distutils.unixccompiler', 'distutils.mwerkscompiler', 'distutils',
'distutils.archive_util', 'distutils.cmd', 'distutils.command',
'distutils.command.build', 'distutils.command.build_py',
'distutils.command.build_scripts', 'distutils.command.clean',
'distutils.command.config', 'distutils.command.install_data',
'distutils.command.install_headers', 'distutils.command.install_lib',
'distutils.command.install_scripts', 'distutils.command.register',
'distutils.core', 'distutils.cygwinccompiler', 'distutils.debug',
'distutils.dep_util', 'distutils.dir_util', 'distutils.dist',
'distutils.emxccompiler', 'distutils.errors', 'distutils.extension',
'distutils.fancy_getopt', 'distutils.file_util', 'distutils.filelist',
'distutils.log', 'distutils.msvccompiler', 'distutils.spawn',
'distutils.sysconfig', 'distutils.text_file', 'distutils.util',
'distutils.version',]

# Some platform-specific modules that would just clutter the results
OBVIOUS = \
['Carbon.AE', 'Carbon.AH', 'Carbon.App',
'Carbon.CaronEvt', 'Carbon.CF', 'Carbon.CG', 'Carbon.Cm', 'Carbon.Ctl',
'Carbon.Dlg', 'Carbon.Evt', 'Carbon.Fm', 'Carbon.Folder', 'Carbon.Help',
'Carbon.List', 'Carbon.Menu', 'Carbon.Mlte', 'Carbon.Qd', 'Carbon.Qdoffs',
'Carbon.Qt', 'Carbon.Res', 'Carbon.Scrap', 'Carbon.Snd', 'Carbon.TE',
'Carbon.Win', 'macerrors', 'macfs', 'MacOS', 'macostools', 'macpath', 'macresource',
'SUNAUDIODEV', 'sunaudiodev',]

# Uncomment this line to also check modules that are "obviously" not supported
# under a system like GAE. May take longer. Some might even hang.
# PYTHON_2_5_MODULES += OBVIOUS

# These are known to have the potential to cause GAE to hang rather than
# raising an exception.
CAUSE_HANG = ['distutils.command.build_ext', 'distutils.command.install',]

# Cause various errors other than ImportError when imported
OTHER_ERRORS = ['site', 'user',]

#----------------------------------------------------------------------------#

if __name__ == '__main__':
    main()
    
#----------------------------------------------------------------------------#
