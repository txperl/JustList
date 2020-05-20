# JustList

> JustList, just the directory.
>
> Another simple file list and sharing tool for cloud storages.

It supports Cloud189, OneDrive, OneDrive CN and can include multiple users of several cloud storages at the same time. Of course, there is also a simple cache and an automatic refresh system.

* [Demo for JustList](https://lib.tls.moe/)
* [README_CN.md](README.md)

## Deploy

This program can be separated front-end and back-end, and the following are mainly back-end deployment instructions.

In a nutshell, it's only few simple steps.

* Install
* Edit configuration
* Enable cores
* Run

The following note may seem like a lot, but it actually contains very little (probably too much crap? hhh).

### Install dependencies

``` bash
$ pip3 install -r requirements.txt
```

### Edit configuration

#### Address of forced data-refresh

Edit `. /app/plugin/sys_update.py` and change `sys/update/xxxiiixxx` to the address you want.

**Be sure to edit this part (or disable this plugin)**! Otherwise it may be requested in bad faith.

#### Cloud189 (optional)

Edit `. /app/core/cloud189/config.json` .

``` 
{
    "accounts": {
        "cloud189_user1": [
            "<your_username>", // username
            "<your_password>", // password
            {} //cookie, with space for {}
        ],
        "cloud189_user2": [
            "<your_username>",
            "<your_password>",
            {}
        ]
    },
    "cant_enterFolder": [], // disabled folders, regular match
    "cant_visFile": ["\\... *?"] , // banned file names, regular match
    "only_Referrer": [], // simple anti-theft chain through allowed referrers. leave blank for all allowed. regular search
    "sys_checkTime": 60, // update task thread interval
    "sys_cookieExpiredTime": 3600, // cookie cache expiration time
    "sys_dataExpiredTime": 900, // file directory cache expiration time
    "sys_dl_urlExpiredNum": 30, // download link cache validity count
    "sys_dl_urlExpiredTime": 300 // download link cache expiration time
}
```

#### OneDrive (optional)

Edit `. /app/core/onedrive/config.json` .

``` 
{
    "accounts": {
        "onedrive_user1": [
            0, // 0 for international version, 1 for China version
            "" // refresh_token, the program will guide you if it's blank
        ],
        "onedrive_user2": [
            1,
            ""
        ]
    },
    "cant_enterFolder": [], // disabled folders, regular match
    "cant_visFile": ["\\... *?"] , // banned file names, regular match
    "only_Referrer": [], // simple anti-theft chain through allowed referrers. leave blank for all allowed. regular search
    "rootPath": "/", //root
    "sys_checkTime": 65, // update task thread interval
    "sys_dataExpiredTime": 1200, // file directory cache expiration time
    "sys_dl_urlExpiredNum": 30, // download link cache validity count
    "sys_dl_urlExpiredTime": 600 // download link cache expiration time
}
```

Note that the **usernames customized in the `accounts` in the above cannot be repeated**!

##### Refresh Token

If you leave this blank in the configuration, the program will automatically get the refresh_token after walking you to the code the first time you initialize, and it will be saved in the configuration file.

##### Client ID/Password

If you want to use your own client ID and password, please edit the `. /app/core/onedrive/onedrive.py` header variable.

For example.

``` python
clientId = [
    "78d4dc35-7e46-42c6-9023-2d39314433a5",
    "3ff8580b-62e2-47ea-94f1-47e41440122c",
]
```

The first one is for OneDrive International and the second one is for OneDrive CN.

### Enable cores

No services will be loaded by default. To enable the service, **edit each configuration correctly and then** enable the cores.

Edit `. /app/core/__init__.py` to remove the corresponding code.

``` python
from .onedrive.main import * # Turn on OneDrive
from .cloud189.main import * # Open Skywing Cloud

```

### Run

``` bash
$ python3 main.py
```

### Front-end and back-end separation (optional)

Not a necessary operation, but follow these steps to configure it if you want.

1. Edit `. /main.py` to remove the code `CORS(app, resources=r"/*")` . If you want to specify a domain, please edit it yourself.

(annotate `return render_template("md.html")` and `if` statements)

2. Edit `. /templates/md.html` and change `api_url` to the back-end address (without `/` at the end).

(If `only_Referrer` is set in the configuration file, please note the change)

## Description

* The program loads and caches all allowed files at once, so it may be slower if there are more files (depending on the number of files you have and the state of your network), but it does not affect normal operation
* Tested only on a small scale (Cloud189 x2, OneDrive INTL x1, OneDrive CN x1) with medium number of requests, files and run well
* Cloud storage operating code edited from [Aruelius/cloud189](https://github.com/Aruelius/cloud189), [MoeClub/OneList](https://github.com/MoeClub/OneList), thanks

## Declaration

* This procedure is for learning purposes only and should stop when the purpose has been achieved
* Any unknowable results after using is not the original author's business and the original author is not responsible for anything
* [MIT License] (https://choosealicense.com/licenses/mit/)

Happy using.

; )
