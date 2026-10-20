# PR119 安装与初始化迁移说明

本次调整只作用于 PR119 异步包。同步驱动目录保持原样。
不同异步包原先存在同名、内容不同的安装目标；以下公开模块使用独立名称，避免由安装顺序决定可用接口。旧的不明确入口不再由这些包安装。

| 驱动包 | 原导入模块 | 新导入模块 |
|---|---|---|
| `sensors/fde_frost_async_driver` | `modbus_rtu_async` | `fde_frost_modbus_rtu_async` |
| `sensors/ina219_async_driver` | `ina_ti_async` | `ina219_async` |
| `sensors/ina226_async_driver` | `ina_ti_async` | `ina226_async` |
| `sensors/mcp1081_async_driver` | `modbus_rtu_async` | `mcp1081_modbus_rtu_async` |
| `sensors/mcp1081_async_driver` | `mer_async` | `mcp1081_mer_async` |
| `sensors/mcp_async_driver` | `mer_async` | `mcp_mer_async` |
| `sensors/mse_soil_sensor_async_driver` | `modbus_rtu_async` | `mse_soil_modbus_rtu_async` |
| `sensors/spring_vibration_async_driver` | `vibration_sensor_async` | `spring_vibration_async` |
| `sensors/vibration_async_driver` | `vibration_sensor_async` | `vibration_async` |

内部来源依赖与辅助模块的完整路径见 [async_install_modules.json](async_install_modules.json) 和 [async_dependency_modules.json](async_dependency_modules.json)。各包示例已同步更新。
升级不会自动删除旧文件。若曾安装旧异步版本，应按新的清单重装依赖；被旧包覆盖过的同步模块需要重新安装对应同步包。

## 初始化与超时

- AS7341、BMA423、BH1750、LSM6DSOX、DPS310、APDS9960、SI1145，以及独立 MPU6500/AK8963 异步实例使用前需要 `await initialize_async()`；组合 MPU9250 使用 `create_async()` 或 `start_async()`。
- PCF8574 IO8 的主循环使用 `await dispatch_pending_async()` 消费 IRQ 标记。
- MicroPython 1.23 未提供内建 `TimeoutError`；这些异步包在该固件中使用 `asyncio.TimeoutError`，应用可 `except asyncio.TimeoutError`。在 CPython 中保留内建异常类型。`IOError` 在 MicroPython 中兼容映射到 `OSError`。
- AD8232 设备端 ECG 处理需要带 `ulab.numpy` 和 `ulab.scipy` 的固件；UART 主机接口不需要数值库。

## 实现与验证边界

私有类 const 的运行时属性只补回来源原值；位域范围判断改用相同掩码上界，避免依赖 MicroPython 不支持的 int.bit_length。原同步算法、配置数据和严格微秒/PIO 波形实现保持不变。
底层短 I2C/SPI/UART 事务及部分来源错误重试仍同步；DHT11 连续波形捕获明确为 NOT_ASYNC_SAFE。源码编译、安装检查和模拟外设上的 MicroPython 执行不代替目标板验证，也不代表执行了 224 个包的全部公开 API。
