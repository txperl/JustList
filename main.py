import logging
import os
import sys

from flask import Flask, jsonify, render_template, abort
from gevent import monkey
from gevent.pywsgi import WSGIServer

from altfe import bridge, handle
from altfe.interface.root import classRoot

monkey.patch_all()

app = Flask(__name__)


# CORS(app, resources=r"/*")


# 路由
@app.route("/favicon.ico")
def favicon():
    return abort(404)


@app.route("/")
def render():
    return render_template("md.html")


@app.route("/<path:path>", methods=['GET', 'POST'])
def run(path):
    rep = handle.handleRoute.do(path)
    if type(rep) == dict:
        code = rep["code"]
        if code == 0:
            status = 400
        elif code == 1:
            status = 200
        else:
            status = code
        return jsonify(rep), status
    else:
        return rep


if __name__ == '__main__':
    # Altfe 框架初始化
    classRoot.setENV("rootPath", os.path.split(os.path.realpath(sys.argv[0]))[0] + "/")
    bridge.bridgeInit().run()

    # 调整日志等级
    logging.getLogger("werkzeug").setLevel(logging.ERROR)

    # 启动
    app.run(host="127.0.0.1", port=5000, debug=True, threaded=True, use_reloader=False)
    # http_server = WSGIServer(("127.0.0.1", 5000), app)
    # http_server.serve_forever()
