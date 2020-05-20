# coding=utf-8
from app.platform import CMDProcessor
from flask import Flask, render_template, jsonify, request, abort
from flask_cors import CORS
from gevent.pywsgi import WSGIServer
import logging
import sys
import os

app = Flask(__name__)
# CORS(app, resources=r"/*")


@app.route("/favicon.ico")
def favicon():
    return abort(404)


# 路由
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def run(path):
    if path == "":
        return render_template("md.html")

    rep = CMDProcessor().process(path)
    if type(rep) == dict:
        return jsonify(rep)
    else:
        return rep


if __name__ == "__main__":
    logging.getLogger("werkzeug").setLevel(logging.ERROR)  # 调整日志等级

    # app.run(host="127.0.0.1", port=5000, debug=True, threaded=True)
    http_server = WSGIServer(("127.0.0.1", 5000), app)
    http_server.serve_forever()
