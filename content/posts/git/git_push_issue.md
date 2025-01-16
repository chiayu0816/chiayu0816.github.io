---
title: "Git non-fast-forward, diverged problem processing"
date: 2025-01-15
categories: ["Git"]
---

今日在將本地測試的專案更改推送到遠端時遇到了一些錯誤，在這裡做個記錄.

```bash
 ! [rejected]        mian -> mian (non-fast-forward)
error: failed to push some refs to 'github.com:chiayu0816/test.git'
```

使用 git status命令查看問題

```bash
git status
```

發現下面問題

```bash
Your branch and 'origin/mian' have diverged,
and have 1 and 1 different commits each, respectively.
```

表示本地和遠端都有新的提交，需要先整合才能推送

```bash
git pull --rebase origin mian
```

出現錯誤

```bash
error: cannot pull with rebase: You have unstaged changes.
error: please commit or stash them.
```

問題處理
1. 先提交當前的變更：
```bash
git add . && git commit -m "Remove .idea directory from git tracking"
```
2. 現在再次嘗試 rebase：
```bash
git pull --rebase origin mian
```

又出現錯誤
```bash
error: cannot pull with rebase: You have unstaged changes.
error: please commit or stash them.
```
再執行 `git status` 出現下面訊息
```bash
On branch mian
Your branch and 'origin/mian' have diverged,
and have 3 and 1 different commits each, respectively.
  (use "git pull" to merge the remote branch into yours)

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
        modified:   ../.gitignore
```

有一些上層目錄的更改，先進行暫存
```bash
git stash
```

再次 rebase
```bash
git pull --rebase origin mian
```

出現錯誤
```bash
error: The following untracked working tree files would be overwritten by merge:
 my-test-project/.idea/
 .
 .
 .
Please move or remove them before you merge.
```

先清理本地的 .idea 目錄：
```bash
rm -rf .idea/
```

中止先前的 rebase, 再次嘗試 rebase：
```bash
git rebase --abort && git pull --rebase origin mian
```

成功 rebase, 重新推送更改
```bash
git push origin mian --force
```

恢復之前暫存的更改
```bash
git stash pop
```

## 重要觀念
1. **Fast-Forward**：當本地分支包含遠端分支的所有提交時，Git 可以直接將遠端分支指向本地分支的最新提交。
2. **Non-Fast-Forward**：當本地分支和遠端分支各自有新的提交時，需要先整合這些更改。
3. **Rebase**：重新應用本地提交到遠端分支的最新狀態上，保持提交歷史的整潔。
4. **Force Push**：強制更新遠端分支，覆蓋遠端的提交歷史（使用時需謹慎）。

## 注意事項
1. 使用 `force push` 時要特別小心，因為它會覆蓋遠端的提交歷史
2. 在團隊協作時，建議先與團隊成員溝通後再使用 `force push`
