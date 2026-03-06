# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/9 上午9:00
# @Author  : alankrantas
# @File    : sim7600_ftp.py
# @Description : SIM7600模块FTP功能类 实现FTP服务器参数配置、文件上传/下载/删除、文件列表查询等FTP功能
# @License : MIT
# @Platform: Raspberry Pi Pico / MicroPython

__version__ = "1.0.0"
__author__ = "alankrantas"
__license__ = "MIT"
__platform__ = "Raspberry Pi Pico / MicroPython v1.23.0"


# ======================================== 导入相关模块 =========================================

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================
class FTP:
    """
    SIM7600模块FTP功能类
    SIM7600 Module FTP Function Class

    封装SIM7600模块的FTP文件传输功能，包括FTP服务器参数配置、文件上传、文件下载、文件删除、远程文件列表查询等核心功能
    Encapsulates FTP file transfer functions of SIM7600 module, including core functions such as FTP server parameter configuration, file upload, file download, file deletion, remote file list query

    Attributes:
        sim7600 (object): SIM7600模块核心对象，需包含send_command、write_uart、read_uart方法
                          SIM7600 module core object, must contain send_command, write_uart, read_uart methods

    Methods:
        __init__(sim7600): 初始化FTP功能类
                           Initialize FTP function class
        set_ftp_parameters(server, port=21, user='', password=''): 配置FTP服务器连接参数
                                                                   Configure FTP server connection parameters
        upload_file(local_path, remote_path): 上传本地文件到FTP服务器
                                              Upload local file to FTP server
        download_file(remote_path, local_path): 从FTP服务器下载文件到本地
                                                Download file from FTP server to local
        delete_file(remote_path): 删除FTP服务器上的指定文件
                                  Delete specified file on FTP server
        list_files(remote_path): 查询FTP服务器指定路径下的文件列表
                                 Query file list under specified path on FTP server
    """

    def __init__(self, sim7600):
        """
        初始化FTP功能类
        Initialize FTP function class

        Args:
            sim7600 (object): SIM7600模块核心对象，需实现send_command、write_uart、read_uart方法
                              SIM7600 module core object, must implement send_command, write_uart, read_uart methods

        Returns:
            None

        Notes:
            依赖SIM7600核心对象提供的AT指令发送和UART读写方法完成FTP文件传输
            Depends on AT command sending and UART read/write methods provided by SIM7600 core object to complete FTP file transfer
        """
        # 保存SIM7600模块核心对象引用
        self.sim7600 = sim7600

    def set_ftp_parameters(self, server, port=21, user="", password=""):
        """
        配置FTP服务器连接参数
        Configure FTP server connection parameters

        Args:
            server (str): FTP服务器IP地址或域名
                          FTP server IP address or domain name
            port (int, optional): FTP服务器端口号，默认21
                                  FTP server port number, default 21
            user (str, optional): FTP登录用户名，默认为空字符串
                                  FTP login username, default empty string
            password (str, optional): FTP登录密码，默认为空字符串
                                      FTP login password, default empty string

        Returns:
            None

        Notes:
            依次配置FTP使用的CID、服务器地址、端口、用户名和密码，CID固定为1对应GPRS承载1
            Configure CID, server address, port, username and password for FTP in sequence, CID is fixed to 1 corresponding to GPRS bearer 1
        """
        # 设置FTP使用的承载ID为1
        self.sim7600.send_command(f"AT+FTPCID=1")
        # 设置FTP服务器地址
        self.sim7600.send_command(f'AT+FTPSERV="{server}"')
        # 设置FTP服务器端口号
        self.sim7600.send_command(f"AT+FTPPORT={port}")
        # 设置FTP登录用户名
        self.sim7600.send_command(f'AT+FTPUN="{user}"')
        # 设置FTP登录密码
        self.sim7600.send_command(f'AT+FTPPW="{password}"')

    def upload_file(self, local_path, remote_path):
        """
        上传本地文件到FTP服务器
        Upload local file to FTP server

        Args:
            local_path (str): 本地文件路径
                              Local file path
            remote_path (str): FTP服务器上的目标文件路径/名称
                               Target file path/name on FTP server

        Returns:
            bytes: 文件上传后的响应数据
                   Response data after file upload

        Notes:
            以512字节为块读取本地文件并分块上传，远程路径固定设置为根目录"/"
            Read local file in 512-byte chunks and upload in chunks, remote path is fixed to root directory "/"
        """
        # 设置FTP上传的远程文件名
        self.sim7600.send_command(f'AT+FTPPUTNAME="{remote_path}"')
        # 设置FTP上传的远程路径为根目录
        self.sim7600.send_command(f'AT+FTPPUTPATH="/"')
        # 启动FTP上传模式
        self.sim7600.send_command("AT+FTPPUT=1")
        # 以二进制模式打开本地文件
        with open(local_path, "rb") as file:
            # 循环读取文件内容，每次读取512字节直到文件结束
            for chunk in iter(lambda: file.read(512), b""):
                # 发送文件数据块到FTP服务器
                self.sim7600.write_uart(chunk)
        # 读取并返回上传完成后的响应数据
        return self.sim7600.read_uart()

    def download_file(self, remote_path, local_path):
        """
        从FTP服务器下载文件到本地
        Download file from FTP server to local

        Args:
            remote_path (str): FTP服务器上的文件路径/名称
                               File path/name on FTP server
            local_path (str): 本地保存文件的路径
                              Local path to save file

        Returns:
            bytes: 下载的文件数据
                   Downloaded file data

        Notes:
            远程路径固定设置为根目录"/"，下载的数据以二进制模式保存到本地文件
            Remote path is fixed to root directory "/", downloaded data is saved to local file in binary mode
        """
        # 设置FTP下载的远程文件名
        self.sim7600.send_command(f'AT+FTPGETNAME="{remote_path}"')
        # 设置FTP下载的远程路径为根目录
        self.sim7600.send_command(f'AT+FTPGETPATH="/"')
        # 启动FTP下载模式
        self.sim7600.send_command("AT+FTPGET=1")
        # 读取下载的文件数据
        data = self.sim7600.read_uart()
        # 以二进制模式写入本地文件
        with open(local_path, "wb") as file:
            file.write(data)
        # 返回下载的文件数据
        return data

    def delete_file(self, remote_path):
        """
        删除FTP服务器上的指定文件
        Delete specified file on FTP server

        Args:
            remote_path (str): FTP服务器上要删除的文件路径/名称
                               File path/name to delete on FTP server

        Returns:
            bytes: 删除文件后的响应数据
                   Response data after file deletion

        Notes:
            使用AT+FTPDELE指令删除FTP服务器上的指定文件，操作不可逆
            Use AT+FTPDELE command to delete specified file on FTP server, operation is irreversible
        """
        # 发送删除FTP文件指令
        self.sim7600.send_command(f'AT+FTPDELE="{remote_path}"')
        # 读取并返回删除操作的响应数据
        return self.sim7600.read_uart()

    def list_files(self, remote_path):
        """
        查询FTP服务器指定路径下的文件列表
        Query file list under specified path on FTP server

        Args:
            remote_path (str): FTP服务器上要查询的目录路径
                               Directory path to query on FTP server

        Returns:
            bytes: 包含文件列表信息的响应数据
                   Response data containing file list information

        Notes:
            使用AT+FTPLIST指令查询指定路径下的文件和目录列表
            Use AT+FTPLIST command to query file and directory list under specified path
        """
        # 发送查询FTP文件列表指令
        self.sim7600.send_command(f'AT+FTPLIST="{remote_path}"')
        # 读取并返回文件列表响应数据
        return self.sim7600.read_uart()


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ===========================================
