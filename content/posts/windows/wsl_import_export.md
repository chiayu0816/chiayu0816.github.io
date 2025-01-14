---
title: "wsl export / import"
categories: ["WSL"]
---

### List Installed WSL Distributions:

```shell
wsl --list --all
```
This will display a list of all WSL distributions, including their names (e.g., Ubuntu, Debian, etc.).

### Export the WSL Distribution:
```shell
wsl --export <DistributionName> <FilePath>

# Example
# wsl --export Ubuntu C:\Backups\ubuntu-backup.tar
```
This will create a .tar file containing the entire WSL distribution.
Check the specified location to ensure the .tar file has been created successfully.

**If you're using WSL 2, you can export the distribution as a .vhdx file instead of a .tar file by using the --vhd option:**
```shell
wsl --export --vhd <DistributionName> <FilePath>
```


### Import the WSL Image
```shell
wsl --import <DistributionName> <InstallLocation> <FilePath> [--version <WSLVersion>]

# Example
# wsl --import Ubuntu_Custom C:\WSL\Ubuntu_Custom C:\Backups\ubuntu-backup.tar --version 2
```
This command imports the WSL image from C:\Backups\ubuntu-backup.tar, stores it in C:\WSL\Ubuntu_Custom, and sets it to use WSL 2.

###  Verify the Imported Distribution
```shell
wsl --list --all
```
This will display a list of all installed WSL distributions, including the newly imported one.


### Set the Default Distribution (Optional)
```shell
wsl --set-default <DistributionName>

# Example
# wsl --set-default Ubuntu_Custom
```