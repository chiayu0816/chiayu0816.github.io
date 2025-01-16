---
title: "File cannot be added to git"
date: 2025-01-13
categories: ["Git"]
---

**專案檔案突然全部都無法加入Git, 查看 .gitignore 檔案都沒有問題，原因竟是 exclude file...**

使用以下指令來檢查為什麼這個路徑被忽略
```bash
git check-ignore -v my-project
```
發現不知道什麼時候誤將整個專案加到 exclude file...
```
.git/info/exclude:10:/my-project/	my-project
```
刪除後，就正常了!


如果檔案或目錄加入 .gitignore 前, 就已加入版本控制怎麼處理?
```bash
git rm -r --cached .idea/
```
