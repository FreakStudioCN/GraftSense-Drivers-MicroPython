# GraftSense-Drivers-MicroPython

# 仓库概述

本仓库是 GraftSense 系列硬件模块的 MicroPython 驱动程序集合，涵盖输入、输出、传感器、通信、存储等多类硬件，所有驱动均附带 package.json 配置，支持通过 MicroPython 包管理工具（mip）、mpremote 命令行工具或 upypi 包源 直接下载安装。驱动程序遵循统一设计规范，包含详细文档和示例代码，适配树莓派 Pico 等主流 MicroPython 开发板，便于开发者快速集成硬件功能。

🔗 核心资源链接:
* upypi 包源地址：https://upypi.net/
* 项目 Wiki 文档：https://freakstudio.cn/

![图片描述](docs/upypi.png)
![图片描述](docs/wiki.png)

# 📂 目录结构与模块说明

仓库按硬件功能分类，结构清晰，以下是各文件夹及包含模块的详细介绍：

```plantuml
GraftSense-Drivers-MicroPython/
├── input/                # 输入类模块（如按钮、摇杆、编码器等）
├── storage/              # 存储类模块（如SD卡、Flash等）
├── misc/                 # 杂项功能模块
├── lighting/             # 发光/显示类模块（如LED、NeoPixel等）
├── signal_generation/    # 信号发生类模块（如PWM、波形生成等）
├── motor_drivers/        # 电机驱动类模块（如直流电机、步进电机、舵机等）
├── signal_acquisition/   # 信号采集类模块（如ADC、传感器数据采集等）
├── sensors/              # 传感器类模块（如温湿度、气压、红外、超声波等）
├── communication/        # 通信类模块（如UART、I2C、SPI、蓝牙等）
├── docs/                 # 详细文档、应用说明和项目截图
├── list_package_info.py  # 可视化扫描工具，查看所有package.json配置
├── modify_package_json.py # 批量修改工具，标准化urls路径和字段
└── rename_readme.py      # 批量重命名工具，统一README.md文件名
```

# 📦 包管理与安装（支持 mip /mpremote/upypi）

所有模块均通过 package.json 标准化配置，支持多种安装方式，满足不同开发场景需求。

## 方式一：代码内通过 mip 安装（开发板联网）

适用于开发板已连接网络（如 WiFi）的场景，直接在代码中执行安装：

1. 确保开发板已烧录 MicroPython 固件（推荐 v1.23.0 及以上版本）。
2. 在代码中通过 `mip` 安装指定模块，示例：
3. python
4. 运行

```python
import mip

# 安装RCWL9623超声波模块驱动
mip.install("github:FreakStudioCN/GraftSense-Drivers-MicroPython/sensors/rcwl9623_driver")

# 安装PS2摇杆驱动
mip.install("github:FreakStudioCN/GraftSense-Drivers-MicroPython/input/ps2_joystick_driver")
```

1. 安装后直接导入使用，示例（以 TCR5000 循迹模块为例）：
2. python
3. 运行

```python
from tcr5000 import TCR5000
from machine import Pin

# 初始化模块（连接GP2引脚）
# 读取检测状态（0=检测到黑线，1=检测到白线）print("检测状态：", sensor.read())
sensor = TCR5000(Pin(2, Pin.IN))
```

## 方式二：通过 mpremote 命令行安装（开发板串口连接）

适用于开发板未联网、仅通过串口连接电脑的场景，需先安装 mpremote 工具：

步骤 1：安装 mpremote（电脑端）
```bash
# 使用pip安装mpremote
pip install mpremote
```

步骤 2：通过串口执行 mip 安装
```bash
# 简化写法（自动识别串口）
mpremote mip install github:FreakStudioCN/GraftSense-Drivers-MicroPython/input/ps2_joystick_driver
```

## 方式三：通过 upypi 包源安装（推荐）
我们提供专属 upypi 包源，访问速度更快、安装更稳定，你可以访问[**upypi网站**](https://upypi.net/)，搜索要安装的对应包的名称，打开直接复制指令在 终端运行即可：
![图片描述](docs/upypi-install.png)

# 🔧 开发环境准备

1. **固件烧录**：从 [MicroPython 官网](https://micropython.org/) 下载对应开发板固件（如树莓派 Pico 选择 `rp2-pico` 系列），按住 `BOOTSEL` 键连接电脑，将 `.uf2` 固件拖入识别的 U 盘完成烧录。
2. **开发工具**：推荐使用 Thonny（[thonny.org](https://thonny.org/)），支持语法高亮、串口调试和文件传输，连接后在右下角选择设备为 `MicroPython (Raspberry Pi Pico)` 即可开发。

# 辅助工具使用

仓库内置 3 个实用工具，提升开发效率：
```bash
# 1. 可视化扫描所有package.json（查看字段完整性、双击打开文件）
python list_package_info.py

# 2. 批量标准化package.json配置（自动修复urls路径、补充字段）
python modify_package_json.py

# 3. 统一文档命名（递归将所有.md文件重命名为README.md）
python rename_readme.py
```

![图片描述](docs/1.png)
![图片描述](docs/2.png)
![图片描述](docs/3.png)
![图片描述](docs/4.png)
![图片描述](docs/5.png)
![图片描述](docs/6.png)

# 📜 许可协议

本仓库所有驱动程序（除 MicroPython 官方模块和参考的相关模块外）均采用MIT许可协议。

# 📞 联系方式

- 邮箱：10696531183@qq.com
- GitHub 仓库：[https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython](https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython)

如有问题或建议，欢迎提交 Issue 或 Pull Request 参与贡献！

![图片描述](docs/freakstudio.png)