# GraftSense-Drivers-MicroPython

本仓库收录 **GraftSense 系列模块的 MicroPython 驱动程序**，并提供简要的使用示例。  
模块按照功能类别进行分类，便于查找和使用。

## 📂 目录结构
```
GraftSense-Drivers-MicroPython/
├── motor_drivers/        # 电机驱动类 (L298N, DRV8833 ...)
├── power/                # 电源类 (INA219, UPS 模块 ...)
├── communication/        # 通信类 (CAN, RS485 ...)
├── sensors/              # 传感器类 (DHT20, MAX9814 ...)
├── lighting/             # 发光类 (WS2812, SSD1306 ...)
├── input/                # 输入类 (按键, 摇杆 ...)
├── signal_acquisition/   # 信号采集类 (MCP3008, ADS1115 ...)
├── signal_generation/    # 信号发生类 (MCP4725, AD9833 ...)
├── misc/                 # 杂项类 (继电器, 蜂鸣器 ...)
└── docs/                 # 详细文档和应用说明
```