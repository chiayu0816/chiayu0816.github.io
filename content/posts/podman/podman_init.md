### 初始化 Podman 
``` shell
podman machine init
podman machine start
```

### 測試容器運行
```shell
podman run -d -p 8080:80 nginx
```

### 檢查運行中的容器
``` shell
podman ps
```

### 測試 Nginx 服務
在瀏覽器中訪問 `http://localhost:8080` 應該能看到 Nginx 的歡迎頁面，這表示容器運行正常

測試完成後，可以停止並刪除容器
```shell

# <container_id> podman ps 命令中看到的容器 ID
podman stop <container_id>
podman rm <container_id>
```