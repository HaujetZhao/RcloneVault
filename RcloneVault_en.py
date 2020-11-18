# 用途：rclone 的 crypt 存储类型，可以作为用户透明加密文件的保险库，本脚本可以方便管理 rclone crypt 保险库，方便地打开和关闭保险库
# 作者：淳帅二代  https://github.com/HaujetZhao   https://gitee.com/haujet   https://space.bilibili.com/62637562
# 编写日期：2020年11月17日

# Purpose:
#   Crypt-type remote of rclone can be used as users File Vault, and this script is ment
#   to make managing, editing, opening and closing File Vaults easier. 
# Author: HaujetZhao  https://github.com/HaujetZhao   https://gitee.com/haujet   https://space.bilibili.com/62637562
# Compose Date: 2020/11/17

# Introduce: 
#     Rclone is a open source storage manage tool, it supports multi kinds of local and cloud storage. 
#     Rclone supports a storage type called "Crypt", it's actually adding a crypt layer on top of a normal storage layer. 
#     By using this crypt layer, files will be crypted by AES algorism using 256 bit key before it written to the normal storage. 
#     So only by passing this crypt layer and correct password, you can read the original file. 
#     You can only read the random bytes on the normal storage.
#     This crypt layer can be applied to any kinds of storage, the crypt process is transparent, not container crypt. 
#     So you can safely upload the crypted folder to the cloud storage without worrying your privacy leaking.
# 
#     Downside of this crypt method: 
#     * All the file within the Vault are crypted by user password, so you can't change the password. 
#       The only way to change password is the open the old vault, then copying the files into another vault with different password. Decrypt then recrypt.
#     * When using a password opening a folder, there won't be a error prompt. Rclone just uses this password to apply a crypt layer. Only when you input the
#       right password, the files written before can be correctly shown and read.
#
#     So when using rclone vault, you must keep your password rememberd. If passwd forgotten, you will lose your data forever! 
#     I suggest you use a password manager like Keepass to take care of your passwords.

#     Rclone has many ways to manage your vault. This script only use the server and mount feature. 
#     aka: Serve your vault by webdav, ftp, sftp, http protocal, or mount your vault to a path, to let users visit. 
#     When served, other devices like your phone will be able to access you PC vault or vice versa, in the meantime, you can also set a access account! 

# Advantages：
#     Rclone is written in go, opensource, hight efficiency performance, cross platform. No worry about safety and compatibility. 

# Dependencies：
#     * Rclone installed
#     * Mount function requires FUSE, Windows users need first install [winfsp](https://github.com/billziss-gh/winfsp/releases) 
#     * Before you run this script, please install python dependencies：pip install stdiomask pycryptodome

# Usage：
#     After installing Rclone and Python dependencies, you can just run this script using python, there will be text guide then.
#     You can edit or add your vault in the USER EDIT REGION below. 
#     Vaults created in this script can also be added to rclone config. 

# rclone static key is from https://github.com/rclone/rclone/blob/master/fs/config/obscure/obscure.go


import os, sys, subprocess, stdiomask, string, time
import base64
from Crypto.Cipher import AES
from Crypto.Util import Counter
from Crypto.Util.number import bytes_to_long
import random

class RcloneCryptRemote:
    def __init__(self, name='', remote='', serverType='webdav', serverAddr=':8080', serverUser='', serverPass='', mountPath='Z:'):
        self.name = name              # A human friendly vault name
        self.innerName = ''.join(random.sample(string.ascii_uppercase + string.digits, 6))    # Internal name of the vault, which is the remote name in rclone. It need to be uppercase. 
        self.remote = remote          # The path of the vault
        self.serverType = serverType    # When serve, the type of the server. Appliable choice: webdav、ftp、sftp、http
        self.serverAddr = serverAddr    # When serve, the address and port of the server
        self.serverUser = serverUser    # When serve, the user name of the server. When blank, authentification will be disabled.
        self.serverPass = serverPass    # When serve, the user password of the server. 
        self.mountPath = mountPath    # When mount, the path of the mount point. Can't be a existing path, or it will fail. 

CryptVultList = [] # Set a list used to store vaults. 


# =====================================USER EDIT REGION ENTRY=====================================================

# Users can edit, add multi vaults. 
# When editing, just modify the content within the quots. 
# When adding, just copy one of example below, then modify the content within the quots. Do not edit the name of variables. 
# Below shown are two vault examples, the comment at the end explains the meaning of that line. 


vaultName =       r'The first vault'     # A human friendly vault name
vaultPath =       r'D:\TestCrypt'   # The path of the vault
vaultServerType =   r'webdav'          # When serve, the type of the server. Appliable choice: webdav、ftp、sftp、http
vaultServerAddr =   r'0.0.0.0:8080'    # When serve, the address and port of the server
vaultServerUser =   r'username'        # When serve, the user name of the server. When blank, authentification will be disabled.
vaultServerPass =   r'password'        # When serve, the user password of the server. 
vaultMountPath =  r'S:'              # When mount, the path of the mount point. Can't be a existing path, or it will fail. 
CryptVultList.append(RcloneCryptRemote(vaultName, vaultPath, vaultServerType, vaultServerAddr, vaultServerUser, vaultServerPass, vaultMountPath)) # Add this vault into the vault list. 


vaultName =       r'The second vault'
vaultPath =       r'D:\My secret'
vaultServerType =   r'webdav'
vaultServerAddr =   r'0.0.0.0:8080'
vaultServerUser =   r'username'
vaultServerPass =   r'password'
vaultMountPath =  r'S:'
CryptVultList.append(RcloneCryptRemote(vaultName, vaultPath, vaultServerType, vaultServerAddr, vaultServerUser, vaultServerPass, vaultMountPath))


# =====================================USER EDIT REGION EXIT=====================================================



key = b'\x9c\x93\x5b\x48\x73\x0a\x55\x4d\x6b\xfd\x7c\x63\xc8\x86\xa9\x2b\xd3\x90\x19\x8e\xb8\x12\x8a\xfb\xf4\xde\x16\x2b\x8b\x95\xf6\x38'
def encrypt(passwd):
    # 用于将明文密码 obscure 成 rclone 的格式
    seed = "1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()_+=-"
    iv = b''
    for i in range(16):
        iv += random.choice(seed).encode() # 得到随机 iv 编码成 bytes 的形式
    counter = Counter.new(128, initial_value=bytes_to_long(iv)) # 得到计数器
    cryptor = AES.new(key=key, mode=AES.MODE_CTR, counter=counter) # 得到加密器
    encrypData = cryptor.decrypt(passwd.encode()) # 加密密码
    result = iv + encrypData
    b64result = base64.b64encode(result).decode(encoding='utf-8').rstrip('=')  # base64 编码后用 utf-8 解码，再去掉后面的 ==
    if '+' in b64result or '/' in b64result: # rclone 的 base64 字符串中不能出现 + 和 /，所以要使用递归重新加密
        b64result = encrypt(passwd)
    return b64result
def decrypt(data):
    data += '=='
    data_origin = base64.b64decode(data) # 进行 base64 解码
    iv = data_origin[:AES.block_size] # 得到 initial_value
    passwd = data_origin[AES.block_size:] # 得到加密的数据部分
    counter = Counter.new(128, initial_value=bytes_to_long(iv)) # 得到计数器
    cryptor = AES.new(key=key, mode=AES.MODE_CTR, counter=counter) # 得到加密器
    # decrypData = cryptor.decrypt(passwd).decode(encoding='utf-8') # 解密加密部分
    decrypData = cryptor.decrypt(passwd)
    return decrypData

print('\n\n\n=====================Step one===========================\n')
print('There is the vaults list：\n')
for index, vault in enumerate(CryptVultList):
    print(f'    ({index}) {vault.name}      path: {vault.remote}\n')
while True:
    vaultSelection = input('Please input the index number of the vault you want to operate: ')
    try:
        vaultSelection = int(vaultSelection)
    except:
        print('Your input is not a number, please retry again. ')
        continue
    if vaultSelection < 0 or vaultSelection > len(CryptVultList):
        print('The index number you input in not in valid range, please retry again. ')
        continue
    break
vault = CryptVultList[vaultSelection]
print('\n\n\n=====================Step two===========================\n')
print(f'''You choose vault {vaultSelection}，it's info is list below: 

    Name:             {vault.name}
    Path:             {vault.remote}
    Server type:      {vault.serverType}
    Server address:   {vault.serverAddr}
    Server username:  {vault.serverUser}
    Server password:  {vault.serverPass}
    Mount path:       {vault.mountPath}
''')
print(f'''Please choose the operation you want to do: 

    (0) serve it to {vault.serverAddr} , so that I can access it through Web Browser or other remote tool. 
    (1) Mount it to {vault.mountPath} , so that I can access it through File Explorer. 
''')
while True:
    operation = input('Input the operation index number: ')
    # if operation == '':
    #     operation = 0
    #     break
    try:
        operation = int(operation)
    except:
        print('Your input is not a number, please retry again. ')
        continue
    if operation < 0 or operation > 1:
        print('The index number you input in not in valid range, please retry again. ')
        continue
    break
print('\n\n\n======================Step three==========================\n')
print('Next you need to input the password of the vault\n')
print('Warning: whether if the password is correct, the vault will open. But, only when your input passwd is the same as the password last time you stored file, then you can correctly read your file! ! ! \n')
passwd = stdiomask.getpass('Now please input the password: ')

typeVar, typeValue = f'RCLONE_CONFIG_{vault.innerName}_TYPE', 'crypt'
remoteVar, remoteValue = f'RCLONE_CONFIG_{vault.innerName}_REMOTE', vault.remote
passVar, passValue = f'RCLONE_CONFIG_{vault.innerName}_PASSWORD', encrypt(passwd)
os.environ[typeVar]=typeValue
os.environ[remoteVar]=remoteValue
os.environ[passVar]=passValue

print('\n\n\n======================Step four==========================\n')


if operation == 0:
    print(f'Server will start, the vault is“{vault.name}”，it\'s actual path is {vault.remote}\n')
    if vault.serverType == 'webdav' or vault.serverType == 'http':
        print(f'Now you can access your vault through {vault.serverAddr.replace("0.0.0.0", "127.0.0.1")} \n')
    elif vault.serverType == 'ftp':
        print(f'Now you can access your vault through  ftp://{vault.serverAddr.replace("0.0.0.0", "127.0.0.1")}\n')
    elif vault.serverType == 'sftp':
        print(f'Now you can access your vault through sftp client accessing {vault.serverAddr.replace("0.0.0.0", "127.0.0.1")} \n')
    if vault.serverUser == '':
        # subprocess.run(f'rclone serve {vault.serverType} "{vault.innerName}:/" --addr {vault.serverAddr}')
        subprocess.run(['rclone', 'serve', f'{vault.serverType}', f'{vault.innerName}:/', '--addr', f'{vault.serverAddr}'])
    else:
        print(f'Username: {vault.serverUser}\npassword: {vault.serverPass}\n')
        subprocess.run(['rclone', 'serve', f'{vault.serverType}', f'{vault.innerName}:/', '--addr', f'{vault.serverAddr}', '--user', f'{vault.serverUser}', '--pass', f'{vault.serverPass}'])
elif operation == 1:
    print(f'\nMount will start, the vault is “{vault.name}”，it\'s actual path is {vault.remote}\n')
    print(f'You can access your vault through {vault.mountPath} \n')
    subprocess.run(['rclone', 'mount', f'{vault.innerName}:/', f'{vault.mountPath}', '--vfs-cache-mode', 'full', '--dir-cache-time', '60s'])
