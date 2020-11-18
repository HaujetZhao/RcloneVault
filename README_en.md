[中文](./README.md)   [English](./README_en.md) 

# Purpose

Crypt-type remote of rclone can be used as users File Vault, and this script is ment to make managing, editing, opening and closing File Vaults easier. 

# Introduce: 

Rclone is a open source storage manage tool, it supports multi kinds of local and cloud storage. 

Rclone supports a storage type called "Crypt", it's actually adding a crypt layer on top of a normal storage layer. 

By using this crypt layer, files will be crypted by AES algorism using 256 bit key before it written to the normal storage. 

So only by passing this crypt layer and correct password, you can read the original file. 

You can only read the random bytes on the normal storage.

This crypt layer can be applied to any kinds of storage, the crypt process is transparent, not container crypt. 

So you can safely upload the crypted folder to the cloud storage without worrying your privacy leaking.

Downside of this crypt method: 
* All the file within the Vault are crypted by user password, so you can't change the password. 
  The only way to change password is the open the old vault, then copying the files into another vault with different password. Decrypt then recrypt.
* When using a password opening a folder, there won't be a error prompt. Rclone just uses this password to apply a crypt layer. Only when you input the
  right password, the files written before can be correctly shown and read.

So when using rclone vault, you must keep your password remembered. If passwd forgotten, you will lose your data forever! 
I suggest you use a password manager like Keepass to take care of your passwords.

Rclone has many ways to manage your vault. This script only use the server and mount feature. 
aka: Serve your vault by webdav, ftp, sftp, http protocal, or mount your vault to a path, to let users visit. 
When served, other devices like your phone will be able to access you PC vault or vice versa, in the meantime, you can also set a access account! 

Advantages：

* Rclone is written in go, opensource, hight efficiency performance, cross platform. No worry about safety and compatibility. 

Dependencies：
* Rclone installed
* Mount function requires FUSE, Windows users need first install [winfsp](https://github.com/billziss-gh/winfsp/releases) 
* Before you run this script, please install python dependencies：pip install stdiomask pycryptodome

Usage：

After installing Rclone and Python dependencies, you can just run this script using python, there will be text guide then.

You can edit or add your vault in the USER EDIT REGION below. 

Vaults created in this script can also be added to rclone config. 

