# GraftSense I2C 四路直流电机驱动（MicroPython）

兼容原 `BusDCMotor` 开环接口，新增可选编码器计数、方向、RPM、四路独立 PID 和电机电源电压查询。硬件基于 PCA9685 与 SS6285L，每路电机使用两个 PWM 通道。

版本：**1.1.0**。本次板测依据为 ESP32-C3 SuperMini、MicroPython v1.29.0（2026-08-24），其他平台需自行验证；原开环使用方式不强制初始化编码器或 ADC。

## 目录

- [简介与主要功能](#简介与主要功能)
- [软件环境](#软件环境)
- [文件结构与说明](#一安装与文件)
- [旧接口兼容](#二保留的旧接口)
- [硬件要求与参数](#三esp32-c3-接线与参数)
- [快速开始](#四完整闭环调用)
- [统一接口与调度](#五统一接口与调度)
- [注意事项与频率](#六pwm-频率与兼容变化)
- [测试与迁移](#七测试与迁移)
- [版本记录](#版本记录)
- [联系方式](#联系方式)
- [许可与来源](#许可与来源)

## 简介与主要功能

面向已有 PCA9685 总线电机板提供四路独立速度闭环，供应用层周期调用。保留原开环接口，闭环、电压监测按配置启用。

- 单边沿 AB 编码器累计计数、方向及输出轴 RPM 换算。
- 独立 PID、在线目标和增益设置、输出与积分限幅。
- 单电机、四电机启停与模式隔离，统一遥测。
- ADC 电源电压换算、校准与缓存。
- 显式 deinit 清理；共享 I2C、PCA 和注入的电压监测器归调用方管理。

## 软件环境

已测目标为 ESP32-C3、MicroPython v1.29.0（2026-08-24）；固件无 machine.Encoder。当前版本已在该开发板完成单路及四路组合 PID、四个电机独立正反转 PID 实机测试。

依赖为内置 machine、time、math、ustruct、micropython 和 package.json 中的七个本地模块，无第三方包依赖。VoltageMonitor 需要 ADC.read_uv 与 ATTN_2_5DB；其他平台先核实接口和 GPIO。PC 回归使用 Python unittest 及模拟对象，不在设备上运行。

## 一、安装与文件

```text
bus_dc_motor_driver/
├── code/
│   ├── bus_dc_motor.py
│   ├── pca9685.py
│   ├── motor.py
│   ├── encoder.py
│   ├── pid.py
│   ├── motor_controller.py
│   ├── voltage_monitor.py
│   └── main.py
├── examples/
├── tests/
├── docs/
├── package.json
├── CHANGELOG.md
├── README.md
└── LICENSE
```

安装本目录的 package.json，或将 code/ 下七个运行库文件上传到设备 /lib/。main.py 是独立示例，不纳入库安装清单。

| 文件 | 功能 |
| --- | --- |
| code/bus_dc_motor.py | 原库兼容入口及开环/PID/刹车模式隔离 |
| code/pca9685.py | I2C、PWM 输出及共享频率配置 |
| code/motor.py | 带符号百分比的底层电机输出 |
| code/encoder.py | A 相上升沿中断计数，B 相判方向及 RPM 换算 |
| code/pid.py | 可独立使用的 PID 类，输出及积分状态限幅 |
| code/motor_controller.py | 多电机采样、独立闭环和统一遥测 |
| code/voltage_monitor.py | ESP32 ADC 电源分压采样、缓存和校准 |
| code/main.py | 开环/四路 PID 完整示例，默认不启动 |
| examples/ | 每个测试项目一个独立文件；含单文件 PC 绘图工具 |
| tests/test_driver.py | 单文件 PC 驱动与故障路径回归 |
| docs/PID_TUNING.md | PID 参数整定方法与当前台架配置 |

保持 package.json 与七个运行库同一版本；只更新 bus_dc_motor.py 而不更新 motor_controller.py 会缺少模式隔离接口。库安装不包含测试、示例或数据。

### 可复制测试入口

以下为完整的 code/main.py；默认禁止运动，确认配置后才启用。

```python
# Python env   : MicroPython v1.29.0 / ESP32-C3
# -*- coding: utf-8 -*-
# @Time    : 2026/11/06
# @Author  : 赵岩松
# @File    : main.py
# @Description : 四路电机兼容开环与编码器闭环测试入口
# @License : MIT

# ======================================== 导入相关模块 ========================================
import time
from machine import Pin, I2C
from pca9685 import PCA9685
from bus_dc_motor import BusDCMotor

# ======================================== 全局变量 ========================================
ARM_MOTORS = False
MODE = "pid"
SCL_PIN = 9
SDA_PIN = 10
PCA_ADDRESS = 0x4F
PWM_FREQUENCY = 1000
ENCODER_PINS = ((5, 6), (7, 8), (3, 2), (1, 0))
PID_PARAMS = ((0.15, 0.6, 0),) * 4
TARGET_RPMS = (30, -40, 50, -60)
VOLTAGE_PIN = 4
RUN_SECONDS = 10
# ======================================== 功能函数 ========================================
# ======================================== 自定义类 ========================================
# ======================================== 初始化配置 ========================================


def _prepare_hardware() -> tuple:
    """显式启用后延时、扫描并创建本示例硬件 / Prepare hardware only when armed."""
    time.sleep(3)
    print("FreakStudio: four-motor driver test")
    i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=400000)
    try:
        devices = i2c.scan()
        print("I2C devices:", [hex(a) for a in devices])
        if not devices:
            raise RuntimeError("No I2C device found")
        if PCA_ADDRESS not in devices:
            raise RuntimeError("Device not found at expected address")
        # 该器件无固定芯片 ID；构造时写 MODE1 检查通信响应。
        pca = PCA9685(i2c, PCA_ADDRESS)
        return i2c, pca
    except BaseException:
        try:
            if hasattr(i2c, "deinit"):
                i2c.deinit()
        except Exception:
            pass
        raise


# ======================================== 主程序 ========================================
def run() -> None:
    """执行有限时长测试；默认禁用，不创建硬件 / Run a bounded test only when armed."""
    if not ARM_MOTORS:
        print("FreakStudio: motors disabled; review wiring and set ARM_MOTORS=True")
        return
    if MODE not in ("legacy", "pid") or not 0 < RUN_SECONDS <= 30:
        raise ValueError("Check MODE and duration (0,30] seconds")
    i2c, pca = _prepare_hardware()
    motor = None
    voltage_monitor = None
    try:
        if MODE == "legacy":
            # 旧位置参数仍可用；新示例选择默认低电平停止，避免默认全高刹车。
            motor = BusDCMotor(pca, 4, startup_brake=False, pwm_frequency=PWM_FREQUENCY)
            motor.set_motor_speed(1, 1900, 0)
            time.sleep(2)
            motor.stop_motor(1)
            time.sleep(2)
            motor.set_motor_speed(1, 1900, 1)
            time.sleep(2)
            motor.break_motor(1)
            time.sleep(1)
        else:
            # 仅闭环/电压模式导入相关依赖，旧开环用法不占编码器与 ADC GPIO。
            from voltage_monitor import VoltageMonitor

            voltage_monitor = VoltageMonitor(pin=VOLTAGE_PIN)
            motor = BusDCMotor(
                pca,
                4,
                encoder_pins=ENCODER_PINS,
                pid_params=PID_PARAMS,
                voltage_monitor=voltage_monitor,
                ppr=13,
                gear_ratio=20,
                startup_brake=False,
                pwm_frequency=PWM_FREQUENCY,
                output_limit=(-50, 50),
            )
            time.sleep_ms(100)
            motor.update()
            print("Supply voltage:", motor.get_voltage())
            if not 6 < motor.get_voltage() < 9:
                raise RuntimeError("Check supply; this example expects 7.4 V motor system")
            motor.set_target_rpms(TARGET_RPMS)
            for i in range(1, 5):
                motor.set_pid(i, 0.15, 0.6, 0)
            motor.start_all()
            start = time.ticks_ms()
            print("elapsed_ms,id,target_rpm,actual_rpm,pwm,count,direction,voltage")
            while time.ticks_diff(time.ticks_ms(), start) < RUN_SECONDS * 1000:
                if motor.update():
                    voltage = motor.get_voltage()
                    if not 6 < voltage < 9:
                        raise RuntimeError("Supply outside example range")
                    fields = motor.get_telemetry()
                    for i in range(1, 5):
                        print(
                            "%d,%d,%s,%s,%s,%d,%d,%s"
                            % (
                                time.ticks_diff(time.ticks_ms(), start),
                                i,
                                TARGET_RPMS[i - 1],
                                motor.get_motor_rpm(i),
                                fields[(i - 1) * 8 + 2],
                                motor.get_encoder_count(i),
                                motor.get_encoder_direction(i),
                                voltage,
                            )
                        )
                time.sleep_ms(5)
    except KeyboardInterrupt:
        print("Interrupted")
        raise
    except OSError as exc:
        print("Hardware communication error:", exc)
        raise
    except Exception as exc:
        print("Motor example failed:", exc)
        raise
    finally:
        try:
            if motor is not None:
                try:
                    motor.stop_all()
                    if MODE == "pid":
                        motor.set_target_rpms((0, 0, 0, 0))
                finally:
                    motor.deinit()
        finally:
            # 本示例拥有 ADC；驱动兼容入口不释放调用方注入的监测器。
            try:
                if voltage_monitor is not None:
                    voltage_monitor.deinit()
            finally:
                pca.deinit()
                if hasattr(i2c, "deinit"):
                    i2c.deinit()
        print("All configured motors stopped; resources released")


if __name__ == "__main__":
    run()
```

## 二、保留的旧接口

```python
from bus_dc_motor import BusDCMotor
motor = BusDCMotor(pca9685, 4)
motor.set_motor_speed(1, 1900, 0)  # 原始 PWM 数值、方向 0 正转
motor.stop_motor(1)
motor.set_motor_speed(1, 1900, 1)  # 方向 1 反转
motor.break_motor(1)               # 保留原拼写：两输入置高刹车
motor.stop_all()
```

上例会实际运行电机，先核对接线和负载。motor_id 为 1～motor_count，motor_count 为 1～4。

为兼容原库，构造默认将整片频率设为 1000 Hz，并将 CH0～CH7 全部置高刹车，即使 motor_count 小于四也如此。新应用推荐 `BusDCMotor(pca9685, 4, startup_brake=False)`，让所配置电机默认置低停转。原调速的调试 print 不再保留，非法类型校验更严格，换向先关闭非工作输入；最终输出与原接口语义一致。

旧 speed 范围保留 **1900～4095**，不是 RPM 或百分比。它是旧 API 的约束，不是“低于此值就没有足够逻辑高电平”的硬件结论；PWM 占空比与高电平幅值不同。新增 PID 可以输出更低占空比。

## 三、ESP32-C3 接线与参数

| 电机 ID | PCA 通道 A/B | 编码器 GPIO A/B |
| --- | --- | --- |
| 1 | 0 / 1 | 5 / 6 |
| 2 | 2 / 3 | 7 / 8 |
| 3 | 4 / 5 | 3 / 2 |
| 4 | 6 / 7 | 1 / 0 |

本板 I2C SCL=GPIO9、SDA=GPIO10，400 kHz，地址 0x4F。以上仅为已测板接线，不适用于任意主控。编码器与 I2C 信号电平须适合主控 GPIO。电机独立供电并共地，电源电压/电流按电机与板级规格选择，不能仅由驱动芯片上限决定。

本项目电机额定 7.4 V；电源监测分压 GPIO4，上端 140 kΩ、下端 20 kΩ，换算倍率 8。默认使用 ADC 2.5 dB 衰减、read_uv、16 次平均、约 200 ms 更新；已使用可调电源和万用表完成校准验证。

当前实机 machine.Encoder 不存在，采用 GPIO 软件中断；PPR=13、减速比=20、A 相上升沿计数，暂按 260 次/输出轴圈：

```text
RPM = 本周期有符号计数增量 / (PPR × gear_ratio) × 60 / 实测周期秒数
```

需要按实际电机标定 PPR、减速比与符号，不能把其他计数方式的四倍频分辨率直接填入。

## 四、完整闭环调用

1. 将 `code/` 下七个库文件上传到设备 `/lib/`，将 [code/main.py](code/main.py) 上传为 `/main.py`。首次保留 `ARM_MOTORS=False`，运行后仅提示禁用，不初始化硬件。
2. 按上表确认接线、电机额定电压、编码器分辨率及四路方向。查看 main.py 的 GPIO、PCA 地址、目标转速和运行时长配置。
3. 需要旧接口测试时设置 `MODE="legacy"`；四路闭环设置 `MODE="pid"`。准备运行时显式设置 `ARM_MOTORS=True`。程序延时三秒后扫描 I2C；PID 模式检查电压、有限时长运行并打印 CSV。
4. 应用结束先停止输出，再调用 `motor.deinit()` 注销自有 IRQ。由调用方另外释放其创建的 VoltageMonitor 和 I2C；不要关闭其他模块共享的总线。

以 main.py 为完整调用示例。examples/ 中每个板测文件均独立运行，只需额外安装 code/ 中的运行库；不需要上传其他测试脚本，默认禁止运动。

PID 0.15/0.6/0 是现有电机低速短时测试的候选参数，不是所有电机/负载通用参数。构造默认输出范围为 ±100%，实机示例主动限制为 ±50%。积分限幅限制积分状态，实际积分输出还要乘 Ki。

## 五、统一接口与调度

| 接口 | 功能与约束 |
| --- | --- |
| set_target_rpm(id,rpm) | 带符号目标 RPM；不自动启动 |
| set_target_rpms(rpms) | 按 ID 设置全部目标 |
| set_pid(id,kp,ki,kd) | 在线独立设置；None 保留原值 |
| start_motor(id) / start_all() | 显式启用闭环，下次 update 更新输出 |
| get_motor_rpm(id) | 最近一次更新采样的实际 RPM |
| get_encoder_count(id) | 累计有符号计数 |
| get_encoder_direction(id) | 最近脉冲方向；停止后可能保留旧方向 |
| stop_motor(id) / stop_all() | 立即停止并禁用 PID，保留目标供显式重启 |
| break_motor(id) | 禁用该路 PID，双输入置高刹车；后续 update 不覆盖 |
| get_voltage() | 返回注入监测器的缓存电压 V，首次 update 前可能为 None |
| get_modes() | 每路 stopped/open/pid/brake 状态 |
| get_telemetry() | 每路 target/RPM/PWM/error/Kp/Ki/Kd/enabled 八字段，末尾全 PID 启动位 |
| deinit() | 停止输出、注销本对象拥有的编码器 IRQ；不释放注入的 PCA、I2C 或电压监测器 |
| update() | 协作式调度，默认内部限为至少 100 ms 一次；应用仍须持续调用 |

未提供 encoder_pins 时，旧开环功能可独立使用；调用闭环或反馈接口会明确报错。未注入 voltage_monitor 时 get_voltage 报错，不默认抢占未知主控的 ADC GPIO。

每个电机一次只能处于一种模式。调用旧开环 API 会关闭该路 PID；从开环或刹车设置 RPM 先停止输出，须显式 start 才进入 PID。处于 PID 模式时可在线修改目标和参数。stop 不等于清目标，如不希望以后恢复旧目标，应另设 RPM=0。

不要让第二个控制器同时操作相同通道。MotorController 的选择更新会继续采集全部编码器，但仅写 PID 模式的输出，防止开环和刹车被覆盖。应用长时间阻塞时没有后台线程补偿；硬件异常时尽力停机，但通信故障可能使某路无法关闭，应保留外部断电手段。

## 六、PWM 频率与兼容变化

PCA9685 通道共享频率。pwm_frequency 默认 1000，可指定 50；不能独立让电机通道 1000 Hz、剩余通道 50 Hz。调用构造器会配置整片频率，必须由一个调度入口管理。

本次修正 PRE_SCALE 缺少 -1 的公式：1000 Hz 设定读回 5，按标称 25 MHz 时钟约 1017.25 Hz；50 Hz 读回 121，计算约 50.03 Hz。旧错误公式的 1000 Hz 设定对应约 871.93 Hz，升级后可能需要重新核对控制表现。数值是分频计算，不是波形仪器实测频率。

50 Hz 实机能驱动电机，但同组 PID 下部分瞬时 RPM 与 ADC 电压读数波动更大，不作为默认推荐或供电验收通过。当前版本不包含舵机、机械臂、底盘距离/转角控制、Wi-Fi 或网页端。

## 七、测试与迁移

每个测试项目保留一个文件，板测脚本只依赖 `code/` 中的驱动。核对脚本内接线、供电和时长后，显式设置 `ARM_MOTORS=True`，每次只运行一个项目。

| 文件 | 测试项目 |
| --- | --- |
| code/main.py | 旧开环或四路 PID 完整使用入口 |
| examples/bus_dc_motor_demo.py | 旧接口、开环/PID隔离及停止/刹车兼容性 |
| examples/single_motor_pid_demo.py | 指定一路电机正反转，其余停止 |
| examples/four_motor_pid_demo.py | 四路不同目标和混合方向 |
| examples/tuning_profile.py | 分路 PI、测速窗口与起步补偿整定 |
| examples/performance_profile.py | 100/30/20ms 控制周期和缓存/窗口比较 |
| examples/realtime_audit.py | 四路全周期、I2C、PID、ADC、GC 和输出完成时差 |
| examples/i2c_benchmark.py | 400kHz/1MHz、预分配与批量写比较 |
| examples/switch_benchmark.py | 正常单帧关断、急停与换向分段计时 |
| examples/pc_live_plot.py | PC 实时四路曲线、指标、CSV 和录屏 |
| tests/test_driver.py | PC 驱动参数、IRQ、停机异常、资源与安装依赖回归 |

在仓库根目录运行 PC 回归：

```powershell
python -m unittest discover -s motor_drivers/bus_dc_motor_driver/tests -p 'test_*.py'
```

当前保留16项回归，不访问真实设备。检查范围包括运行库故障路径、单文件测试的默认禁止运动、安装依赖及分路窗口；不是实机测试的替代。

PC 绘图工具也为单文件，上传时只上传所选项目及运行库：

```powershell
pip install matplotlib numpy pillow pyserial mpremote
python motor_drivers/bus_dc_motor_driver/examples/pc_live_plot.py --profile tuning_profile --port COM8 --baud 921600 --run --seconds 15 --out pid-results-01
```

可选项目为 `performance_profile`、`tuning_profile`、`realtime_audit`、`i2c_benchmark`、`switch_benchmark`。输出目录须不存在。明确 `--run` 后才上传并运行电机；先备份/校验，等待15秒，不改设备 main.py。运行错误或关图会通知设备停止并限时等待采集线程，结束状态写入本次输出目录。串口断线时不能把线程退出当成物理停机确认。

性能、调参和总线优化均为独立台架实验，不替换七模块默认 API/参数。记录会保存到用户指定目录，组件仓库不收录 CSV、日志、统计 JSON、录屏及过程报告。完整历史记录和复算工具见[云测试文档](https://f1829ryac0m.feishu.cn/docx/Kee4dEPucoFTGTxnyE4cKEEGnce)，PID 调整方法见[整定指南](docs/PID_TUNING.md)。

已完成 ESP32-C3 单路及四路 PID 台架测试，编码器读取与电压校准经开发者确认。分路细调后的后段均值/波动基础验收20/20通过，仍有启动超调；批量写和换向关断优化已有短时实机比较，不能据此推及带载整车或长期实时性。

运行库执行仓库设备规范检查；独立设备测试执行格式、语法、默认禁用及依赖检查，PC工具和夹具执行格式与回归。实验工具不宣称满足运行库级全部双语API规范。BusDCMotor/PCA9685保留李清水署名，新增模块和测试署名赵岩松。

## 版本记录

| 版本 | 日期 | 作者 | 修改说明 |
| --- | --- | --- | --- |
| 1.1.0 | 2026-11-06 | 赵岩松；原库署名保留 | 四路 PID、编码器、电压接口及规范化；已完成实机 PID 测试 |
| 1.0.0 | 原库未标明日期 | 李清水 | 原始总线直流电机接口 |

## 联系方式

GitHub 问题反馈：[当前 fork 的 Issues](https://github.com/yangcong-bit/GraftSense-Drivers-MicroPython/issues)。原库：[FreakStudioCN/GraftSense-Drivers-MicroPython](https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython)。来源文件未提供联系邮箱，暂未填写。

## 许可与来源

包根 [LICENSE](LICENSE) 保留原库 MIT 许可及 FreakStudio 版权声明。BusDCMotor 原库作者李清水的署名保留，PCA9685 保留其已有参考来源。新增模块来自现有四编码器电机项目，本次按兼容升级迁入本包；测试证据与过程见上面的云测试文档，不声明其他驱动包已回归。
