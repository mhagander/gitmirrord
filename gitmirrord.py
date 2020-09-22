#!/usr/bin/python3 -u
#
# gitmirrord.py - simple script to trigger git push to mirrors upon being
#                 pinged.
#

from flask import Flask, request, abort, make_response
import configparser
import os
import subprocess
import sys
import re
import threading
from queue import Queue


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


class ReloadingConfigParser(object):
    def __init__(self, filename):
        self.filename = filename
        self._load()

    def _load(self):
        self.loadtime = os.stat(self.filename).st_mtime
        self.parser = configparser.ConfigParser()
        self.parser.read(self.filename)

    def __getattr__(self, name):
        return getattr(self.parser, name)

    def refresh(self):
        if os.stat(self.filename).st_mtime != self.loadtime:
            eprint("Reloading configuration")
            self._load()


cfg = ReloadingConfigParser('gitmirrord.ini')
app = Flask('gitmirrord')
queue = Queue()


@app.route("/mirror/<repository>", methods=['GET', 'POST'])
def mirror(repository):
    cfg.refresh()
    if not cfg.has_section(repository):
        return "Repo not found", 404
    if not cfg.has_option(repository, 'path') or not cfg.has_option(repository, 'remote'):
        return "Repo misconfigured", 500

    if cfg.has_option(repository, 'timeout'):
        timeout = int(cfg.get(repository, 'timeout'))
    else:
        timeout = 60

    queue.put((cfg.get(repository, 'path'), cfg.get(repository, 'remote'), timeout))

    r = make_response("Mirror request queued.")
    r.mimetype = 'text/plain'
    return r


@app.before_request
def limit_remote_addr():
    if request.remote_addr not in ('127.0.0.1', '::1'):
        abort(403)


def mirror_worker():
    while True:
        (path, remote, timeout) = queue.get()
        print("Running push from {} to {}".format(path, remote))
        try:
            subprocess.run(['git', 'push', remote, '--all'], cwd=path, timeout=timeout, check=True)
            subprocess.run(['git', 'push', remote, '--tags'], cwd=path, timeout=30, check=True)
        except Exception as e:
            print("Failed in git push command: {}".format(e), file=sys.stderr)
        print("Push from {} to {} completed".format(path, remote))

        queue.task_done()


if __name__ == "__main__":
    workerthread = threading.Thread(target=mirror_worker)
    workerthread.start()

    app.run(debug=False, host="127.0.0.1", port=9992)
