#!/usr/bin/env python
# encoding: utf-8

# Copyright (c) 2016-2017, Stadt Karlsruhe (www.karlsruhe.de)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the 'Software'), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

'''
Tests for the geoextract package.
'''


from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import errno
import json
import os
import signal
import threading
import time

import requests


def wait_for_server(url, max_tries=10, delay=1):
    '''
    Wait until a server responds to HTTP GET.
    '''
    for i in range(max_tries):
        try:
            requests.get(url)
            return
        except requests.ConnectionError:
            if i == max_tries - 1:
                # Last try failed
                raise
            time.sleep(delay)
            continue
    assert False


def wait_for_process(pid, timeout=None):
    '''
    Wait for a process to finish, possibly with a timeout.

    ``timeout`` specifies the timeout in seconds. A timeout of ``None``
    waits indefinitely.

    Returns ``True`` if the process exited in time.
    '''
    exited = threading.Event()

    def target():
        try:
            os.waitpid(pid, 0)
        except OSError as e:
            if e.errno != errno.ESRCH:
                raise
        exited.set()

    thread = threading.Thread(target=target)
    thread.start()
    thread.join(timeout)
    return exited.is_set()


def stop_process(pid, delay=None):
    '''
    Stop a process.

    Stops the process by first sending it SIGINT, then SIGTERM, and
    finally SIGKILL after waiting for ``delay`` seconds after each
    signal.
    '''
    for s in signal.SIGINT, signal.SIGTERM, signal.SIGKILL:
        try:
            os.kill(pid, s)
        except OSError as e:
            if e.errno == errno.ESRCH:
                return
            raise
        if wait_for_process(pid, delay):
            break


def sort_as_json(values):
    '''
    Sort a list of values according to their JSON representation.
    '''
    return sorted(values, key=json.dumps)
