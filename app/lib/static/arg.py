# coding=utf-8
from flask import request

from altfe.interface.root import interRoot


@interRoot.bind("arg", "LIB_STATIC")
class static_arg(object):
    @staticmethod
    def gets(li, ty="GET"):
        sym = {"{_none}": None, "{_blank}": "", "{_()}": ()}
        if request.method != ty:
            raise AttributeError("bad request")
        fun = request.args if ty == "GET" else request.json
        rst = {}
        for x in li:
            c = x.split("=")
            req = fun.get(c[0]) if fun else None
            if not req:
                if len(c) == 2:
                    rst[c[0]] = str(c[1]) if c[1] not in sym else sym[c[1]]
                else:
                    raise AttributeError("missing parameters: %s" % c[0])
            else:
                rst[c[0]] = req
        return rst

    @staticmethod
    def pure(fun, li):
        for x in li:
            fun[li[x]] = fun[x]
            del fun[x]
