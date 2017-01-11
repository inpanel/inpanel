# Adapted from here: https://gist.github.com/489093
# Original credit goes to pplante and copyright notice pasted below

# Copyright (c) 2010, Philip Plante of EndlessPaths.com
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
# from handlers.base import BaseHandler
# 
# import tornado.web
# from tornado import gen
# from async_process import call_subprocess, on_subprocess_result
# 
# class ShellHandler(BaseHandler):
#     @tornado.web.asynchronous
#     @gen.engine
#     def get(self):
#         self.write("Before sleep<br />")
#         self.flush()
#         response = yield gen.Task(call_subprocess, self, "ls /")
#         self.write("Output is:\n%s" % (response.read(),))
#         self.finish()
#


# Modifications Copyright (c) 2012, Hily Jiang of vpsmate.org
# License remains as above
#
# Modify to:
# * prevent blocking and the zombie process
# * prevent process handup when command fail to run
# * add a callbackable decorator
#
# We change ioloop.READ event to ioloop.ERROR to make callback
# invoke after the process end. And it can prevent blocking when the
# process is running.
# We make a Popen.wait() at the end to prevent the zombie process.


import logging
import shlex
import subprocess
import tornado

def call_subprocess(context, command, callback=None, shell=False):
    context.ioloop = tornado.ioloop.IOLoop.instance()
    if not shell: command = shlex.split(command)
    try:
        context.pipe = p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True, shell=shell)
        context.ioloop.add_handler(p.stdout.fileno(), context.async_callback(on_subprocess_result, context, callback), context.ioloop.ERROR)
    except:
        if callback: callback((-1, ''))

def on_subprocess_result(context, callback, fd, result):
    try:
        context.pipe.wait()
        if callback:
            callback((context.pipe.returncode, context.pipe.stdout.read()))
    except Exception, e:
        logging.error(e)
    finally:
        context.ioloop.remove_handler(fd)

def callbackable(func):
    """Make a function callbackable.
    """
    def wrapper(*args, **kwds):
        callback = kwds['callback']
        if callback: del kwds['callback']
        result = func(*args, **kwds)
        if callback:
            return callback(result)
        else:
            return result
    return wrapper