# Python env   : Python v3.13
# -*- coding: utf-8 -*-
# @Time    : 2025/9/5 下午10:11
# @Author  : 侯钧瀚
# @File    : http_sever.py
# @Description : 简易http服务器示例代码
# ======================================== 导入相关模块 =========================================

from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import TCPServer
import socket
import sys
import os

# ======================================== 全局变量 ============================================


HOST = "0.0.0.0"  # 0.0.0.0 允许所有网络设备访问（本地用 localhost 或 127.0.0.1）
PORT = 8080  # 监听端口（建议选 8000/8080/9090 等非占用端口）

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 =============================================


# 完全禁用标准错误输出
class DevNull:
    def write(self, msg):
        pass

    def flush(self):
        pass


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    """自定义请求处理器，重写 GET 请求逻辑"""

    def _set_response(self, status_code=200, content_type="text/html"):
        """设置 HTTP 响应头（状态码、内容类型等）"""
        self.send_response(status_code)
        self.send_header("Content-type", content_type)
        self.send_header("Server", "Python-Simple-HTTP-Server")  # 服务器标识
        self.end_headers()  # 结束响应头（必须调用）

    def do_GET(self):
        """处理 GET 请求（核心逻辑）"""
        # 1. 打印请求日志（控制台输出）
        client_ip, client_port = self.client_address  # 获取客户端 IP 和端口
        print(f"\n[新请求]")
        print(f"  客户端: {client_ip}:{client_port}")
        print(f"  方法: {self.command}")  # 请求方法（GET/POST 等）
        print(f"  路径: {self.path}")  # 请求路径（如 / 或 /test）
        print(f"  协议: {self.request_version}")

        # 2. 构造响应内容（支持 HTML 格式，可自定义）
        response_html = f"""
        <html>
            <head><title>Python 简单 HTTP 服务器</title></head>
            <body style="text-align: center; margin-top: 50px;">
                <h1>✅ 服务器响应成功！</h1>
                <p>请求信息:</p>
                <p>客户端 IP: {client_ip}:{client_port}</p>
                <p>请求方法: {self.command}</p>
                <p>请求路径: {self.path}</p>
                <p>服务器端口: {PORT}</p>
                <hr>
                <p style="color: #666;">Powered by Python http.server</p>
            </body>
        </html>
        """

        # 3. 发送响应（先设置响应头，再发送内容）
        self._set_response(status_code=200)  # 200 = 成功
        # 将字符串转为字节流（HTTP 传输需字节格式）
        self.wfile.write(response_html.encode("utf-8"))

    def do_POST(self):
        """处理 POST 请求"""
        # 1. 打印请求日志
        client_ip, client_port = self.client_address
        print(f"\n[新请求]")
        print(f"  客户端: {client_ip}:{client_port}")
        print(f"  方法: {self.command}")
        print(f"  路径: {self.path}")
        print(f"  协议: {self.request_version}")

        # 2. 读取 POST 数据
        content_length = int(self.headers["Content-Length"]) if self.headers.get("Content-Length") else 0
        post_data = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else ""
        print(f"  POST 数据: {post_data}")

        # 3. 构造响应内容
        response_html = f"""
        <html>
            <head><title>Python 简单 HTTP 服务器</title></head>
            <body style="text-align: center; margin-top: 50px;">
                <h1>✅ POST 请求处理成功！</h1>
                <p>请求信息:</p>
                <p>客户端 IP: {client_ip}:{client_port}</p>
                <p>请求方法: {self.command}</p>
                <p>请求路径: {self.path}</p>
                <p>POST 数据: {post_data}</p>
                <p>服务器端口: {PORT}</p>
                <hr>
                <p style="color: #666;">Powered by Python http.server</p>
            </body>
        </html>
        """

        # 4. 发送响应
        self._set_response(status_code=200)
        self.wfile.write(response_html.encode("utf-8"))

    def log_message(self, format, *args):
        """禁用默认日志（可选，避免控制台冗余输出）"""
        return


def run_simple_http_server():
    """启动 HTTP 服务器"""
    # 创建 TCP 服务器实例（绑定主机+端口，指定请求处理器）
    server_address = (HOST, PORT)
    httpd = TCPServer(server_address, SimpleHTTPRequestHandler)

    # 打印启动信息
    print(f"📡 Python 简单 HTTP 服务器已启动")
    print(f"  访问地址: http://{socket.gethostbyname(socket.gethostname())}:{PORT}")
    print(f"  本地访问: http://localhost:{PORT} 或 http://127.0.0.1:{PORT}")
    print(f"  提示: 按 Ctrl+C 关闭服务器")

    try:
        # 持续监听请求（阻塞模式）
        httpd.serve_forever()
    except KeyboardInterrupt:
        # 捕获 Ctrl+C 信号，优雅关闭服务器
        print(f"\n🔌 正在关闭服务器...")
        httpd.server_close()  # 关闭服务器连接
        print(f"✅ 服务器已关闭")


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================

sys.stderr = DevNull()
if __name__ == "__main__":
    run_simple_http_server()
