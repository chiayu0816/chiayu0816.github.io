### Linux Podman machint start failed question

Starting machine "podman-machine-default"
Error: unable to start host networking: "could not find \"gvproxy\" in one of {[/usr/local/libexec/podman /usr/local/lib/podman /usr/libexec/podman /usr/lib/podman] {<nil>}}.  To resolve this error, set the helper_binaries_dir key in the `[engine]` section of containers.conf to the directory containing your helper binaries."

下載 gvproxy
https://github.com/containers/gvisor-tap-vsock/releases

```shell
wget https://github.com/containers/gvisor-tap-vsock/releases/download/v0.8.1/gvproxy-linux-amd64
```

下載完成後，要將 gvproxy 移動到 Podman 預期的目錄中

/usr/local/libexec/podman 
/usr/local/lib/podman 
/usr/libexec/podman 
/usr/lib/podman

```shell
sudo mv gvproxy-linux-amd64 /usr/lib/podman
```

完成後，可以通過運行以下命令來驗證 gvproxy
```shell
gvproxy --version
```


Starting machine "podman-machine-default"
Waiting for VM ...
Error: qemu exited unexpectedly with exit code 1, stderr: Could not access KVM kernel module: Permission denied
qemu-system-x86_64: -accel kvm: failed to initialize kvm: Permission denied

錯誤信息顯示 qemu 無法訪問 KVM 內核模組，這通常是由於以下幾個原因造成:
1. KVM 模組未加載：KVM 模組可能未正確加載，可以通過以下命令檢查 KVM 模組是否存在：
```shell
lsmod | grep kvm
```
如果沒有輸出，則表示 KVM 模組未加載。 可以使用以下命令加載 KVM 模組：
```shell
sudo modprobe kvm

# Intel 處理器，則還需要加載 kvm-intel 模組
sudo modprobe kvm-intel

# AMD 處理器
sudo modprobe kvm-amd
```

2. 權限問題：確保當前用戶有權訪問 /dev/kvm。 可以使用以下命令檢查 /dev/kvm 的權限：
```shell
ls -l /dev/kvm
```
如果當前用戶不在 kvm 群組中，可以將用戶添加到 kvm 群組：
```
sudo usermod -aG kvm $USER
```
添加後，需要重新登錄或重啟系統以使更改生效。

3. 檢查 KVM 是否可用
```shell
egrep -c '(vmx|svm)' /proc/cpuinfo
```
如果輸出為 0，則表示 CPU 不支持 KVM，或者虛擬化未在 BIOS 中啟用。



Error: short-name "nginx" did not resolve to an alias and no unqualified-search registries are defined in "/etc/containers/registries.conf"

打開 /etc/containers/registries.conf 文件
```
sudo nano /etc/containers/registries.conf
```

找到 unqualified-search-registries 的行，並將其設置為包含 docker.io
`unqualified-search-registries = ["docker.io"]`