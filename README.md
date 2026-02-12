# GraftSense-Drivers-MicroPython

# 仓库概述

本仓库是 **GraftSense 系列硬件模块的 MicroPython 驱动程序集合**，涵盖输入、输出、传感器、通信、存储等多类硬件，所有驱动均附带 `package.json` 配置，支持通过 MicroPython 包管理工具（`mip`）直接下载安装。驱动程序遵循统一设计规范，包含详细文档和示例代码，适配树莓派 Pico 等主流 MicroPython 开发板，便于开发者快速集成硬件功能。

# 📂 目录结构与模块说明

仓库按硬件功能分类，结构清晰，以下是各文件夹及包含模块的详细介绍：

plaintext

```
GraftSense-Drivers-MicroPython/
├── input/                # 输入类模块
├── storage/              # 存储类模块
├── misc/                 # 杂项功能模块
├── lighting/             # 发光/显示类模块
├── signal_generation/    # 信号发生类模块
├── motor_drivers/        # 电机驱动类模块
├── signal_acquisition/   # 信号采集类模块
├── sensors/              # 传感器类模块
├── communication/        # 通信类模块
├── power/                # 电源管理类模块
└── docs/                 # 详细文档和应用说明
```

# 📦 包管理与安装（支持 mip 下载）

所有模块均通过 `package.json` 标准化配置，支持 `mip` 工具一键安装：

## 安装步骤

1. 确保开发板已烧录 MicroPython 固件（推荐 v1.23.0 及以上版本）。
2. 在代码中通过 `mip` 安装指定模块，示例：
3. python
4. 运行

```python
# 安装RCWL9623超声波模块驱动import mip
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

# 🔧 开发环境准备

1. **固件烧录**：从 [MicroPython 官网](https://micropython.org/) 下载对应开发板固件（如树莓派 Pico 选择 `rp2-pico` 系列），按住 `BOOTSEL` 键连接电脑，将 `.uf2` 固件拖入识别的 U 盘完成烧录。
2. **开发工具**：推荐使用 Thonny（[thonny.org](https://thonny.org/)），支持语法高亮、串口调试和文件传输，连接后在右下角选择设备为 `MicroPython (Raspberry Pi Pico)` 即可开发。

# 📜 许可协议

本仓库所有驱动程序（除 MicroPython 官方模块和参考的相关模块外）均采用 **知识共享署名 - 非商业性使用 4.0 国际版（CC BY-NC 4.0）**或** MIT** 许可协议。

# 📞 联系方式

- 邮箱：10696531183@qq.com
- GitHub 仓库：[https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython](https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython)

如有问题或建议，欢迎提交 Issue 或 Pull Request 参与贡献！
