# 用途：rclone 的 crypt 存储类型，可以作为用户透明加密文件的保险库，本脚本可以方便管理 rclone crypt 保险库，方便地打开和关闭保险库
# 作者：淳帅二代  https://github.com/HaujetZhao   https://gitee.com/haujet   https://space.bilibili.com/62637562
# 编写日期：2020年11月17日

# Purpose:
#   Crypt-type remote of rclone can be used as users File Vault, and this script is ment
#   to make managing, editing, opening and closing File Vaults easier. 

# 介绍：rclone 是一个开源的存储管理工具，支持多种本地和云盘存储。
#     rclone 支持一种 crypt 的存储，其实就是在普通存储层上加了一层加密层。
#     通过这层加密层，写入到普通存储上的文件，就被 256 位密钥的 AES 算法加密了。
#     只有通过这层加密层和正确的密码，才能读取到原始的文件
#     而在普通存储上读取到的就是乱码密文
#     这种加密层可以加到任何存储上，加密过程也是透明加密，而不是容器加密，你可以放心地将加密后的文件夹上传到网盘，而不用担心泄密

#     这种加密方式的缺陷有：
#     * 所有保险库内的文件都是使用用户密码加密的，所以无法改密码。唯一改密码的方式就是先打开保险库，再将保险库的文件复制到另一个密码不同的保险库中，解密再加密。
#     * 你在使用一个密码打开一个文件夹时，不会有错误提示。rclone 只负责用该密码在指定文件夹上打开一个加密层。只有当输入的密码和之前的密码相同时，才能正确读取到之前写入的文件。
#     
#     所以，在使用保险库时，一定要记好你的密码，一旦忘记了，数据是找不回来的！建议使用 keepass 之类的密码管理器保管密码。

#     rclone 管理保险库有多种方式，本脚本仅使用它的 server 和 mount 功能
#     即：将加密层映射到 webdav、ftp、sftp、http 服务上，或者挂载到指定目录，供用户访问
#     当映射到 webdav 等网络协议时，就可以方便同一局域网的设备访问，同时，还可以设置访问密码

# 优点：
#     rclone 是 go 语言写的开源软件，高效，跨平台，在各种系统上都能用，所以无需担心加密不安全，无需担心跨平台兼容问题

# 依赖：
#     * 如上所说，本脚本的加密依赖于 rclone，所以请先确保安装了 rclone 才能使用。
#     * 需要注意的是，rclone 的挂载功能依赖于 FUSE，所以在 Windwos 上挂载需要先安装 [winfsp](https://github.com/billziss-gh/winfsp/releases) 
#       Linux 系统上也需要有 FUSE 启用。
#     * 在使用脚本前，请先安装 python 依赖：pip install stdiomask pycryptodome

# 使用方法：
#     在安装 rclone 和 python 依赖后，直接用 python 运行该脚本就可以用了，会有文字交互引导你。
#     你可以在下面的 “用户编辑区” 编辑、增减你的保险库。
#     在本脚本中创建的保险库，也可以添加到 rclone 的配置文件中。rclone 是一个命令行软件，你可以到 [Rclone 文档部分翻译](https://ld246.com/article/1600853705300) 看下我的学习笔记

# rclone 的静态密钥来自 https://github.com/rclone/rclone/blob/master/fs/config/obscure/obscure.go


import os, sys, subprocess, stdiomask, string, time
import base64
from Crypto.Cipher import AES
from Crypto.Util import Counter
from Crypto.Util.number import bytes_to_long
import random

class RcloneCryptRemote:
    def __init__(self, name='', remote='', serverType='webdav', serverAddr=':8080', serverUser='', serverPass='', mountPath='Z:'):
        self.name = name              # 一个好认的保险库名字
        self.innerName = ''.join(random.sample(string.ascii_letters + string.digits, 6))    # 保险库内部的名字，用于 rclone 识别，不能重复，只能使用英文字母、数字和下划线
        self.remote = remote          # 保险库的路径
        self.serverType = serverType    # 当映射到端口服务时，服务的类型，可填：webdav、ftp、sftp、http
        self.serverAddr = serverAddr    # 当映射到端口服务时，服务的访问地址
        self.serverUser = serverUser    # 当映射到端口服务时，服务的登陆用户名，留空则所有人都可以访问
        self.serverPass = serverPass    # 当映射到端口服务时，服务的登陆密码 
        self.mountPath = mountPath    # 当挂载到硬盘时，挂载的路径。不能与已有路径相同，否则会冲突。

CryptVultList = [] # 设一个列表用于存放所有保险库


# =====================================用户编辑区入口=====================================================

# 用户可以在这里修改、添加多个保险库
# 修改的时候，修改单引号里的内容即可
# 添加的时候，将下面一个示例段复制到后面一份，再修改引号里的内容即可，建议不要修改变量的名字
# 下面示例添加了两个保险库，每一行后面有一个注释，解释了这一行是什么作用


vaultName =       r'第一个保险库'     # 设置一个好认的保险库名字
vaultPath =       r'D:\TestCrypt'   # 设置保险库的路径
vaultServerType =   r'webdav'          # 设置当映射到端口服务时，服务的类型，可填：webdav、ftp、sftp、http
vaultServerAddr =   r'0.0.0.0:8080'    # 设置当映射到端口服务时，服务的访问地址
vaultServerUser =   r'username'        # 设置当映射到端口服务时，服务的登陆用户名，留空则所有人都可以访问
vaultServerPass =   r'password'        # 设置当映射到端口服务时，服务的登陆密码
vaultMountPath =  r'S:'              # 设置当挂载到硬盘时，挂载的路径。不能与已有路径相同，否则会冲突。
CryptVultList.append(RcloneCryptRemote(vaultName, vaultPath, vaultServerType, vaultServerAddr, vaultServerUser, vaultServerPass, vaultMountPath)) # 将设置的保险库加到列表


vaultName =       r'第二个保险库'
vaultPath =       r'D:\测试加密'
vaultServerType =   r'webdav'
vaultServerAddr =   r'0.0.0.0:8080'
vaultServerUser =   r'username'
vaultServerPass =   r'password'
vaultMountPath =  r'S:'
CryptVultList.append(RcloneCryptRemote(vaultName, vaultPath, vaultServerType, vaultServerAddr, vaultServerUser, vaultServerPass, vaultMountPath))


# =====================================用户编辑区结束=====================================================




def encrypt(passwd):
    # 用于将明文密码 obscure 成 rclone 的格式
    key = b'\x9c\x93\x5b\x48\x73\x0a\x55\x4d\x6b\xfd\x7c\x63\xc8\x86\xa9\x2b\xd3\x90\x19\x8e\xb8\x12\x8a\xfb\xf4\xde\x16\x2b\x8b\x95\xf6\x38'
    seed = "1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()_+=-"
    iv = b''
    for i in range(16):
        iv += random.choice(seed).encode() # 得到随机 iv 编码成 bytes 的形式
    counter = Counter.new(128, initial_value=bytes_to_long(iv)) # 得到计数器
    cryptor = AES.new(key=key, mode=AES.MODE_CTR, counter=counter) # 得到加密器
    encrypData = cryptor.decrypt(passwd.encode()) # 加密密码
    result = iv + encrypData
    print(f'base64b: {base64.b64encode(result)}')
    print(f'base64 utf-8: {base64.b64encode(result).decode(encoding="utf-8")}')
    b64result = base64.b64encode(result).decode(encoding='utf-8').rstrip('=').replace("+", "-").replace("/", "_")  # base64 编码后用 utf-8 解码，再去掉后面的 ==
    return b64result


print('\n\n\n=====================第一步===========================\n')
print('目前有以下保险库：\n')
for index, vault in enumerate(CryptVultList):
    print(f'    ({index}) {vault.name}      路径：{vault.remote}\n')
while True:
    vaultSelection = input('请输入要操作的保险库的序号：')
    try:
        vaultSelection = int(vaultSelection)
    except:
        print('您的输入不是有效数字，请重新输入')
        continue
    if vaultSelection < 0 or vaultSelection > len(CryptVultList):
        print('您输入的序号不在有效范围内，请重新输入')
        continue
    break
vault = CryptVultList[vaultSelection]
print('\n\n\n=====================第二步===========================\n')
print(f'''您选择了 {vaultSelection} 号保险库，其信息为：

    名称：         {vault.name}
    路径：         {vault.remote}
    Server 类型：  {vault.serverType}
    Server 地址：  {vault.serverAddr}
    Server 用户名：{vault.serverUser}
    Server 密码：  {vault.serverPass}
    挂载路径：     {vault.mountPath}
''')
print(f'''请选择要对其进行的操作：

    (0) 将其映射到 {vault.serverAddr} 地址，我使用浏览器或其它远程工具访问
    (1) 将其挂载到 {vault.mountPath} 路径，我使用文件管理器访问
''')
while True:
    operation = input('输入操作的序号：')
    # if operation == '':
    #     operation = 0
    #     break
    try:
        operation = int(operation)
    except:
        print('您的输入不是有效数字，请重新输入')
        continue
    if operation < 0 or operation > 1:
        print('您输入的序号不在有效范围内，请重新输入')
        continue
    break
print('\n\n\n======================第三步==========================\n')
print('接下来需要输入保险库的密码\n')
print('注意，无论密码是否正确，都能打开保险库，但只有当“输入的密码”与“存入文件前输入的密码”一致时，才能正确读取保险库里的文件！！！\n')
passwd = stdiomask.getpass('现在请输入保险库密码：')

typeVar, typeValue = f'RCLONE_CONFIG_{vault.innerName}_TYPE', 'crypt'
remoteVar, remoteValue = f'RCLONE_CONFIG_{vault.innerName}_REMOTE', vault.remote
passVar, passValue = f'RCLONE_CONFIG_{vault.innerName}_PASSWORD', encrypt(passwd)
os.environ[typeVar]=typeValue
os.environ[remoteVar]=remoteValue
os.environ[passVar]=passValue

print('\n\n\n======================第四步==========================\n')


if operation == 0:
    print(f'开始映射，此次映射的保险库是“{vault.name}”，其实际存储路径为 {vault.remote}\n')
    if vault.serverType == 'webdav' or vault.serverType == 'http':
        print(f'你可以通过在浏览器或远程文件管理器访问 {vault.serverAddr.replace("0.0.0.0", "127.0.0.1")} 来查看你的保险库\n')
    elif vault.serverType == 'ftp':
        print(f'你可以通过在浏览器或远程文件管理器访问 ftp://{vault.serverAddr.replace("0.0.0.0", "127.0.0.1")} 来查看你的保险库\n')
    elif vault.serverType == 'sftp':
        print(f'你可以通过在支持 sftp 协议的远程文件管理器访问 {vault.serverAddr.replace("0.0.0.0", "127.0.0.1")} 来查看你的保险库\n')
    if vault.serverUser == '':
        subprocess.run(f'rclone serve {vault.serverType} "{vault.innerName}:/" --addr {vault.serverAddr}')
    else:
        print(f'访问用户名为：{vault.serverUser}，密码为：{vault.serverPass}\n')
        subprocess.run(f'rclone serve {vault.serverType} "{vault.innerName}:/" --addr {vault.serverAddr} --user {vault.serverUser} --pass {vault.serverPass}')
elif operation == 1:
    print(f'\n开始挂载，此次映射的保险库是“{vault.name}”，其实际存储路径为 {vault.remote}\n')
    print(f'你可以通过在文件浏览器访问 {vault.mountPath} 来查看你的保险库\n')
    subprocess.run(f'rclone mount "{vault.innerName}:/" "{vault.mountPath}" --vfs-cache-mode full --dir-cache-time 60s')
