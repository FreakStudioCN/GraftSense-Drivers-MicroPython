# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19 00:00
# @Author  : jgromes
# @File    : sx126x.py
# @Description : SX126X base class providing SPI communication, register access, and common LoRa/GFSK operations
# @License : MIT
# pylint: disable=wildcard-import,unused-wildcard-import,undefined-variable,function-redefined

__version__ = "1.0.0"
__author__ = "jgromes"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

from micropython import const
from _sx126x import *

from sys import implementation

# MicroPython 平台导入
if implementation.name == "micropython":
    from machine import SPI, Pin
    from utime import sleep_ms, sleep_us, ticks_ms, ticks_us, ticks_diff

# CircuitPython 平台适配
if implementation.name == "circuitpython":
    import digitalio
    import busio
    from time import sleep, monotonic_ns

    _MS_PER_NS = const(1000000)
    _US_PER_NS = const(1000)
    _MS_PER_S = const(1000)
    _TICKS_MAX = const(536870911)
    _TICKS_PERIOD = const(536870912)
    _TICKS_HALFPERIOD = const(268435456)

    def sleep_ms(ms):
        sleep(ms / 1000)

    def sleep_us(us):
        sleep(us / 1000000)

    def ticks_ms():
        return (monotonic_ns() // _MS_PER_NS) & _TICKS_MAX

    def ticks_us():
        return (monotonic_ns() // _US_PER_NS) & _TICKS_MAX

    def ticks_diff(end, start):
        diff = (end - start) & _TICKS_MAX
        diff = ((diff + _TICKS_HALFPERIOD) & _TICKS_MAX) - _TICKS_HALFPERIOD
        return diff


class SX126X:

    def __init__(self, spi_bus, clk, mosi, miso, cs, irq, rst, gpio):
        self._irq = irq
        # MicroPython 平台：创建 SPI 和 Pin 对象
        if implementation.name == "micropython":
            try:
                # Pycom 变体 MicroPython
                self.spi = SPI(spi_bus, mode=SPI.MASTER, baudrate=2000000, pins=(clk, mosi, miso))
            except:
                # 通用 MicroPython 变体
                self.spi = SPI(spi_bus, baudrate=2000000, sck=Pin(clk), mosi=Pin(mosi), miso=Pin(miso))
            # 初始化控制引脚
            self.cs = Pin(cs, mode=Pin.OUT)
            self.irq = Pin(irq, mode=Pin.IN)
            self.rst = Pin(rst, mode=Pin.OUT)
            self.gpio = Pin(gpio, mode=Pin.IN)

        # CircuitPython 平台：创建 DigitalInOut 对象
        if implementation.name == "circuitpython":
            self.spi = busio.SPI(clk, MOSI=mosi, MISO=miso)
            while not self.spi.try_lock():
                pass
            self.spi.configure(baudrate=2000000, phase=0, polarity=0, bits=8)
            self.spi.unlock()
            self.cs = digitalio.DigitalInOut(cs)
            # CS 初始为高（不选中）
            self.cs.switch_to_output(value=True)
            self.irq = digitalio.DigitalInOut(irq)
            self.irq.switch_to_input()
            self.rst = digitalio.DigitalInOut(rst)
            # RST 初始为高
            self.rst.switch_to_output(value=True)
            self.gpio = digitalio.DigitalInOut(gpio)
            self.gpio.switch_to_input()

        # LoRa 配置参数
        self._bwKhz = 0
        self._sf = 0
        self._bw = 0
        self._cr = 0
        self._ldro = 0
        self._crcType = 0
        self._preambleLength = 0
        self._tcxoDelay = 0
        self._headerType = 0
        self._implicitLen = 0
        self._txIq = 0
        self._rxIq = 0
        self._invertIQ = 0
        self._ldroAuto = True

        # GFSK 配置参数
        self._br = 0
        self._freqDev = 0
        self._rxBw = 0
        self._rxBwKhz = 0
        self._pulseShape = 0
        self._crcTypeFSK = 0
        self._preambleLengthFSK = 0
        self._addrComp = 0
        self._syncWordLength = 0
        self._whitening = 0
        self._packetType = 0
        self._dataRate = 0
        self._packetLength = 0
        self._preambleDetectorLength = 0

    def begin(self, bw, sf, cr, syncWord, currentLimit, preambleLength, tcxoVoltage, useRegulatorLDO=False, txIq=False, rxIq=False):
        # 保存 LoRa 参数
        self._bwKhz = bw
        self._sf = sf

        # 设置默认值
        self._bw = SX126X_LORA_BW_125_0
        self._cr = SX126X_LORA_CR_4_7
        self._ldro = 0x00
        self._crcType = SX126X_LORA_CRC_ON
        self._preambleLength = preambleLength
        self._tcxoDelay = 0
        self._headerType = SX126X_LORA_HEADER_EXPLICIT
        self._implicitLen = 0xFF

        # IQ 配置
        self._txIq = txIq
        self._rxIq = rxIq
        self._invertIQ = SX126X_LORA_IQ_STANDARD

        # 复位芯片
        state = self.reset()
        ASSERT(state)

        # 进入待机模式
        state = self.standby()
        ASSERT(state)

        # 配置 TCXO（如果启用）
        if tcxoVoltage > 0.0:
            state = self.setTCXO(tcxoVoltage)
            ASSERT(state)

        # 设置为 LoRa 模式
        state = self.config(SX126X_PACKET_TYPE_LORA)
        ASSERT(state)

        # 选择稳压器模式
        if useRegulatorLDO:
            state = self.setRegulatorLDO()
        else:
            state = self.setRegulatorDCDC()
        ASSERT(state)

        # 配置 LoRa 参数
        state = self.setSpreadingFactor(sf)
        ASSERT(state)

        state = self.setBandwidth(bw)
        ASSERT(state)

        state = self.setCodingRate(cr)
        ASSERT(state)

        state = self.setSyncWord(syncWord)
        ASSERT(state)

        state = self.setCurrentLimit(currentLimit)
        ASSERT(state)

        state = self.setPreambleLength(preambleLength)
        ASSERT(state)

        # DIO2 设为射频开关控制
        state = self.setDio2AsRfSwitch(True)
        ASSERT(state)

        return state

    def beginFSK(self, br, freqDev, rxBw, currentLimit, preambleLength, dataShaping, preambleDetectorLength, tcxoVoltage, useRegulatorLDO=False):
        # 设置 GFSK 默认参数
        self._br = 21333
        self._freqDev = 52428
        self._rxBw = SX126X_GFSK_RX_BW_156_2
        self._rxBwKhz = 156.2
        self._pulseShape = SX126X_GFSK_FILTER_GAUSS_0_5
        self._crcTypeFSK = SX126X_GFSK_CRC_2_BYTE_INV
        self._preambleLengthFSK = preambleLength
        self._addrComp = SX126X_GFSK_ADDRESS_FILT_OFF
        self._preambleDetectorLength = preambleDetectorLength

        # 复位芯片
        state = self.reset()
        ASSERT(state)

        # 进入待机模式
        state = self.standby()
        ASSERT(state)

        # 配置 TCXO（如果启用）
        if tcxoVoltage > 0.0:
            state = self.setTCXO(tcxoVoltage)
            ASSERT(state)

        # 设置为 GFSK 模式
        state = self.config(SX126X_PACKET_TYPE_GFSK)
        ASSERT(state)

        # 选择稳压器模式
        if useRegulatorLDO:
            state = self.setRegulatorLDO()
        else:
            state = self.setRegulatorDCDC()
        ASSERT(state)

        # 配置 GFSK 参数
        state = self.setBitRate(br)
        ASSERT(state)

        state = self.setFrequencyDeviation(freqDev)
        ASSERT(state)

        state = self.setRxBandwidth(rxBw)
        ASSERT(state)

        state = self.setCurrentLimit(currentLimit)
        ASSERT(state)

        state = self.setDataShaping(dataShaping)
        ASSERT(state)

        state = self.setPreambleLength(preambleLength)
        ASSERT(state)

        # 默认同步字
        sync = [0x2D, 0x01]
        state = self.setSyncWord(sync, 2)
        ASSERT(state)

        # 默认启用白化
        state = self.setWhitening(True, 0x0100)
        ASSERT(state)

        # 默认可变包长模式
        state = self.variablePacketLengthMode(SX126X_MAX_PACKET_LENGTH)
        ASSERT(state)

        # DIO2 设为射频开关控制
        state = self.setDio2AsRfSwitch(True)
        ASSERT(state)

        return state

    def reset(self, verify=True):
        # MicroPython 复位时序：脉冲式拉低 RST
        if implementation.name == "micropython":
            self.rst.value(1)
            sleep_us(150)
            self.rst.value(0)
            sleep_us(150)
            self.rst.value(1)
            sleep_us(150)

        # CircuitPython 复位时序
        if implementation.name == "circuitpython":
            self.rst.value = True
            sleep_us(150)
            self.rst.value = False
            sleep_us(150)
            self.rst.value = True
            sleep_us(150)

        # 不验证时直接返回成功
        if not verify:
            return ERR_NONE

        # 验证芯片是否正常响应（轮询 standby 直至成功或超时 3s）
        start = ticks_ms()
        while True:
            state = self.standby()
            if state == ERR_NONE:
                return ERR_NONE
            if abs(ticks_diff(start, ticks_ms())) >= 3000:
                return state
            sleep_ms(10)

    def transmit(self, data, len_, addr=0):
        # 进入待机模式
        state = self.standby()
        ASSERT(state)

        # 检查包长度
        if len_ > SX126X_MAX_PACKET_LENGTH:
            return ERR_PACKET_TOO_LONG

        timeout = 0

        # 根据调制模式计算超时时间
        modem = self.getPacketType()
        if modem == SX126X_PACKET_TYPE_LORA:
            # LoRa: 1.5 倍空中时间
            timeout = int((self.getTimeOnAir(len_) * 3) / 2)

        elif modem == SX126X_PACKET_TYPE_GFSK:
            # GFSK: 5 倍空中时间
            timeout = int(self.getTimeOnAir(len_) * 5)

        else:
            return ERR_UNKNOWN

        # 启动发送
        state = self.startTransmit(data, len_, addr)
        ASSERT(state)

        # 等待发送完成（轮询 IRQ 引脚）
        start = ticks_us()
        if implementation.name == "micropython":
            while not self.irq.value():
                yield_()
                if abs(ticks_diff(start, ticks_us())) > timeout:
                    self.clearIrqStatus()
                    self.standby()
                    return ERR_TX_TIMEOUT
        if implementation.name == "circuitpython":
            while not self.irq.value:
                yield_()
                if abs(ticks_diff(start, ticks_us())) > timeout:
                    self.clearIrqStatus()
                    self.standby()
                    return ERR_TX_TIMEOUT

        elapsed = abs(ticks_diff(start, ticks_us()))

        # 计算数据传输率
        self._dataRate = (len_ * 8.0) / (float(elapsed) / 1000000.0)

        # 清除中断状态并返回待机
        state = self.clearIrqStatus()
        ASSERT(state)

        state = self.standby()

        return state

    def receive(self, data, len_, timeout_en, timeout_ms):
        # 进入待机模式
        state = self.standby()
        ASSERT(state)

        timeout = 0

        # 根据调制模式计算接收超时
        modem = self.getPacketType()
        if modem == SX126X_PACKET_TYPE_LORA:
            # LoRa: 100 个符号长度作为超时
            symbolLength = float(1 << self._sf) / float(self._bwKhz)
            timeout = int(symbolLength * 100.0 * 1000.0)
        elif modem == SX126X_PACKET_TYPE_GFSK:
            maxLen = len_
            if len_ == 0:
                maxLen = 0xFF
            # GFSK: 按比特率计算
            brBps = (float(SX126X_CRYSTAL_FREQ) * 1000000.0 * 32.0) / float(self._br)
            timeout = int(((maxLen * 8.0) / brBps) * 1000000.0 * 5.0)
        else:
            return ERR_UNKNOWN

        # 用户指定超时优先
        if timeout_ms == 0:
            pass
        else:
            timeout = timeout_ms * 1000

        # 计算超时寄存器值
        if timeout_en:
            timeoutValue = int(float(timeout) / 15.625)
        else:
            timeoutValue = SX126X_RX_TIMEOUT_NONE

        # 启动接收
        state = self.startReceive(timeoutValue)
        ASSERT(state)

        # 等待接收完成（轮询 IRQ 引脚）
        start = ticks_us()
        if implementation.name == "micropython":
            while not self.irq.value():
                yield_()
                if timeout_en:
                    if abs(ticks_diff(start, ticks_us())) > timeout:
                        self.fixImplicitTimeout()
                        self.clearIrqStatus()
                        self.standby()
                        return ERR_RX_TIMEOUT
        if implementation.name == "circuitpython":
            while not self.irq.value:
                yield_()
                if timeout_en:
                    if abs(ticks_diff(start, ticks_us())) > timeout:
                        self.fixImplicitTimeout()
                        self.clearIrqStatus()
                        self.standby()
                        return ERR_RX_TIMEOUT

        # 隐式报头模式需修复超时
        if self._headerType == SX126X_LORA_HEADER_IMPLICIT and self.getPacketType() == SX126X_PACKET_TYPE_LORA:
            state = self.fixImplicitTimeout()
            ASSERT(state)

        return self.readData(data, len_)

    def transmitDirect(self, frf=0):
        # 直接发送连续载波（用于测试）
        state = ERR_NONE
        if frf != 0:
            state = self.setRfFrequency(frf)
        ASSERT(state)

        data = [SX126X_CMD_NOP]
        return self.SPIwriteCommand([SX126X_CMD_SET_TX_CONTINUOUS_WAVE], 1, data, 1)

    def receiveDirect(self):
        # 直接接收（未实现）
        return ERR_UNKNOWN

    def scanChannel(self):
        # 仅 LoRa 模式支持信道活动检测（CAD）
        if self.getPacketType() != SX126X_PACKET_TYPE_LORA:
            return ERR_WRONG_MODEM

        state = self.standby()
        ASSERT(state)

        # 配置 CAD 中断
        state = self.setDioIrqParams(SX126X_IRQ_CAD_DETECTED | SX126X_IRQ_CAD_DONE, SX126X_IRQ_CAD_DETECTED | SX126X_IRQ_CAD_DONE)
        ASSERT(state)

        state = self.clearIrqStatus()
        ASSERT(state)

        # 启动 CAD
        state = self.setCad()
        ASSERT(state)

        # 等待 CAD 完成
        if implementation.name == "micropython":
            while not self.irq.value():
                yield_()
        if implementation.name == "circuitpython":
            while not self.irq.value:
                yield_()

        cadResult = self.getIrqStatus()
        if cadResult & SX126X_IRQ_CAD_DETECTED:
            self.clearIrqStatus()
            return LORA_DETECTED
        elif cadResult & SX126X_IRQ_CAD_DONE:
            self.clearIrqStatus()
            return CHANNEL_FREE

        return ERR_UNKNOWN

    def sleep(self, retainConfig=True):
        # 休眠模式配置
        sleepMode = [SX126X_SLEEP_START_WARM | SX126X_SLEEP_RTC_OFF]
        if not retainConfig:
            # 冷启动，不保留配置
            sleepMode = [SX126X_SLEEP_START_COLD | SX126X_SLEEP_RTC_OFF]
        state = self.SPIwriteCommand([SX126X_CMD_SET_SLEEP], 1, sleepMode, 1, False)

        sleep_us(500)

        return state

    def standby(self, mode=SX126X_STANDBY_RC):
        # 进入待机模式
        data = [mode]
        return self.SPIwriteCommand([SX126X_CMD_SET_STANDBY], 1, data, 1)

    def setDio1Action(self, func):
        # 注册 DIO1 中断回调
        try:
            # Pycom 变体 MicroPython
            self.irq.callback(trigger=Pin.IRQ_RISING, handler=func)
        except:
            # 通用 MicroPython 变体
            self.irq.irq(trigger=Pin.IRQ_RISING, handler=func)

    def clearDio1Action(self):
        # 清除 DIO1 中断回调（重新创建 Pin 对象以解除 irq）
        if implementation.name == "micropython":
            self.irq = Pin(self._irq, mode=Pin.IN)

        if implementation.name == "circuitpython":
            self.irq.deinit()
            self.irq = digitalio.DigitalInOut(self._irq)
            self.irq.switch_to_input()

    def startTransmit(self, data, len_, addr=0):
        # 检查包长度
        if len_ > SX126X_MAX_PACKET_LENGTH:
            return ERR_PACKET_TOO_LONG

        # 地址过滤模式下需要额外一个字节
        if self._addrComp != SX126X_GFSK_ADDRESS_FILT_OFF and len_ > (SX126X_MAX_PACKET_LENGTH - 1):
            return ERR_PACKET_TOO_LONG

        state = ERR_NONE
        modem = self.getPacketType()
        if modem == SX126X_PACKET_TYPE_LORA:
            # LoRa IQ 配置
            if self._txIq:
                self._invertIQ = SX126X_LORA_IQ_INVERTED
            else:
                self._invertIQ = SX126X_LORA_IQ_STANDARD

            # 隐式报头模式下校验包长度
            if self._headerType == SX126X_LORA_HEADER_IMPLICIT:
                if len_ != self._implicitLen:
                    return ERR_INVALID_PACKET_LENGTH

            state = self.setPacketParams(self._preambleLength, self._crcType, len_, self._headerType, self._invertIQ)
        elif modem == SX126X_PACKET_TYPE_GFSK:
            # GFSK 固定包长模式下校验包长度
            if self._packetType == SX126X_GFSK_PACKET_FIXED:
                if len_ != self._packetLength:
                    return ERR_INVALID_PACKET_LENGTH

            state = self.setPacketParamsFSK(
                self._preambleLengthFSK,
                self._crcTypeFSK,
                self._syncWordLength,
                self._addrComp,
                self._whitening,
                self._packetType,
                len_,
                self._preambleDetectorLength,
            )
        else:
            return ERR_UNKNOWN
        ASSERT(state)

        # 配置 TX 完成 + 超时中断
        state = self.setDioIrqParams(SX126X_IRQ_TX_DONE | SX126X_IRQ_TIMEOUT, SX126X_IRQ_TX_DONE)
        ASSERT(state)

        # 设置缓冲区基地址
        state = self.setBufferBaseAddress()
        ASSERT(state)

        # 写入数据到发送缓冲区
        state = self.writeBuffer(data, len_)
        ASSERT(state)

        # 清除所有中断标志
        state = self.clearIrqStatus()
        ASSERT(state)

        # 修复灵敏度配置
        state = self.fixSensitivity()
        ASSERT(state)

        # 启动发射
        state = self.setTx(SX126X_TX_TIMEOUT_NONE)
        ASSERT(state)

        # 等待 GPIO 就绪
        if implementation.name == "micropython":
            while self.gpio.value():
                yield_()

        if implementation.name == "circuitpython":
            while self.gpio.value:
                yield_()

        return state

    def startReceive(self, timeout=SX126X_RX_TIMEOUT_INF):
        state = ERR_NONE
        modem = self.getPacketType()
        if modem == SX126X_PACKET_TYPE_LORA:
            # LoRa IQ 配置
            if self._rxIq:
                self._invertIQ = SX126X_LORA_IQ_INVERTED
            else:
                self._invertIQ = SX126X_LORA_IQ_STANDARD

            state = self.setPacketParams(self._preambleLength, self._crcType, self._implicitLen, self._headerType, self._invertIQ)
        elif modem == SX126X_PACKET_TYPE_GFSK:
            state = self.setPacketParamsFSK(
                self._preambleLengthFSK,
                self._crcTypeFSK,
                self._syncWordLength,
                self._addrComp,
                self._whitening,
                self._packetType,
                self._packetLength,
                self._preambleDetectorLength,
            )
        else:
            return ERR_UNKNOWN
        ASSERT(state)

        # 公共接收初始化
        state = self.startReceiveCommon()
        ASSERT(state)

        # 进入接收模式
        state = self.setRx(timeout)

        return state

    def startReceiveDutyCycle(self, rxPeriod, sleepPeriod):
        # 计算过渡时间
        transitionTime = int(self._tcxoDelay + 1000)
        sleepPeriod -= transitionTime

        # 转换为原始寄存器值（单位：15.625us）
        rxPeriodRaw = int((rxPeriod * 8) / 125)
        sleepPeriodRaw = int((sleepPeriod * 8) / 125)

        if rxPeriodRaw & 0xFF000000 or rxPeriodRaw == 0:
            return ERR_INVALID_RX_PERIOD

        if sleepPeriodRaw & 0xFF000000 or sleepPeriodRaw == 0:
            return ERR_INVALID_SLEEP_PERIOD

        state = self.startReceiveCommon()
        ASSERT(state)

        # 设置占空比接收周期
        data = [
            int((rxPeriodRaw >> 16) & 0xFF),
            int((rxPeriodRaw >> 8) & 0xFF),
            int(rxPeriodRaw & 0xFF),
            int((sleepPeriodRaw >> 16) & 0xFF),
            int((sleepPeriodRaw >> 8) & 0xFF),
            int(sleepPeriodRaw & 0xFF),
        ]
        return self.SPIwriteCommand([SX126X_CMD_SET_RX_DUTY_CYCLE], 1, data, 6)

    def startReceiveDutyCycleAuto(self, senderPreambleLength=0, minSymbols=8):
        # 自动计算占空比接收参数
        if senderPreambleLength == 0:
            senderPreambleLength = self._preambleLength

        sleepSymbols = int(senderPreambleLength - 2 * minSymbols)

        # 前导码太短，改为连续接收
        if (2 * minSymbols) > senderPreambleLength:
            return self.startReceive()

        symbolLength = int(((10 * 1000) << self._sf) / (10 * self._bwKhz))
        sleepPeriod = symbolLength * sleepSymbols

        wakePeriod = int(max((symbolLength * (senderPreambleLength + 1) - (sleepPeriod - 1000)) / 2, symbolLength * (minSymbols + 1)))

        # 休眠时段太短，改为连续接收
        if sleepPeriod < (self._tcxoDelay + 1016):
            return self.startReceive()

        return self.startReceiveDutyCycle(wakePeriod, sleepPeriod)

    def startReceiveCommon(self):
        # 配置接收中断
        state = self.setDioIrqParams(SX126X_IRQ_RX_DONE | SX126X_IRQ_TIMEOUT | SX126X_IRQ_CRC_ERR | SX126X_IRQ_HEADER_ERR, SX126X_IRQ_RX_DONE)
        ASSERT(state)

        # 设置缓冲区基地址
        state = self.setBufferBaseAddress()
        ASSERT(state)

        # 清除中断标志
        state = self.clearIrqStatus()

        # 根据调制模式设置包参数
        modem = self.getPacketType()
        if modem == SX126X_PACKET_TYPE_LORA:
            state = self.setPacketParams(self._preambleLength, self._crcType, self._implicitLen, self._headerType, self._invertIQ)
        elif modem == SX126X_PACKET_TYPE_GFSK:
            state = self.setPacketParamsFSK(
                self._preambleLengthFSK, self._crcTypeFSK, self._syncWordLength, self._addrComp, self._whitening, self._packetType
            )
        else:
            return ERR_UNKNOWN

        return state

    def readData(self, data, len_):
        # 进入待机模式读取数据
        state = self.standby()
        ASSERT(state)

        # 检查 CRC 和报头错误
        irq = self.getIrqStatus()
        crcState = ERR_NONE
        if irq & SX126X_IRQ_CRC_ERR or irq & SX126X_IRQ_HEADER_ERR:
            crcState = ERR_CRC_MISMATCH

        # 获取实际包长度
        length = len_
        if len_ == SX126X_MAX_PACKET_LENGTH:
            length = self.getPacketLength()

        # 从接收缓冲区读取数据
        state = self.readBuffer(data, length)
        ASSERT(state)

        # 清除中断标志
        state = self.clearIrqStatus()

        ASSERT(crcState)

        return state

    def setBandwidth(self, bw):
        # 仅 LoRa 模式支持
        if self.getPacketType() != SX126X_PACKET_TYPE_LORA:
            return ERR_WRONG_MODEM

        # 校验带宽范围
        if not ((bw > 0) and (bw < 510)):
            return ERR_INVALID_BANDWIDTH

        # 带宽映射表（基于 bw/2 四舍五入值）
        bw_div2 = int(bw / 2 + 0.01)
        switch = {
            3: SX126X_LORA_BW_7_8,
            5: SX126X_LORA_BW_10_4,
            7: SX126X_LORA_BW_15_6,
            10: SX126X_LORA_BW_20_8,
            15: SX126X_LORA_BW_31_25,
            20: SX126X_LORA_BW_41_7,
            31: SX126X_LORA_BW_62_5,
            62: SX126X_LORA_BW_125_0,
            125: SX126X_LORA_BW_250_0,
            250: SX126X_LORA_BW_500_0,
        }
        try:
            self._bw = switch[bw_div2]
        except:
            return ERR_INVALID_BANDWIDTH

        self._bwKhz = bw
        return self.setModulationParams(self._sf, self._bw, self._cr, self._ldro)

    def setSpreadingFactor(self, sf):
        # 仅 LoRa 模式支持
        if self.getPacketType() != SX126X_PACKET_TYPE_LORA:
            return ERR_WRONG_MODEM

        # 校验扩频因子范围
        if not ((sf >= 5) and (sf <= 12)):
            return ERR_INVALID_SPREADING_FACTOR

        self._sf = sf
        return self.setModulationParams(self._sf, self._bw, self._cr, self._ldro)

    def setCodingRate(self, cr):
        # 仅 LoRa 模式支持
        if self.getPacketType() != SX126X_PACKET_TYPE_LORA:
            return ERR_WRONG_MODEM

        # 校验编码率范围
        if not ((cr >= 5) and (cr <= 8)):
            return ERR_INVALID_CODING_RATE

        # 编码率偏移（CR 值 - 4 = 寄存器值）
        self._cr = cr - 4
        return self.setModulationParams(self._sf, self._bw, self._cr, self._ldro)

    def setSyncWord(self, syncWord, *args):
        # LoRa 模式：设置 LoRa 同步字寄存器
        if self.getPacketType() == SX126X_PACKET_TYPE_LORA:
            if len(args) > 0:
                controlBits = args[0]
            else:
                controlBits = 0x44
            data = [int((syncWord & 0xF0) | ((controlBits & 0xF0) >> 4)), int(((syncWord & 0x0F) << 4) | (controlBits & 0x0F))]
            return self.writeRegister(SX126X_REG_LORA_SYNC_WORD_MSB, data, 2)

        # GFSK 模式：设置同步字寄存器
        elif self.getPacketType() == SX126X_PACKET_TYPE_GFSK:
            len_ = args[0]
            if len_ > 8:
                return ERR_INVALID_SYNC_WORD

            state = self.writeRegister(SX126X_REG_SYNC_WORD_0, syncWord, len_)
            ASSERT(state)

            self._syncWordLength = len_ * 8
            state = self.setPacketParamsFSK(
                self._preambleLengthFSK,
                self._crcTypeFSK,
                self._syncWordLength,
                self._addrComp,
                self._whitening,
                self._packetType,
                self._packetLength,
                self._preambleDetectorLength,
            )

            return state

        else:
            return ERR_WRONG_MODEM

    def setCurrentLimit(self, currentLimit):
        # 校验电流限制范围（0 ~ 140 mA）
        if not ((currentLimit >= 0) and (currentLimit <= 140)):
            return ERR_INVALID_CURRENT_LIMIT

        # 原始值 = mA / 2.5
        rawLimit = [int(currentLimit / 2.5)]

        return self.writeRegister(SX126X_REG_OCP_CONFIGURATION, rawLimit, 1)

    def getCurrentLimit(self):
        # 读取 OCP 寄存器并换算为 mA
        ocp = bytearray(1)
        ocp_mv = memoryview(ocp)
        self.readRegister(SX126X_REG_OCP_CONFIGURATION, ocp_mv, 1)

        return float(ocp[0]) * 2.5

    def setPreambleLength(self, preambleLength):
        # 根据调制模式设置前导码长度
        modem = self.getPacketType()
        if modem == SX126X_PACKET_TYPE_LORA:
            self._preambleLength = preambleLength
            return self.setPacketParams(self._preambleLength, self._crcType, self._implicitLen, self._headerType, self._invertIQ)
        elif modem == SX126X_PACKET_TYPE_GFSK:
            self._preambleLengthFSK = preambleLength
            return self.setPacketParamsFSK(
                self._preambleLengthFSK,
                self._crcTypeFSK,
                self._syncWordLength,
                self._addrComp,
                self._whitening,
                self._packetType,
                self._packetLength,
                self._preambleDetectorLength,
            )

        return ERR_UNKNOWN

    def setFrequencyDeviation(self, freqDev):
        # 仅 GFSK 模式支持
        if self.getPacketType() != SX126X_PACKET_TYPE_GFSK:
            return ERR_WRONG_MODEM

        # 校验频偏范围
        if not (freqDev <= 200.0):
            return ERR_INVALID_FREQUENCY_DEVIATION

        # 频偏 → 原始寄存器值
        freqDevRaw = int(((freqDev * 1000.0) * float(1 << 25)) / (SX126X_CRYSTAL_FREQ * 1000000.0))

        self._freqDev = freqDevRaw
        return self.setModulationParamsFSK(self._br, self._pulseShape, self._rxBw, self._freqDev)

    def setBitRate(self, br):
        # 仅 GFSK 模式支持
        if self.getPacketType() != SX126X_PACKET_TYPE_GFSK:
            return ERR_WRONG_MODEM

        # 校验比特率范围（0.6 ~ 300 kbps）
        if not ((br >= 0.6) and (br <= 300.0)):
            return ERR_INVALID_BIT_RATE

        # 比特率 → 原始寄存器值
        brRaw = int((SX126X_CRYSTAL_FREQ * 1000000.0 * 32.0) / (br * 1000.0))

        self._br = brRaw

        return self.setModulationParamsFSK(self._br, self._pulseShape, self._rxBw, self._freqDev)

    def setRxBandwidth(self, rxBw):
        # 仅 GFSK 模式支持
        if self.getPacketType() != SX126X_PACKET_TYPE_GFSK:
            return ERR_WRONG_MODEM

        self._rxBwKhz = rxBw

        # GFSK 接收带宽映射（浮点容差比较）
        if abs(rxBw - 4.8) <= 0.001:
            self._rxBw = SX126X_GFSK_RX_BW_4_8
        elif abs(rxBw - 5.8) <= 0.001:
            self._rxBw = SX126X_GFSK_RX_BW_5_8
        elif abs(rxBw - 7.3) <= 0.001:
            self._rxBw = SX126X_GFSK_RX_BW_7_3
        elif abs(rxBw - 9.7) <= 0.001:
            self._rxBw = SX126X_GFSK_RX_BW_9_7
        elif abs(rxBw - 11.7) <= 0.001:
            self._rxBw = SX126X_GFSK_RX_BW_11_7
        elif abs(rxBw - 14.6) <= 0.001:
            self._rxBw = SX126X_GFSK_RX_BW_14_6
        elif abs(rxBw - 19.5) <= 0.001:
            self._rxBw = SX126X_GFSK_RX_BW_19_5
        elif abs(rxBw - 23.4) <= 0.001:
            self._rxBw = SX126X_GFSK_RX_BW_23_4
        elif abs(rxBw - 29.3) <= 0.001:
            self._rxBw = SX126X_GFSK_RX_BW_29_3
        elif abs(rxBw - 39.0) <= 0.001:
            self._rxBw = SX126X_GFSK_RX_BW_39_0
        elif abs(rxBw - 46.9) <= 0.001:
            self._rxBw = SX126X_GFSK_RX_BW_46_9
        elif abs(rxBw - 58.6) <= 0.001:
            self._rxBw = SX126X_GFSK_RX_BW_58_6
        elif abs(rxBw - 78.2) <= 0.001:
            self._rxBw = SX126X_GFSK_RX_BW_78_2
        elif abs(rxBw - 93.8) <= 0.001:
            self._rxBw = SX126X_GFSK_RX_BW_93_8
        elif abs(rxBw - 117.3) <= 0.001:
            self._rxBw = SX126X_GFSK_RX_BW_117_3
        elif abs(rxBw - 156.2) <= 0.001:
            self._rxBw = SX126X_GFSK_RX_BW_156_2
        elif abs(rxBw - 187.2) <= 0.001:
            self._rxBw = SX126X_GFSK_RX_BW_187_2
        elif abs(rxBw - 234.3) <= 0.001:
            self._rxBw = SX126X_GFSK_RX_BW_234_3
        elif abs(rxBw - 312.0) <= 0.001:
            self._rxBw = SX126X_GFSK_RX_BW_312_0
        elif abs(rxBw - 373.6) <= 0.001:
            self._rxBw = SX126X_GFSK_RX_BW_373_6
        elif abs(rxBw - 467.0) <= 0.001:
            self._rxBw = SX126X_GFSK_RX_BW_467_0
        else:
            return ERR_INVALID_RX_BANDWIDTH

        return self.setModulationParamsFSK(self._br, self._pulseShape, self._rxBw, self._freqDev)

    def setDataShaping(self, sh):
        # 仅 GFSK 模式支持
        if self.getPacketType() != SX126X_PACKET_TYPE_GFSK:
            return ERR_WRONG_MODEM

        # 高斯滤波器整形映射
        sh *= 10.0
        if abs(sh - 0.0) <= 0.001:
            self._pulseShape = SX126X_GFSK_FILTER_NONE
        elif abs(sh - 3.0) <= 0.001:
            self._pulseShape = SX126X_GFSK_FILTER_GAUSS_0_3
        elif abs(sh - 5.0) <= 0.001:
            self._pulseShape = SX126X_GFSK_FILTER_GAUSS_0_5
        elif abs(sh - 7.0) <= 0.001:
            self._pulseShape = SX126X_GFSK_FILTER_GAUSS_0_7
        elif abs(sh - 10.0) <= 0.001:
            self._pulseShape = SX126X_GFSK_FILTER_GAUSS_1
        else:
            return ERR_INVALID_DATA_SHAPING

        return self.setModulationParamsFSK(self._br, self._pulseShape, self._rxBw, self._freqDev)

    def setSyncBits(self, syncWord, bitsLen):
        # 仅 GFSK 模式支持
        if self.getPacketType() != SX126X_PACKET_TYPE_GFSK:
            return ERR_WRONG_MODEM

        # 校验同步字比特长度
        if bitsLen > 0x40:
            return ERR_INVALID_SYNC_WORD

        # 比特 → 字节（向上取整）
        bytesLen = int(bitsLen / 8)
        if (bitsLen % 8) != 0:
            bytesLen += 1

        # 写入同步字
        state = self.writeRegister(SX126X_REG_SYNC_WORD_0, syncWord, bytesLen)
        ASSERT(state)

        self._syncWordLength = bitsLen
        state = self.setPacketParamsFSK(
            self._preambleLengthFSK,
            self._crcTypeFSK,
            self._syncWordLength,
            self._addrComp,
            self._whitening,
            self._packetType,
            self._packetLength,
            self._preambleDetectorLength,
        )

        return state

    def setNodeAddress(self, nodeAddr):
        # 仅 GFSK 模式支持
        if self.getPacketType() != SX126X_PACKET_TYPE_GFSK:
            return ERR_WRONG_MODEM

        # 设置节点地址过滤模式
        self._addrComp = SX126X_GFSK_ADDRESS_FILT_NODE

        state = self.setPacketParamsFSK(
            self._preambleLengthFSK,
            self._crcTypeFSK,
            self._syncWordLength,
            self._addrComp,
            self._whitening,
            self._packetType,
            self._packetLength,
            self._preambleDetectorLength,
        )
        ASSERT(state)

        # 写入节点地址
        state = self.writeRegister(SX126X_REG_NODE_ADDRESS, [nodeAddr], 1)

        return state

    def setBroadcastAddress(self, broadAddr):
        # 仅 GFSK 模式支持
        if self.getPacketType() != SX126X_PACKET_TYPE_GFSK:
            return ERR_WRONG_MODEM

        # 设置广播地址过滤模式
        self._addrComp = SX126X_GFSK_ADDRESS_FILT_NODE_BROADCAST
        state = self.setPacketParamsFSK(
            self._preambleLengthFSK,
            self._crcTypeFSK,
            self._syncWordLength,
            self._addrComp,
            self._whitening,
            self._packetType,
            self._packetLength,
            self._preambleDetectorLength,
        )
        ASSERT(state)

        # 写入广播地址
        state = self.writeRegister(SX126X_REG_BROADCAST_ADDRESS, [broadAddr], 1)

        return state

    def disableAddressFiltering(self):
        # 仅 GFSK 模式支持
        if self.getPacketType() != SX126X_PACKET_TYPE_GFSK:
            return ERR_WRONG_MODEM

        # 关闭地址过滤
        self._addrComp = SX126X_GFSK_ADDRESS_FILT_OFF
        return self.setPacketParamsFSK(
            self._preambleLengthFSK,
            self._crcTypeFSK,
            self._syncWordLength,
            self._addrComp,
            self._whitening,
            self._packetType,
            self._packetLength,
            self._preambleDetectorLength,
        )

    def setCRC(self, len_, initial=0x1D0F, polynomial=0x1021, inverted=True):
        modem = self.getPacketType()

        # GFSK 模式 CRC 配置
        if modem == SX126X_PACKET_TYPE_GFSK:
            if len_ == 0:
                self._crcTypeFSK = SX126X_GFSK_CRC_OFF
            elif len_ == 1:
                if inverted:
                    self._crcTypeFSK = SX126X_GFSK_CRC_1_BYTE_INV
                else:
                    self._crcTypeFSK = SX126X_GFSK_CRC_1_BYTE
            elif len_ == 2:
                if inverted:
                    self._crcTypeFSK = SX126X_GFSK_CRC_2_BYTE_INV
                else:
                    self._crcTypeFSK = SX126X_GFSK_CRC_2_BYTE
            else:
                return ERR_INVALID_CRC_CONFIGURATION

            state = self.setPacketParamsFSK(
                self._preambleLengthFSK,
                self._crcTypeFSK,
                self._syncWordLength,
                self._addrComp,
                self._whitening,
                self._packetType,
                self._packetLength,
                self._preambleDetectorLength,
            )
            ASSERT(state)

            # 写入 CRC 初始值
            data = [int((initial >> 8) & 0xFF), int(initial & 0xFF)]
            state = self.writeRegister(SX126X_REG_CRC_INITIAL_MSB, data, 2)
            ASSERT(state)

            # 写入 CRC 多项式
            data[0] = int((polynomial >> 8) & 0xFF)
            data[1] = int(polynomial & 0xFF)
            state = self.writeRegister(SX126X_REG_CRC_POLYNOMIAL_MSB, data, 2)

            return state

        # LoRa 模式 CRC 配置（仅开/关）
        elif modem == SX126X_PACKET_TYPE_LORA:

            if len_:
                self._crcType = SX126X_LORA_CRC_ON
            else:
                self._crcType = SX126X_LORA_CRC_OFF

            return self.setPacketParams(self._preambleLength, self._crcType, self._implicitLen, self._headerType, self._invertIQ)

        return ERR_UNKNOWN

    def setWhitening(self, enabled, initial=0x0100):
        # 仅 GFSK 模式支持
        if self.getPacketType() != SX126X_PACKET_TYPE_GFSK:
            return ERR_WRONG_MODEM

        state = ERR_NONE
        if enabled != True:
            # 关闭白化
            self._whitening = SX126X_GFSK_WHITENING_OFF

            state = self.setPacketParamsFSK(
                self._preambleLengthFSK,
                self._crcTypeFSK,
                self._syncWordLength,
                self._addrComp,
                self._whitening,
                self._packetType,
                self._packetLength,
                self._preambleDetectorLength,
            )
            ASSERT(state)
        else:
            # 开启白化，配置初始值
            self._whitening = SX126X_GFSK_WHITENING_ON

            data = bytearray(1)
            data_mv = memoryview(data)
            state = self.readRegister(SX126X_REG_WHITENING_INITIAL_MSB, data_mv, 1)
            ASSERT(state)
            data2 = [(data[0] & 0xFE) | int((initial >> 8) & 0x01), int(initial & 0xFF)]
            state = self.writeRegister(SX126X_REG_WHITENING_INITIAL_MSB, data2, 2)
            ASSERT(state)

            state = self.setPacketParamsFSK(
                self._preambleLengthFSK,
                self._crcTypeFSK,
                self._syncWordLength,
                self._addrComp,
                self._whitening,
                self._packetType,
                self._packetLength,
                self._preambleDetectorLength,
            )
            ASSERT(state)
        return state

    def getDataRate(self):
        # 返回最近一次传输的数据速率
        return self._dataRate

    def getRSSI(self):
        # 读取包状态中的 RSSI 值并换算为 dBm
        packetStatus = self.getPacketStatus()
        rssiPkt = int(packetStatus & 0xFF)
        return -1.0 * rssiPkt / 2.0

    def getSNR(self):
        # 仅 LoRa 模式支持
        if self.getPacketType() != SX126X_PACKET_TYPE_LORA:
            return ERR_WRONG_MODEM

        # 读取包状态中的 SNR 值
        packetStatus = self.getPacketStatus()
        snrPkt = int((packetStatus >> 8) & 0xFF)
        if snrPkt < 128:
            return snrPkt / 4.0
        else:
            return (snrPkt - 256) / 4.0

    def getPacketLength(self, update=True):
        # 查询接收缓冲区状态获取包长度
        rxBufStatus = bytearray(2)
        rxBufStatus_mv = memoryview(rxBufStatus)
        self.SPIreadCommand([SX126X_CMD_GET_RX_BUFFER_STATUS], 1, rxBufStatus_mv, 2)
        return rxBufStatus[0]

    def fixedPacketLengthMode(self, len_=SX126X_MAX_PACKET_LENGTH):
        # 切换到固定包长模式
        return self.setPacketMode(SX126X_GFSK_PACKET_FIXED, len_)

    def variablePacketLengthMode(self, maxLen=SX126X_MAX_PACKET_LENGTH):
        # 切换到可变包长模式
        return self.setPacketMode(SX126X_GFSK_PACKET_VARIABLE, maxLen)

    def getTimeOnAir(self, len_):
        # 计算空中传输时间（us）
        if self.getPacketType() == SX126X_PACKET_TYPE_LORA:
            # LoRa 空中时间计算
            symbolLength_us = int(((1000 * 10) << self._sf) / (self._bwKhz * 10))
            sfCoeff1_x4 = 17
            sfCoeff2 = 8
            if self._sf == 5 or self._sf == 6:
                sfCoeff1_x4 = 25
                sfCoeff2 = 0
            sfDivisor = 4 * self._sf
            if symbolLength_us >= 16000:
                sfDivisor = 4 * (self._sf - 2)
            bitsPerCrc = 16
            N_symbol_header = 20 if self._headerType == SX126X_LORA_HEADER_EXPLICIT else 0

            bitCount = int(8 * len_ + self._crcType * bitsPerCrc - 4 * self._sf + sfCoeff2 + N_symbol_header)
            if bitCount < 0:
                bitCount = 0

            nPreCodedSymbols = int((bitCount + (sfDivisor - 1)) / sfDivisor)

            nSymbol_x4 = int((self._preambleLength + 8) * 4 + sfCoeff1_x4 + nPreCodedSymbols * (self._cr + 4) * 4)

            return int((symbolLength_us * nSymbol_x4) / 4)
        else:
            # GFSK 空中时间计算
            return int((len_ * 8 * self._br) / (SX126X_CRYSTAL_FREQ * 32))

    def implicitHeader(self, len_):
        # 切换到隐式报头模式
        return self.setHeaderType(SX126X_LORA_HEADER_IMPLICIT, len_)

    def explicitHeader(self):
        # 切换到显式报头模式
        return self.setHeaderType(SX126X_LORA_HEADER_EXPLICIT)

    def setRegulatorLDO(self):
        # 选择 LDO 稳压器
        return self.setRegulatorMode(SX126X_REGULATOR_LDO)

    def setRegulatorDCDC(self):
        # 选择 DCDC 稳压器
        return self.setRegulatorMode(SX126X_REGULATOR_DC_DC)

    def setEncoding(self, encoding):
        # 兼容别名：设置白化
        return self.setWhitening(encoding)

    def forceLDRO(self, enable):
        # 强制设置低数据率优化
        if self.getPacketType() != SX126X_PACKET_TYPE_LORA:
            return ERR_WRONG_MODEM

        self._ldroAuto = False
        self._ldro = enable
        return self.setModulationParams(self._sf, self._bw, self._cr, self._ldro)

    def autoLDRO(self):
        # 自动低数据率优化
        if self.getPacketType() != SX126X_PACKET_TYPE_LORA:
            return ERR_WRONG_MODEM

        self._ldroAuto = True
        return self.setModulationParams(self._sf, self._bw, self._cr, self._ldro)

    def setTCXO(self, voltage, delay=5000):
        # 进入待机模式
        self.standby()

        # 检查并清除晶振启动错误
        if self.getDeviceErrors() & SX126X_XOSC_START_ERR:
            self.clearDeviceErrors()

        # 电压为 0 则复位（无 TCXO）
        if abs(voltage - 0.0) <= 0.001:
            return self.reset()

        # TCXO 电压映射
        data = [0, 0, 0, 0]
        if abs(voltage - 1.6) <= 0.001:
            data[0] = SX126X_DIO3_OUTPUT_1_6
        elif abs(voltage - 1.7) <= 0.001:
            data[0] = SX126X_DIO3_OUTPUT_1_7
        elif abs(voltage - 1.8) <= 0.001:
            data[0] = SX126X_DIO3_OUTPUT_1_8
        elif abs(voltage - 2.2) <= 0.001:
            data[0] = SX126X_DIO3_OUTPUT_2_2
        elif abs(voltage - 2.4) <= 0.001:
            data[0] = SX126X_DIO3_OUTPUT_2_4
        elif abs(voltage - 2.7) <= 0.001:
            data[0] = SX126X_DIO3_OUTPUT_2_7
        elif abs(voltage - 3.0) <= 0.001:
            data[0] = SX126X_DIO3_OUTPUT_3_0
        elif abs(voltage - 3.3) <= 0.001:
            data[0] = SX126X_DIO3_OUTPUT_3_3
        else:
            return ERR_INVALID_TCXO_VOLTAGE

        # TCXO 延时（15.625us 为单位）
        delayValue = int(float(delay) / 15.625)
        data[1] = int((delayValue >> 16) & 0xFF)
        data[2] = int((delayValue >> 8) & 0xFF)
        data[3] = int(delayValue & 0xFF)

        self._tcxoDelay = delay

        return self.SPIwriteCommand([SX126X_CMD_SET_DIO3_AS_TCXO_CTRL], 1, data, 4)

    def setDio2AsRfSwitch(self, enable=True):
        # 配置 DIO2 为射频开关或 IRQ
        data = [0]
        if enable:
            data = [SX126X_DIO2_AS_RF_SWITCH]
        else:
            data = [SX126X_DIO2_AS_IRQ]
        return self.SPIwriteCommand([SX126X_CMD_SET_DIO2_AS_RF_SWITCH_CTRL], 1, data, 1)

    def setTx(self, timeout=0):
        # 启动发射
        data = [int((timeout >> 16) & 0xFF), int((timeout >> 8) & 0xFF), int(timeout & 0xFF)]
        return self.SPIwriteCommand([SX126X_CMD_SET_TX], 1, data, 3)

    def setRx(self, timeout):
        # 启动接收
        data = [int((timeout >> 16) & 0xFF), int((timeout >> 8) & 0xFF), int(timeout & 0xFF)]
        return self.SPIwriteCommand([SX126X_CMD_SET_RX], 1, data, 3)

    def setCad(self):
        # 启动信道活动检测
        return self.SPIwriteCommand([SX126X_CMD_SET_CAD], 1, [], 0)

    def setPaConfig(self, paDutyCycle, deviceSel, hpMax=SX126X_PA_CONFIG_HP_MAX, paLut=SX126X_PA_CONFIG_PA_LUT):
        # 配置功率放大器
        data = [paDutyCycle, hpMax, deviceSel, paLut]
        return self.SPIwriteCommand([SX126X_CMD_SET_PA_CONFIG], 1, data, 4)

    def writeRegister(self, addr, data, numBytes):
        # SPI 写寄存器命令
        cmd = [SX126X_CMD_WRITE_REGISTER, int((addr >> 8) & 0xFF), int(addr & 0xFF)]
        state = self.SPIwriteCommand(cmd, 3, data, numBytes)
        return state

    def readRegister(self, addr, data, numBytes):
        # SPI 读寄存器命令
        cmd = [SX126X_CMD_READ_REGISTER, int((addr >> 8) & 0xFF), int(addr & 0xFF)]
        return self.SPItransfer(cmd, 3, False, [], data, numBytes, True)

    def writeBuffer(self, data, numBytes, offset=0x00):
        # SPI 写缓冲区命令
        cmd = [SX126X_CMD_WRITE_BUFFER, offset]
        state = self.SPIwriteCommand(cmd, 2, data, numBytes)

        return state

    def readBuffer(self, data, numBytes):
        # SPI 读缓冲区命令
        cmd = [SX126X_CMD_READ_BUFFER, SX126X_CMD_NOP]
        state = self.SPIreadCommand(cmd, 2, data, numBytes)

        return state

    def setDioIrqParams(self, irqMask, dio1Mask, dio2Mask=SX126X_IRQ_NONE, dio3Mask=SX126X_IRQ_NONE):
        # 配置 DIO 中断参数
        data = [
            int((irqMask >> 8) & 0xFF),
            int(irqMask & 0xFF),
            int((dio1Mask >> 8) & 0xFF),
            int(dio1Mask & 0xFF),
            int((dio2Mask >> 8) & 0xFF),
            int(dio2Mask & 0xFF),
            int((dio3Mask >> 8) & 0xFF),
            int(dio3Mask & 0xFF),
        ]
        return self.SPIwriteCommand([SX126X_CMD_SET_DIO_IRQ_PARAMS], 1, data, 8)

    def getIrqStatus(self):
        # 读取 IRQ 状态
        data = bytearray(2)
        data_mv = memoryview(data)
        self.SPIreadCommand([SX126X_CMD_GET_IRQ_STATUS], 1, data_mv, 2)
        return int((data[0] << 8) | data[1])

    def clearIrqStatus(self, clearIrqParams=SX126X_IRQ_ALL):
        # 清除 IRQ 标志
        data = [int((clearIrqParams >> 8) & 0xFF), int(clearIrqParams & 0xFF)]
        return self.SPIwriteCommand([SX126X_CMD_CLEAR_IRQ_STATUS], 1, data, 2)

    def setRfFrequency(self, frf):
        # 设置射频频率原始值
        data = [int((frf >> 24) & 0xFF), int((frf >> 16) & 0xFF), int((frf >> 8) & 0xFF), int(frf & 0xFF)]
        return self.SPIwriteCommand([SX126X_CMD_SET_RF_FREQUENCY], 1, data, 4)

    def calibrateImage(self, data):
        # 执行镜像校准
        return self.SPIwriteCommand([SX126X_CMD_CALIBRATE_IMAGE], 1, data, 2)

    def getPacketType(self):
        # 查询当前包类型（LoRa / GFSK）
        data = bytearray([0xFF])
        data_mv = memoryview(data)
        self.SPIreadCommand([SX126X_CMD_GET_PACKET_TYPE], 1, data_mv, 1)
        return data[0]

    def setTxParams(self, power, rampTime=SX126X_PA_RAMP_200U):
        # 处理负功率（补码转换）
        if power < 0:
            power += 256
        data = [power, rampTime]
        return self.SPIwriteCommand([SX126X_CMD_SET_TX_PARAMS], 1, data, 2)

    def setPacketMode(self, mode, len_):
        # 仅 GFSK 模式支持
        if self.getPacketType() != SX126X_PACKET_TYPE_GFSK:
            return ERR_WRONG_MODEM

        # 更新包模式和长度
        state = self.setPacketParamsFSK(
            self._preambleLengthFSK, self._crcTypeFSK, self._syncWordLength, self._addrComp, self._whitening, mode, len_, self._preambleDetectorLength
        )
        ASSERT(state)

        self._packetType = mode
        self._packetLength = len_
        return state

    def setHeaderType(self, headerType, len_=0xFF):
        # 仅 LoRa 模式支持
        if self.getPacketType() != SX126X_PACKET_TYPE_LORA:
            return ERR_WRONG_MODEM

        # 更新报头类型
        state = self.setPacketParams(self._preambleLength, self._crcType, len_, headerType, self._invertIQ)
        ASSERT(state)

        self._headerType = headerType
        self._implicitLen = len_

        return state

    def setModulationParams(self, sf, bw, cr, ldro):
        # LoRa 调制参数，自动 LDRO 判断
        if self._ldroAuto:
            # 符号长度 >= 16ms 时自动开启 LDRO
            symbolLength = float((1 << self._sf)) / float(self._bwKhz)
            if symbolLength >= 16.0:
                self._ldro = SX126X_LORA_LOW_DATA_RATE_OPTIMIZE_ON
            else:
                self._ldro = SX126X_LORA_LOW_DATA_RATE_OPTIMIZE_OFF
        else:
            self._ldro = ldro

        data = [sf, bw, cr, self._ldro]
        return self.SPIwriteCommand([SX126X_CMD_SET_MODULATION_PARAMS], 1, data, 4)

    def setModulationParamsFSK(self, br, pulseShape, rxBw, freqDev):
        # GFSK 调制参数
        data = [
            int((br >> 16) & 0xFF),
            int((br >> 8) & 0xFF),
            int(br & 0xFF),
            pulseShape,
            rxBw,
            int((freqDev >> 16) & 0xFF),
            int((freqDev >> 8) & 0xFF),
            int(freqDev & 0xFF),
        ]
        return self.SPIwriteCommand([SX126X_CMD_SET_MODULATION_PARAMS], 1, data, 8)

    def setPacketParams(self, preambleLength, crcType, payloadLength, headerType, invertIQ=SX126X_LORA_IQ_STANDARD):
        # LoRa 包参数
        state = self.fixInvertedIQ(invertIQ)
        ASSERT(state)
        data = [int((preambleLength >> 8) & 0xFF), int(preambleLength & 0xFF), headerType, payloadLength, crcType, invertIQ]
        return self.SPIwriteCommand([SX126X_CMD_SET_PACKET_PARAMS], 1, data, 6)

    def setPacketParamsFSK(
        self,
        preambleLength,
        crcType,
        syncWordLength,
        addrComp,
        whitening,
        packetType=SX126X_GFSK_PACKET_VARIABLE,
        payloadLength=0xFF,
        preambleDetectorLength=SX126X_GFSK_PREAMBLE_DETECT_16,
    ):
        # GFSK 包参数
        data = [
            int((preambleLength >> 8) & 0xFF),
            int(preambleLength & 0xFF),
            preambleDetectorLength,
            syncWordLength,
            addrComp,
            packetType,
            payloadLength,
            crcType,
            whitening,
        ]
        return self.SPIwriteCommand([SX126X_CMD_SET_PACKET_PARAMS], 1, data, 9)

    def setBufferBaseAddress(self, txBaseAddress=0x00, rxBaseAddress=0x00):
        # 设置 TX/RX 缓冲区基地址
        data = [txBaseAddress, rxBaseAddress]
        return self.SPIwriteCommand([SX126X_CMD_SET_BUFFER_BASE_ADDRESS], 1, data, 2)

    def setRegulatorMode(self, mode):
        # 设置稳压器模式
        data = [mode]
        return self.SPIwriteCommand([SX126X_CMD_SET_REGULATOR_MODE], 1, data, 1)

    def getStatus(self):
        # 查询芯片状态
        data = bytearray(1)
        data_mv = memoryview(data)
        self.SPIreadCommand([SX126X_CMD_GET_STATUS], 1, data_mv, 1)
        return data[0]

    def getPacketStatus(self):
        # 查询包状态
        data = bytearray(3)
        data_mv = memoryview(data)
        self.SPIreadCommand([SX126X_CMD_GET_PACKET_STATUS], 1, data_mv, 3)
        return (data[0] << 16) | (data[1] << 8) | data[2]

    def getDeviceErrors(self):
        # 查询设备错误
        data = bytearray(2)
        data_mv = memoryview(data)
        self.SPIreadCommand([SX126X_CMD_GET_DEVICE_ERRORS], 1, data_mv, 2)
        opError = (data[0] << 8) | data[1]
        return opError

    def clearDeviceErrors(self):
        # 清除设备错误
        data = [SX126X_CMD_NOP, SX126X_CMD_NOP]
        return self.SPIwriteCommand([SX126X_CMD_CLEAR_DEVICE_ERRORS], 1, data, 2)

    def setFrequencyRaw(self, freq):
        # 将 MHz 频率转换为射频寄存器值
        frf = int((freq * (1 << SX126X_DIV_EXPONENT)) / SX126X_CRYSTAL_FREQ)
        return self.setRfFrequency(frf)

    def fixSensitivity(self):
        # 修复灵敏度配置（500kHz 带宽特殊处理）
        sensitivityConfig = bytearray(1)
        sensitivityConfig_mv = memoryview(sensitivityConfig)
        state = self.readRegister(SX126X_REG_SENSITIVITY_CONFIG, sensitivityConfig_mv, 1)
        ASSERT(state)

        if self.getPacketType() == SX126X_PACKET_TYPE_LORA and abs(self._bwKhz - 500.0) <= 0.001:
            sensitivityConfig_mv[0] &= 0xFB
        else:
            sensitivityConfig_mv[0] |= 0x04
        return self.writeRegister(SX126X_REG_SENSITIVITY_CONFIG, sensitivityConfig, 1)

    def fixPaClamping(self):
        # 修复 PA 钳位配置
        clampConfig = bytearray(1)
        clampConfig_mv = memoryview(clampConfig)
        state = self.readRegister(SX126X_REG_TX_CLAMP_CONFIG, clampConfig_mv, 1)
        ASSERT(state)

        clampConfig_mv[0] |= 0x1E
        return self.writeRegister(SX126X_REG_TX_CLAMP_CONFIG, clampConfig, 1)

    def fixImplicitTimeout(self):
        # 修复隐式报头模式下的超时处理
        if not (self._headerType == SX126X_LORA_HEADER_IMPLICIT and self.getPacketType() == SX126X_PACKET_TYPE_LORA):
            return ERR_WRONG_MODEM

        # 停止 RTC 并触发放射事件
        rtcStop = [0x00]
        state = self.writeRegister(SX126X_REG_RTC_STOP, rtcStop, 1)
        ASSERT(state)

        rtcEvent = bytearray(1)
        rtcEvent_mv = memoryview(rtcEvent)
        state = self.readRegister(SX126X_REG_RTC_EVENT, rtcEvent_mv, 1)
        ASSERT(state)

        rtcEvent_mv[0] |= 0x02
        return self.writeRegister(SX126X_REG_RTC_EVENT, rtcEvent, 1)

    def fixInvertedIQ(self, iqConfig):
        # 修复反转 IQ 配置
        iqConfigCurrent = bytearray(1)
        iqConfigCurrent_mv = memoryview(iqConfigCurrent)
        state = self.readRegister(SX126X_REG_IQ_CONFIG, iqConfigCurrent_mv, 1)
        ASSERT(state)

        if iqConfig == SX126X_LORA_IQ_STANDARD:
            iqConfigCurrent_mv[0] &= 0xFB
        else:
            iqConfigCurrent_mv[0] |= 0x04

        return self.writeRegister(SX126X_REG_IQ_CONFIG, iqConfigCurrent, 1)

    def config(self, modem):
        # 芯片初始化配置：设置调制模式、回退模式、CAD 参数、校准
        state = self.setBufferBaseAddress()
        ASSERT(state)

        # 设置包类型（LoRa / GFSK）
        data = [0, 0, 0, 0, 0, 0, 0]
        data[0] = modem
        state = self.SPIwriteCommand([SX126X_CMD_SET_PACKET_TYPE], 1, data, 1)
        ASSERT(state)

        # 设置回退模式
        data[0] = SX126X_RX_TX_FALLBACK_MODE_STDBY_RC
        state = self.SPIwriteCommand([SX126X_CMD_SET_RX_TX_FALLBACK_MODE], 1, data, 1)
        ASSERT(state)

        # 设置 CAD 参数
        data[0] = SX126X_CAD_ON_8_SYMB
        data[1] = self._sf + 13
        data[2] = 10
        data[3] = SX126X_CAD_GOTO_STDBY
        data[4] = 0x00
        data[5] = 0x00
        data[6] = 0x00
        state = self.SPIwriteCommand([SX126X_CMD_SET_CAD_PARAMS], 1, data, 7)
        ASSERT(state)

        # 清除中断并配置 DIO
        state = self.clearIrqStatus()
        state |= self.setDioIrqParams(SX126X_IRQ_NONE, SX126X_IRQ_NONE)
        ASSERT(state)

        # 执行全校准
        data[0] = SX126X_CALIBRATE_ALL
        state = self.SPIwriteCommand([SX126X_CMD_CALIBRATE], 1, data, 1)
        ASSERT(state)

        sleep_ms(5)

        # 等待 GPIO 就绪
        if implementation.name == "micropython":
            while self.gpio.value():
                yield_()

        if implementation.name == "circuitpython":
            while self.gpio.value:
                yield_()

        return ERR_NONE

    def SPIwriteCommand(self, cmd, cmdLen, data, numBytes, waitForBusy=True):
        # SPI 写命令封装
        return self.SPItransfer(cmd, cmdLen, True, data, [], numBytes, waitForBusy)

    def SPIreadCommand(self, cmd, cmdLen, data, numBytes, waitForBusy=True):
        # SPI 读命令封装
        return self.SPItransfer(cmd, cmdLen, False, [], data, numBytes, waitForBusy)

    def SPItransfer(self, cmd, cmdLen, write, dataOut, dataIn, numBytes, waitForBusy, timeout=5000):
        # MicroPython SPI 传输
        if implementation.name == "micropython":
            # 拉低 CS 选中芯片
            self.cs.value(0)

            # 等待 GPIO 就绪（忙标志清除）
            start = ticks_ms()
            while self.gpio.value():
                yield_()
                if abs(ticks_diff(start, ticks_ms())) >= timeout:
                    self.cs.value(1)
                    return ERR_SPI_CMD_TIMEOUT

            # 发送命令字节
            for i in range(cmdLen):
                self.spi.write(bytes([cmd[i]]))

        # CircuitPython SPI 传输
        if implementation.name == "circuitpython":
            while not self.spi.try_lock():
                pass
            self.cs.value = False

            start = ticks_ms()
            while self.gpio.value:
                yield_()
                if abs(ticks_diff(start, ticks_ms())) >= timeout:
                    self.cs.value = True
                    self.spi.unlock()
                    return ERR_SPI_CMD_TIMEOUT

            for i in range(cmdLen):
                self.spi.write(bytes([cmd[i]]))

            in_ = bytearray(1)

        status = 0

        # 数据写入/读取阶段
        if write:
            for i in range(numBytes):
                if implementation.name == "micropython":
                    try:
                        in_ = self.spi.read(1, dataOut[i])
                    except:
                        in_ = self.spi.read(1, write=dataOut[i])

                if implementation.name == "circuitpython":
                    self.spi.write_readinto(bytes([dataOut[i]]), in_)

                # 检查状态字节
                if (
                    (in_[0] & 0b00001110) == SX126X_STATUS_CMD_TIMEOUT
                    or (in_[0] & 0b00001110) == SX126X_STATUS_CMD_INVALID
                    or (in_[0] & 0b00001110) == SX126X_STATUS_CMD_FAILED
                ):
                    status = in_[0] & 0b00001110
                    break
                elif (in_[0] == 0x00) or (in_[0] == 0xFF):
                    status = SX126X_STATUS_SPI_FAILED
                    break
        else:
            # 读取模式：发送 NOP 触发读取
            if implementation.name == "micropython":
                try:
                    in_ = self.spi.read(1, SX126X_CMD_NOP)
                except:
                    in_ = self.spi.read(1, write=SX126X_CMD_NOP)

            if implementation.name == "circuitpython":
                self.spi.readinto(in_)

            # 检查状态字节
            if (
                (in_[0] & 0b00001110) == SX126X_STATUS_CMD_TIMEOUT
                or (in_[0] & 0b00001110) == SX126X_STATUS_CMD_INVALID
                or (in_[0] & 0b00001110) == SX126X_STATUS_CMD_FAILED
            ):
                status = in_[0] & 0b00001110
            elif (in_[0] == 0x00) or (in_[0] == 0xFF):
                status = SX126X_STATUS_SPI_FAILED
            else:
                # 读取数据字节
                if implementation.name == "micropython":
                    for i in range(numBytes):
                        try:
                            dataIn[i] = self.spi.read(1, SX126X_CMD_NOP)[0]
                        except:
                            dataIn[i] = self.spi.read(1, write=SX126X_CMD_NOP)[0]

                if implementation.name == "circuitpython":
                    for i in range(numBytes):
                        self.spi.readinto(in_)
                        dataIn[i] = in_[0]

        # 拉高 CS 释放总线
        if implementation.name == "micropython":
            self.cs.value(1)

        if implementation.name == "circuitpython":
            self.cs.value = True
            self.spi.unlock()

        # 等待忙碌标志清除
        if waitForBusy:
            sleep_us(1)
            start = ticks_ms()
            if implementation.name == "micropython":
                while self.gpio.value():
                    yield_()
                    if abs(ticks_diff(start, ticks_ms())) >= timeout:
                        status = SX126X_STATUS_CMD_TIMEOUT
                        break

            if implementation.name == "circuitpython":
                while self.gpio.value:
                    yield_()
                    if abs(ticks_diff(start, ticks_ms())) >= timeout:
                        status = SX126X_STATUS_CMD_TIMEOUT
                        break

        # 状态码映射
        switch = {
            SX126X_STATUS_CMD_TIMEOUT: ERR_SPI_CMD_TIMEOUT,
            SX126X_STATUS_CMD_INVALID: ERR_SPI_CMD_INVALID,
            SX126X_STATUS_CMD_FAILED: ERR_SPI_CMD_FAILED,
            SX126X_STATUS_SPI_FAILED: ERR_CHIP_NOT_FOUND,
        }
        try:
            return switch[status]
        except:
            return ERR_NONE
