# JustList

> JustList，仅仅是目录。
>
> 没错，又一款简单的网盘文件列表与分享工具。

支持天翼云盘、OneDrive、OneDrive 世纪互联，可以同时启用多个云盘的多个用户。当然，也有一个简单的缓存与自动刷新系统。

* [Demo for JustList](https://lib.tls.moe/)

## 部署

本程序可前后端分离，以下主要为后端部署说明。

总的来说，很简单的几步：

* 安装程序与依赖
* 修改云盘配置项
* 启用核心
* 运行

下述说明看似很多，其实内容很少（可能是废话太多了？hhh）。

### 1. 安装依赖

``` bash
$ pip3 install -r requirements.txt
```

### 2. 修改配置

#### 2.1. 天翼云盘（可选）

编辑 `./app/core/cloud189/config.json` 。

``` 
{
    "accounts": {
        "cloud189_user1": [
            "<your_username>",     // 用户名
            "<your_password>",     // 密码
            {}                     // cookie，可留空为 {}（但必须存在）
        ],
        "cloud189_user2": [
            "<your_username>",
            "<your_password>",
            {}
        ]
    },
    "cant_enterFolder": [          // 禁止访问的文件夹，正则 match
        "同步盘",
        "我的.."
    ],
    "cant_visFile": [              // 禁止文件名，正则 match
        "\\..*?"
    ],
    "only_Referrer": [],           // 简单防盗链，允许的 Referrer，留空为全部允许，正则 search
    "rootPath": "/",               // 根目录
    "sys_checkTime": 60,           // 更新任务线程间隔
    "sys_cookieExpiredTime": 3600, // cookie 缓存有效时间
    "sys_dataExpiredTime": 900,    // 文件目录缓存有效时间
    "sys_dl_urlExpiredNum": 30,    // 下载链接缓存有效次数
    "sys_dl_urlExpiredTime": 300   // 下载链接缓存有效时间
}
```

#### 2.2. OneDrive（可选）

编辑 `./app/core/onedrive/config.json` 。

``` 
{
    "accounts": {
        "onedrive_intl": [
            0,                   // 0 为国际版，1 为世纪互联
            ""                   // refresh_token，留空时程序会引导填写，也可提前填写（但必须存在此字段）
        ],
        "onedrive_cn": [
            1,
            ""
        ]
    },
    "cant_enterFolder": [],      // 禁止访问的文件夹，正则 match
    "cant_visFile": [            // 禁止文件名，正则 match
        "\\..*?"
    ],
    "only_Referrer": [],         // 简单防盗链，允许的 Referrer，留空为全部允许，正则 search
    "rootPath": "/",             // 根目录
    "sys_checkTime": 65,         // 更新任务线程间隔
    "sys_dataExpiredTime": 1200, // 文件目录缓存有效时间
    "sys_dl_urlExpiredNum": 30,  // 下载链接缓存有效次数
    "sys_dl_urlExpiredTime": 600 // 下载链接缓存有效时间
}
```

注意，以上两个配置文件中 `accounts` 中自定义的**多用户用户名不可重复**！

##### 2.2.1 Client ID 等更改

**如果你遇到与 Token 验证相关的错误，请务必尝试修改此项。**

如果想使用自己的客户端 ID 和密码，请修改 `./app/core/onedrive/onedrive.py` 头部的变量。

例如，

``` 
clientId = [
    "78d4dc35-7e46-42c6-9023-2d39314433a5",
    "dfe36e60-6133-48cf-869f-4d15b8354769",
]
```

第一行为 OneDrive 国际版的，第二行为世纪互联版的。

### 3. 启用核心

默认不会加载任何服务。若要开启服务，请**正确修改各配置后**启用加载核心。

编辑 `./app/core/__init__.py` ，取消相应注释即可。

``` python
from .onedrive.main import * # 开启 OneDrive
from .cloud189.main import * # 开启 天翼云盘
```

#### 3.1. 强制刷新目录缓存（可选）

如果需要强制刷新目录缓存，请先编辑 `./app/plugin/__init__.py` ，取消 `sys_update` 注释。

编辑 `./app/plugin/sys_update.py` ，将 `sys/update/xxxiiixxx` 改为你想要的强制刷新地址。

**默认为停用状态，若要开启请务必修改地址**！否则可能会被恶意请求。

### 4. 启动程序

``` bash
$ python3 main.py
```

若要更改程序的运行地址，请修改 `./main.py`，默认为 `http://127.0.0.1:5000/`。

### 5. 前后端分离（可选）

不是必要的操作，但如果你想的话，请按照以下步骤配置。

1. 编辑 `./main.py` ，将 `CORS(app, resources=r"/*")` 取消注释，并将 `return render_template("md.html")` 及 `if` 语句注释。
2. 编辑 `./templates/md.html` ，将 `api_url` 改为后端运行地址即可（结尾不含 `/` ）。

### 6. 其他

#### 6.1. md 主题的默认显示用户

若要自定义前端 md 主题的默认显示用户，即优先显示的网盘文件列表，可修改 `./templates/md.html` 中 `root_user` 一项。

## 开发

### 目录

``` 
├── app
├── ├── __init__.py
├── ├── core           // 核心 //
├── ├── ├── __init__.py       // 开关
├── ├── ├── args              // 请求参数获取
├── ├── ├── cache             // 缓存
├── ├── ├── file              // 文件操作
├── ├── ├── cloud189          // 天翼云盘核心
├── ├── ├── onedrive          // OneDrive 核心
├── ├── plugin         // 插件 //
├── ├── ├── __init__.py       // 开关
├── ├── ├── do_file.py        // 文件直链跳转
├── ├── ├── get_list.py       // 网盘目录
├── ├── ├── get_text.py       // 文件内容获取
├── ├── ├── sys_update.py     // 强制刷新网盘目录缓存
├── ├── platform.py           // 提供核心、插件的注册和调用（中转）
├── templates         // 前端页面
├── .gitattributes
├── .gitignore
├── main.py           // 运行
├── README.md
```

简略框架说明可以查看 [PixivBiu-后端](https://biu.tls.moe/#/develop/backend)。

### API

此部分可自行修改插件以更改。

1. `api/get/list`
* **获取网盘的目录**
* 示例
  + `api/get/list` : 返回全部目录
  + `api/get/list/user1/a/x` : 返回 user1 的 a 目录下的 x 目录/文件（如果存在）
  + `api/get/list/user2/?id=xxx` : 返回 user2 的 id 为 xxx 的目录/文件 

2. `api/get/text`
* **获取文件的内容**
* 示例
  + `api/get/text/user1/a/x` : 返回 user1 的 a 目录下的 x 文件内容（如果存在）
  + `api/get/text/user2/?id=xxx` : 返回 user2 的 id 为 xxx 的文件内容

3. `file`
* **直链跳转（下载文件）**
* 示例
  + `file/user1/a/x` : 重定向至 user1 的 a 目录下的 x 文件下载链接（如果存在）
  + `file/user2/?id=xxx` : 重定向至 user2 的 id 为 xxx 的文件的下载链接

4. `sys/update/xxxiiixxx`
* **强制刷新网盘目录缓存**

## 说明

* 本程序会一次性加载全部允许的文件并缓存，所以若文件较多此过程可能会较慢（取决于你文件的数量与网络状况），但不影响正常运行
* 仅在小规模（天翼云盘x2、OneDrive 国际版x1、世纪互联版x1）且请求、文件数量中等的情况下测试，运行稳定
* 网盘操作代码修改自 [Aruelius/cloud189](https://github.com/Aruelius/cloud189)、[MoeClub/OneList](https://github.com/MoeClub/OneList)，感谢

## 声明

* 本程序仅供学习参考，请在达成目的后停止使用
* 使用后任何不可知事件都与原作者无关，原作者不承担任何后果
* [MIT License](https://choosealicense.com/licenses/mit/)

使用愉快。

; )
