# coding=utf-8
# pylint: disable=relative-beyond-top-level
import json
import time
import os


class io:
    @staticmethod
    def ain(uri, mode="r"):
        if not os.path.exists(uri):
            return False
        try:
            with open(uri, mode) as f:
                fileType = uri.split(".")[-1]
                if fileType == "json":
                    f = json.load(f)
        except:
            print("\033[31m[failed-load] %s\033[0m" % (uri))
            return False
        return f

    @staticmethod
    def aout(uri, data, mode="w", dRename=False):
        if not uri:
            return False

        uri = uri.replace("\\\\", "/").replace("\\", "/").replace("//", "/")

        uriDir = ""
        fileName = ""
        # 获取文件路径
        for x in uri.split("/")[:-1]:
            uriDir = uriDir + x + "/"
        # 获取文件名
        for x in uri.split("/")[-1].split(".")[:-1]:
            fileName = fileName + x + "."
        fileName = fileName[:-1]
        # 获取文件类型
        fileType = uri.split("/")[-1].split(".")[-1]
        # 检测路径中文件夹是否存在，无则创建
        if uriDir != "" and not os.path.exists(uriDir):
            os.makedirs(uriDir)
        # 检测是否有重名文件，有则将文件名改为 x_time
        if dRename and os.path.exists(uri):
            uri = uriDir + fileName + "_" + str(int(time.time())) + "." + fileType

        try:
            if fileType == "json":
                data = json.dumps(
                    data,
                    ensure_ascii=False,
                    sort_keys=True,
                    indent=4,
                    separators=(", ", ": "),
                )
                with open(uri, mode, encoding="utf8") as f:
                    f.write(data)
            else:
                with open(uri, mode) as f:
                    f.write(data)
        except:
            print("\033[31m[failed-save] %s -> %s\033[0m" % (fileName, uri))
            return False
        print(
            "\033[32m[saved]\033[0m \033[36m%s\033[0m -> \033[36m%s\033[0m"
            % (fileName, uri)
        )
        return True

    @staticmethod
    def rm(uri):
        if not os.path.exists(uri):
            return False
        try:
            os.remove(uri)
        except:
            print("\033[31m[failed-remove] %s\033[0m" % (uri))
            return False
        print("\033[32m[removed]\033[0m \033[36m%s\033[0m" % (uri))
        return True
