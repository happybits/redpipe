# -*- coding: utf-8 -*-

"""
Utility classes and functions for LUA scripts
"""

from .connections import ConnectionManager


class SmartScript(object):
    """
    Represents a registered LUA script that can be executed via EVAL or
    EVALSHA dynamically
    """

    CMD_EVAL = "eval"
    CMD_EVALSHA = "evalsha"

    def __init__(self, code, sha, use_evalsha_cb=None):
        self.code = code
        self.sha = sha
        self._use_evalsha_cb = use_evalsha_cb if use_evalsha_cb is not None \
            else lambda: True

    def use_evalsha(self):
        return self._use_evalsha_cb()


def register_smart_script(conn_name, code, use_evalsha_cb):
    """
    Returns a "smart" script object that can be passed to the eval_smart()
    command and dynamically invoke either EVALSHA or EVAL depending on the
    result of the given callback.  This allows the calling application to e.g.
    handle issues with scripts getting flushed from memory by reverting to
    normal EVAL commands until the issue is resolved.  The use_evalsha_cb
    unction should be extremely lightweight sicne it is invoked before each
    smart_eval command is executed.

    @param conn_name: str - the name of the DB connection to use
    @param code: str - the LUA source code for the script
    @param use_evalsha_cb: function - no args, returns True if EVALSHA should
                                        be used, False if EVAL should be used.
    """
    pipe = ConnectionManager.get(conn_name)
    pipe.script_load(code)
    sha = pipe.execute(raise_on_error=True)[0]
    return SmartScript(code, sha, use_evalsha_cb)
