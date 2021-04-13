import hashlib
import re

import bcrypt

from altfe.interface.root import interRoot


@interRoot.bind("util", "LIB_STATIC")
class static_util(object):
    @classmethod
    def filterVerifyPassword(cls, li, allPassword={}, password=(), index=0):
        r = []
        for i in range(len(li)):
            file = li[i].copy()
            if file["isSecret"]:
                if len(password) > index and cls.verifyBcryptPassword(password[index], allPassword[file["fileId"]]):
                    index += 1
                else:
                    if file["isFolder"]:
                        file["child"] = []
                        r.append(file)
                    continue
            if file["isFolder"]:
                file["child"] = cls.filterVerifyPassword(file["child"], allPassword, password, index)
            r.append(file)
        return r

    @classmethod
    def process_addPassword(cls, arr, passwords={}):
        """
        查找用户列表文件中的加密文件夹。
        :param arr: 用户网盘列表
        :param passwords: 密码集
        :return: dict@{fileId: password}
        """
        for file in arr:
            if file["isFolder"]:
                for i in range(len(file["child"])):
                    child = file["child"][i]
                    if "._.jl" in child["fileName"]:
                        passwords[file["fileId"]] = child["fileName"][:-5]
                        file["isSecret"] = True
                        del file["child"][i]
                        break
                cls.process_addPassword(file["child"], passwords)
        return passwords

    @classmethod
    def process_locateByID(cls, arr, fid, r):
        r[fid] = True
        for file in arr:
            if fid == file["fileId"]:
                r[0] = [file]
                return
            if len(r[0]) == 0 and file["fileId"] not in r:
                cls.process_locateByID(file["child"], fid, r)
        return

    @staticmethod
    def locateByPath(now, path):
        for i in range(1, len(path)):
            nothing = True
            looking = path[i]
            for file in now:
                if looking == file["fileName"]:
                    if i == len(path) - 1:
                        return [file]
                    if file["isFolder"] and file["child"] != []:
                        nothing = False
                        now = file["child"]
                        break
            if nothing:
                break

        return []

    @staticmethod
    def verifyBcryptPassword(hashed, password):
        try:
            return bcrypt.checkpw(str(password).encode('utf8'), str(hashed).encode('utf8'))
        except:
            return False

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
            for x in conf["cant_visFile"]:
                if re.match(x, fileName) is not None:
                    isPass = True
                    break
        else:
            for x in conf["cant_enterFolder"]:
                if re.match(x, fileName) is not None:
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
