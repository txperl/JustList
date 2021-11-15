import hashlib
import re

import bcrypt

from altfe.interface.root import interRoot


@interRoot.bind("util", "LIB_STATIC")
class static_util(object):
    @staticmethod
    def isNeedLoad(isFolder, fileName, conf):
        """
        根据配置项判断是否需要跳过某一文件或文件夹。
        :param isFolder: 是否是文件夹
        :param fileName: 文件名
        :param conf: 配置项
        :return: bool
        """
        isPass = False
        if not isFolder:
            if conf["cant_visFile"] is None:
                return False
            for x in conf["cant_visFile"]:
                if re.match(str(x), fileName) is not None:
                    isPass = True
                    break
        else:
            if conf["cant_enterFolder"] is None:
                return False
            for x in conf["cant_enterFolder"]:
                if re.match(str(x), fileName) is not None:
                    isPass = True
                    break
        return isPass

    @staticmethod
    def md5(c):
        md5 = hashlib.md5()
        md5.update((c).encode(encoding="utf-8"))
        return md5.hexdigest()

    @staticmethod
    def pureSize(size, dig=2, space=1):
        """
        格式化文件 size。
        :param size: int: 文件大小
        :param dig: int: 保留小数位数
        :param space: int: 大小与单位之间的空格数量
        :return:
        str: 格式化的 size，如 "1.23 MB"
        """
        units = ["B", "KB", "MB", "GB", "TB", "PB"]
        unit_index = 0
        K = 1024.0
        while size >= K:
            size = size / K
            unit_index += 1
        return ("%." + str(dig) + "f" + " " * space + "%s") % (size, units[unit_index])
