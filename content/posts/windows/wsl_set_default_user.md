---
title: "wsl change default"
categories: ["WSL"]
---

### WSL 設定預設用戶

在WSL實例中，編輯/etc/wsl.conf文件

```shell
nano /etc/wsl.conf
```

添加以下內容
```shell
[user]
default=用戶名
```

退出WSL並在PowerShell中執行以下命令重啟WSL：
```shell
wsl --terminate <Distro>
```