[中文](./README.md)　|　[English](./README_en.md) 

[Gitee](https://gitee.com/haujet/RcloneVault)　|　[Github](https://github.com/HaujetZhao/RcloneVault) 

# 用途

rclone 的 crypt 存储类型，可以作为用户透明加密文件的保险库，本脚本可以方便管理 rclone crypt 保险库，方便地打开和关闭保险库

# 介绍

[rclone](https://rclone.org/) 是一个开源的存储管理工具，支持多种本地和云盘存储。

[rclone](https://rclone.org/) 支持一种 [crypt](https://rclone.org/crypt/) 格式的存储，其实就是在普通存储层上加了一层加密层。

通过这层加密层，写入到普通存储上的文件，就被 256 位密钥的 AES 算法加密了。

只有通过这层加密层和正确的密码，才能读取到原始的文件

而在普通存储上读取到的就是乱码密文

这种加密层可以加到任何存储上，加密过程也是透明加密，而不是容器加密，你可以放心地将加密后的文件夹上传到网盘，而不用担心泄密



这种加密方式的缺陷有：

  * 所有保险库内的文件都是使用用户密码加密的，所以无法改密码。唯一改密码的方式就是先打开保险库，再将保险库的文件复制到另一个密码不同的保险库中，解密再加密。

  * 你在使用一个密码打开一个文件夹时，不会有错误提示。rclone 只负责用该密码在指定文件夹上打开一个加密层。只有当输入的密码和之前的密码相同时，才能正确读取到之前写入的文件。

  

所以，在使用保险库时，一定要记好你的密码，一旦忘记了，数据是找不回来的！建议使用 keepass 之类的密码管理器保管密码。



rclone 管理保险库有多种方式，本脚本仅使用它的 server 和 mount 功能

即：将加密层映射到 webdav、ftp、sftp、http 服务上，或者挂载到指定目录，供用户访问

当映射到 webdav 等网络协议时，就可以方便同一局域网的设备访问，同时，还可以设置访问密码



优点：

rclone 是 go 语言写的开源软件，高效，跨平台，在各种系统上都能用，所以无需担心加密不安全，无需担心跨平台兼容问题



依赖：

  * 如上所说，本脚本的加密依赖于 rclone，所以请先确保安装了 rclone 才能使用。

  * 需要注意的是，rclone 的挂载功能依赖于 FUSE，所以在 Windwos 上挂载需要先安装 [winfsp](https://github.com/billziss-gh/winfsp/releases) 

   Linux 系统上也需要有 FUSE 启用。

  * 在使用脚本前，请先安装 python 依赖：`pip install stdiomask pycryptodome`



使用方法：

在安装 rclone 和 python 依赖后，直接用 python 运行该脚本就可以用了，会有文字交互引导你。

你可以在脚本下面的  用户编辑区 编辑、增减你的保险库。

在本脚本中创建的保险库，也可以添加到 rclone 的配置文件中。rclone 是一个命令行软件，你可以到 [Rclone 文档部分翻译](https://ld246.com/article/1600853705300) 看下我的学习笔记

