"""Explicit async adapters for bounded AXP2101 I2C transactions."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from axp2101 import *


class SyncAdapterMixin:
    """Expose explicit async entry points without hiding I2C blocking."""

    async def deinit(self):
        """Awaitable source lifecycle API; calls the next MRO implementation."""
        return super().deinit()

    async def aclose(self):
        await self.deinit()


class AXP2101Async(SyncAdapterMixin, AXP2101):
    """Async facade for bounded source I2C transactions."""

    async def aclose(self):
        """Explicitly expose the source deinit() mapping on this facade."""
        await super().aclose()

    async def isVbusGood_async(self):
        return super().isVbusGood()

    async def getBatfetState_async(self):
        return super().getBatfetState()

    async def isBatteryConnect_async(self):
        return super().isBatteryConnect()

    async def isBatInActiveModeState_async(self):
        return super().isBatInActiveModeState()

    async def getThermalRegulationStatus_async(self):
        return super().getThermalRegulationStatus()

    async def getCurrentLimitStatus_async(self):
        return super().getCurrentLimitStatus()

    async def isCharging_async(self):
        return super().isCharging()

    async def isDischarge_async(self):
        return super().isDischarge()

    async def isStandby_async(self):
        return super().isStandby()

    async def isPowerOn_async(self):
        return super().isPowerOn()

    async def isPowerOff_async(self):
        return super().isPowerOff()

    async def isVbusIn_async(self):
        return super().isVbusIn()

    async def getChargerStatus_async(self):
        return super().getChargerStatus()

    async def writeDataBuffer_async(self, data: list, size: int):
        return super().writeDataBuffer(data, size)

    async def readDataBuffer_async(self, size: int):
        return super().readDataBuffer(size)

    async def enableInternalDischarge_async(self):
        return super().enableInternalDischarge()

    async def disableInternalDischarge_async(self):
        return super().disableInternalDischarge()

    async def enablePwrOkPinPullLow_async(self):
        return super().enablePwrOkPinPullLow()

    async def disablePwrOkPinPullLow_async(self):
        return super().disablePwrOkPinPullLow()

    async def enablePwronShutPMIC_async(self):
        return super().enablePwronShutPMIC()

    async def disablePwronShutPMIC_async(self):
        return super().disablePwronShutPMIC()

    async def reset_async(self):
        return super().reset()

    async def shutdown_async(self):
        return super().shutdown()

    async def enableBATFET_async(self):
        return super().enableBATFET()

    async def disableBATFET_async(self):
        return super().disableBATFET()

    async def setDieOverTempLevel1_async(self, opt: int):
        return super().setDieOverTempLevel1(opt)

    async def getDieOverTempLevel1_async(self):
        return super().getDieOverTempLevel1()

    async def enableDieOverTempDetect_async(self):
        return super().enableDieOverTempDetect()

    async def disableDieOverTempDetect_async(self):
        return super().disableDieOverTempDetect()

    async def setLinearChargerVsysDpm_async(self, opt: int):
        return super().setLinearChargerVsysDpm(opt)

    async def getLinearChargerVsysDpm_async(self):
        return super().getLinearChargerVsysDpm()

    async def setVbusVoltageLimit_async(self, opt: int):
        return super().setVbusVoltageLimit(opt)

    async def getVbusVoltageLimit_async(self):
        return super().getVbusVoltageLimit()

    async def setVbusCurrentLimit_async(self, opt: int):
        return super().setVbusCurrentLimit(opt)

    async def getVbusCurrentLimit_async(self):
        return super().getVbusCurrentLimit()

    async def enableButtonBatteryCharge_async(self):
        return super().enableButtonBatteryCharge()

    async def disableButtonBatteryCharge_async(self):
        return super().disableButtonBatteryCharge()

    async def isEnableButtonBatteryCharge_async(self):
        return super().isEnableButtonBatteryCharge()

    async def setButtonBatteryChargeVoltage_async(self, millivolt: int):
        return super().setButtonBatteryChargeVoltage(millivolt)

    async def getButtonBatteryVoltage_async(self):
        return super().getButtonBatteryVoltage()

    async def enableCellbatteryCharge_async(self):
        return super().enableCellbatteryCharge()

    async def disableCellbatteryCharge_async(self):
        return super().disableCellbatteryCharge()

    async def enableWatchdog_async(self):
        return super().enableWatchdog()

    async def disableWatchdog_async(self):
        return super().disableWatchdog()

    async def setWatchdogConfig_async(self, opt: int):
        return super().setWatchdogConfig(opt)

    async def getWatchConfig_async(self):
        return super().getWatchConfig()

    async def clrWatchdog_async(self):
        return super().clrWatchdog()

    async def setWatchdogTimeout_async(self, opt: int):
        return super().setWatchdogTimeout(opt)

    async def getWatchdogTimerout_async(self):
        return super().getWatchdogTimerout()

    async def setLowBatWarnThreshold_async(self, opt: int):
        return super().setLowBatWarnThreshold(opt)

    async def getLowBatWarnThreshold_async(self):
        return super().getLowBatWarnThreshold()

    async def setLowBatShutdownThreshold_async(self, opt: int):
        return super().setLowBatShutdownThreshold(opt)

    async def getLowBatShutdownThreshold_async(self):
        return super().getLowBatShutdownThreshold()

    async def isPoweronAlwaysHighSource_async(self):
        return super().isPoweronAlwaysHighSource()

    async def isBattInsertOnSource_async(self):
        return super().isBattInsertOnSource()

    async def isBattNormalOnSource_async(self):
        return super().isBattNormalOnSource()

    async def isVbusInsertOnSource_async(self):
        return super().isVbusInsertOnSource()

    async def isIrqLowOnSource_async(self):
        return super().isIrqLowOnSource()

    async def isPwronLowOnSource_async(self):
        return super().isPwronLowOnSource()

    async def getPowerOnSource_async(self):
        return super().getPowerOnSource()

    async def isOverTemperatureOffSource_async(self):
        return super().isOverTemperatureOffSource()

    async def isDcOverVoltageOffSource_async(self):
        return super().isDcOverVoltageOffSource()

    async def isDcUnderVoltageOffSource_async(self):
        return super().isDcUnderVoltageOffSource()

    async def isVbusOverVoltageOffSource_async(self):
        return super().isVbusOverVoltageOffSource()

    async def isVsysUnderVoltageOffSource_async(self):
        return super().isVsysUnderVoltageOffSource()

    async def isPwronAlwaysLowOffSource_async(self):
        return super().isPwronAlwaysLowOffSource()

    async def isSwConfigOffSource_async(self):
        return super().isSwConfigOffSource()

    async def isPwrSourcePullDown_async(self):
        return super().isPwrSourcePullDown()

    async def getPowerOffSource_async(self):
        return super().getPowerOffSource()

    async def enableOverTemperatureLevel2PowerOff_async(self):
        return super().enableOverTemperatureLevel2PowerOff()

    async def disableOverTemperaturePowerOff_async(self):
        return super().disableOverTemperaturePowerOff()

    async def enableLongPressShutdown_async(self):
        return super().enableLongPressShutdown()

    async def disableLongPressShutdown_async(self):
        return super().disableLongPressShutdown()

    async def setLongPressRestart_async(self):
        return super().setLongPressRestart()

    async def setLongPressPowerOFF_async(self):
        return super().setLongPressPowerOFF()

    async def enableDCHighVoltageTurnOff_async(self):
        return super().enableDCHighVoltageTurnOff()

    async def disableDCHighVoltageTurnOff_async(self):
        return super().disableDCHighVoltageTurnOff()

    async def enableDC5LowVoltageTurnOff_async(self):
        return super().enableDC5LowVoltageTurnOff()

    async def disableDC5LowVoltageTurnOff_async(self):
        return super().disableDC5LowVoltageTurnOff()

    async def enableDC4LowVoltageTurnOff_async(self):
        return super().enableDC4LowVoltageTurnOff()

    async def disableDC4LowVoltageTurnOff_async(self):
        return super().disableDC4LowVoltageTurnOff()

    async def enableDC3LowVoltageTurnOff_async(self):
        return super().enableDC3LowVoltageTurnOff()

    async def disableDC3LowVoltageTurnOff_async(self):
        return super().disableDC3LowVoltageTurnOff()

    async def enableDC2LowVoltageTurnOff_async(self):
        return super().enableDC2LowVoltageTurnOff()

    async def disableDC2LowVoltageTurnOff_async(self):
        return super().disableDC2LowVoltageTurnOff()

    async def enableDC1LowVoltageTurnOff_async(self):
        return super().enableDC1LowVoltageTurnOff()

    async def disableDC1LowVoltageTurnOff_async(self):
        return super().disableDC1LowVoltageTurnOff()

    async def setSysPowerDownVoltage_async(self, millivolt: int):
        return super().setSysPowerDownVoltage(millivolt)

    async def getSysPowerDownVoltage_async(self):
        return super().getSysPowerDownVoltage()

    async def enablePwrOk_async(self):
        return super().enablePwrOk()

    async def disablePwrOk_async(self):
        return super().disablePwrOk()

    async def enablePowerOffDelay_async(self):
        return super().enablePowerOffDelay()

    async def disablePowerOffDelay_async(self):
        return super().disablePowerOffDelay()

    async def enablePowerSequence_async(self):
        return super().enablePowerSequence()

    async def disablePowerSequence_async(self):
        return super().disablePowerSequence()

    async def setPwrOkDelay_async(self, opt: int):
        return super().setPwrOkDelay(opt)

    async def getPwrOkDelay_async(self):
        return super().getPwrOkDelay()

    async def wakeupControl_async(self, opt: int, enable: bool):
        return super().wakeupControl(opt, enable)

    async def enableWakeup_async(self):
        return super().enableWakeup()

    async def disableWakeup_async(self):
        return super().disableWakeup()

    async def enableSleep_async(self):
        return super().enableSleep()

    async def disableSleep_async(self):
        return super().disableSleep()

    async def setIrqLevel_async(self, opt: int):
        return super().setIrqLevel(opt)

    async def setOffLevel_async(self, opt: int):
        return super().setOffLevel(opt)

    async def setOnLevel_async(self, opt: int):
        return super().setOnLevel(opt)

    async def setDc4FastStartSequence_async(self, opt: int):
        return super().setDc4FastStartSequence(opt)

    async def setDc3FastStartSequence_async(self, opt: int):
        return super().setDc3FastStartSequence(opt)

    async def setDc2FastStartSequence_async(self, opt: int):
        return super().setDc2FastStartSequence(opt)

    async def setDc1FastStartSequence_async(self, opt: int):
        return super().setDc1FastStartSequence(opt)

    async def setAldo3FastStartSequence_async(self, opt: int):
        return super().setAldo3FastStartSequence(opt)

    async def setAldo2FastStartSequence_async(self, opt: int):
        return super().setAldo2FastStartSequence(opt)

    async def setAldo1FastStartSequence_async(self, opt: int):
        return super().setAldo1FastStartSequence(opt)

    async def setDc5FastStartSequence_async(self, opt: int):
        return super().setDc5FastStartSequence(opt)

    async def setCpuldoFastStartSequence_async(self, opt: int):
        return super().setCpuldoFastStartSequence(opt)

    async def setBldo2FastStartSequence_async(self, opt: int):
        return super().setBldo2FastStartSequence(opt)

    async def setBldo1FastStartSequence_async(self, opt: int):
        return super().setBldo1FastStartSequence(opt)

    async def setAldo4FastStartSequence_async(self, opt: int):
        return super().setAldo4FastStartSequence(opt)

    async def setDldo2FastStartSequence_async(self, opt: int):
        return super().setDldo2FastStartSequence(opt)

    async def setDldo1FastStartSequence_async(self, opt: int):
        return super().setDldo1FastStartSequence(opt)

    async def setFastPowerOnLevel_async(self, opt, seq_level):
        return super().setFastPowerOnLevel(opt, seq_level)

    async def disableFastPowerOn_async(self, opt: int):
        return super().disableFastPowerOn(opt)

    async def enableFastPowerOnCtrl_async(self):
        return super().enableFastPowerOnCtrl()

    async def disableFastPowerOnCtrl_async(self):
        return super().disableFastPowerOnCtrl()

    async def enableFastWakeup_async(self):
        return super().enableFastWakeup()

    async def disableFastWakeup_async(self):
        return super().disableFastWakeup()

    async def setDCHighVoltagePowerDown_async(self, en: bool):
        return super().setDCHighVoltagePowerDown(en)

    async def getDCHighVoltagePowerDownEn_async(self):
        return super().getDCHighVoltagePowerDownEn()

    async def setDcUVPDebounceTime_async(self, opt: int):
        return super().setDcUVPDebounceTime(opt)

    async def settDC1WorkModeToPwm_async(self, enable: bool):
        return super().settDC1WorkModeToPwm(enable)

    async def settDC2WorkModeToPwm_async(self, enable: bool):
        return super().settDC2WorkModeToPwm(enable)

    async def settDC3WorkModeToPwm_async(self, enable: bool):
        return super().settDC3WorkModeToPwm(enable)

    async def settDC4WorkModeToPwm_async(self, enable: bool):
        return super().settDC4WorkModeToPwm(enable)

    async def setDCFreqSpreadRange_async(self, opt: int):
        return super().setDCFreqSpreadRange(opt)

    async def setDCFreqSpreadRangeEn_async(self, en: bool):
        return super().setDCFreqSpreadRangeEn(en)

    async def isEnableDC1_async(self):
        return super().isEnableDC1()

    async def enableDC1_async(self):
        return super().enableDC1()

    async def disableDC1_async(self):
        return super().disableDC1()

    async def setDC1Voltage_async(self, millivolt: int):
        return super().setDC1Voltage(millivolt)

    async def getDC1Voltage_async(self):
        return super().getDC1Voltage()

    async def setDC1LowVoltagePowerDown_async(self, en):
        return super().setDC1LowVoltagePowerDown(en)

    async def getDC1LowVoltagePowerDownEn_async(self):
        return super().getDC1LowVoltagePowerDownEn()

    async def isEnableDC2_async(self):
        return super().isEnableDC2()

    async def enableDC2_async(self):
        return super().enableDC2()

    async def disableDC2_async(self):
        return super().disableDC2()

    async def setDC2Voltage_async(self, millivolt: int):
        return super().setDC2Voltage(millivolt)

    async def getDC2Voltage_async(self):
        return super().getDC2Voltage()

    async def getDC2WorkMode_async(self):
        return super().getDC2WorkMode()

    async def setDC2LowVoltagePowerDown_async(self, en: bool):
        return super().setDC2LowVoltagePowerDown(en)

    async def getDC2LowVoltagePowerDownEn_async(self):
        return super().getDC2LowVoltagePowerDownEn()

    async def isEnableDC3_async(self):
        return super().isEnableDC3()

    async def enableDC3_async(self):
        return super().enableDC3()

    async def disableDC3_async(self):
        return super().disableDC3()

    async def setDC3Voltage_async(self, millivolt: int):
        return super().setDC3Voltage(millivolt)

    async def getDC3Voltage_async(self):
        return super().getDC3Voltage()

    async def getDC3WorkMode_async(self):
        return super().getDC3WorkMode()

    async def setDC3LowVoltagePowerDown_async(self, en: bool):
        return super().setDC3LowVoltagePowerDown(en)

    async def getDC3LowVoltagePowerDownEn_async(self):
        return super().getDC3LowVoltagePowerDownEn()

    async def isEnableDC4_async(self):
        return super().isEnableDC4()

    async def enableDC4_async(self):
        return super().enableDC4()

    async def disableDC4_async(self):
        return super().disableDC4()

    async def setDC4Voltage_async(self, millivolt: int):
        return super().setDC4Voltage(millivolt)

    async def getDC4Voltage_async(self):
        return super().getDC4Voltage()

    async def setDC4LowVoltagePowerDown_async(self, en: bool):
        return super().setDC4LowVoltagePowerDown(en)

    async def getDC4LowVoltagePowerDownEn_async(self):
        return super().getDC4LowVoltagePowerDownEn()

    async def isEnableDC5_async(self):
        return super().isEnableDC5()

    async def enableDC5_async(self):
        return super().enableDC5()

    async def disableDC5_async(self):
        return super().disableDC5()

    async def setDC5Voltage_async(self, millivolt: int):
        return super().setDC5Voltage(millivolt)

    async def getDC5Voltage_async(self):
        return super().getDC5Voltage()

    async def isDC5FreqCompensationEn_async(self):
        return super().isDC5FreqCompensationEn()

    async def enableDC5FreqCompensation_async(self):
        return super().enableDC5FreqCompensation()

    async def disableFreqCompensation_async(self):
        return super().disableFreqCompensation()

    async def setDC5LowVoltagePowerDown_async(self, en: bool):
        return super().setDC5LowVoltagePowerDown(en)

    async def getDC5LowVoltagePowerDownEn_async(self):
        return super().getDC5LowVoltagePowerDownEn()

    async def isEnableALDO1_async(self):
        return super().isEnableALDO1()

    async def enableALDO1_async(self):
        return super().enableALDO1()

    async def disableALDO1_async(self):
        return super().disableALDO1()

    async def setALDO1Voltage_async(self, millivolt: int):
        return super().setALDO1Voltage(millivolt)

    async def getALDO1Voltage_async(self):
        return super().getALDO1Voltage()

    async def isEnableALDO2_async(self):
        return super().isEnableALDO2()

    async def enableALDO2_async(self):
        return super().enableALDO2()

    async def disableALDO2_async(self):
        return super().disableALDO2()

    async def setALDO2Voltage_async(self, millivolt: int):
        return super().setALDO2Voltage(millivolt)

    async def getALDO2Voltage_async(self):
        return super().getALDO2Voltage()

    async def isEnableALDO3_async(self):
        return super().isEnableALDO3()

    async def enableALDO3_async(self):
        return super().enableALDO3()

    async def disableALDO3_async(self):
        return super().disableALDO3()

    async def setALDO3Voltage_async(self, millivolt: int):
        return super().setALDO3Voltage(millivolt)

    async def getALDO3Voltage_async(self):
        return super().getALDO3Voltage()

    async def isEnableALDO4_async(self):
        return super().isEnableALDO4()

    async def enableALDO4_async(self):
        return super().enableALDO4()

    async def disableALDO4_async(self):
        return super().disableALDO4()

    async def setALDO4Voltage_async(self, millivolt: int):
        return super().setALDO4Voltage(millivolt)

    async def getALDO4Voltage_async(self):
        return super().getALDO4Voltage()

    async def isEnableBLDO1_async(self):
        return super().isEnableBLDO1()

    async def enableBLDO1_async(self):
        return super().enableBLDO1()

    async def disableBLDO1_async(self):
        return super().disableBLDO1()

    async def setBLDO1Voltage_async(self, millivolt: int):
        return super().setBLDO1Voltage(millivolt)

    async def getBLDO1Voltage_async(self):
        return super().getBLDO1Voltage()

    async def isEnableBLDO2_async(self):
        return super().isEnableBLDO2()

    async def enableBLDO2_async(self):
        return super().enableBLDO2()

    async def disableBLDO2_async(self):
        return super().disableBLDO2()

    async def setBLDO2Voltage_async(self, millivolt: int):
        return super().setBLDO2Voltage(millivolt)

    async def getBLDO2Voltage_async(self):
        return super().getBLDO2Voltage()

    async def isEnableCPUSLDO_async(self):
        return super().isEnableCPUSLDO()

    async def enableCPUSLDO_async(self):
        return super().enableCPUSLDO()

    async def disableCPUSLDO_async(self):
        return super().disableCPUSLDO()

    async def setCPUSLDOVoltage_async(self, millivolt: int):
        return super().setCPUSLDOVoltage(millivolt)

    async def getCPUSLDOVoltage_async(self):
        return super().getCPUSLDOVoltage()

    async def isEnableDLDO1_async(self):
        return super().isEnableDLDO1()

    async def enableDLDO1_async(self):
        return super().enableDLDO1()

    async def disableDLDO1_async(self):
        return super().disableDLDO1()

    async def setDLDO1Voltage_async(self, millivolt: int):
        return super().setDLDO1Voltage(millivolt)

    async def getDLDO1Voltage_async(self):
        return super().getDLDO1Voltage()

    async def isEnableDLDO2_async(self):
        return super().isEnableDLDO2()

    async def enableDLDO2_async(self):
        return super().enableDLDO2()

    async def disableDLDO2_async(self):
        return super().disableDLDO2()

    async def setDLDO2Voltage_async(self, millivolt: int):
        return super().setDLDO2Voltage(millivolt)

    async def getDLDO2Voltage_async(self):
        return super().getDLDO2Voltage()

    async def setIrqLevelTime_async(self, opt: int):
        return super().setIrqLevelTime(opt)

    async def getIrqLevelTime_async(self):
        return super().getIrqLevelTime()

    async def setPowerKeyPressOnTime_async(self, opt: int):
        return super().setPowerKeyPressOnTime(opt)

    async def getPowerKeyPressOnTime_async(self):
        return super().getPowerKeyPressOnTime()

    async def setPowerKeyPressOffTime_async(self, opt: int):
        return super().setPowerKeyPressOffTime(opt)

    async def getPowerKeyPressOffTime_async(self):
        return super().getPowerKeyPressOffTime()

    async def enableGeneralAdcChannel_async(self):
        return super().enableGeneralAdcChannel()

    async def disableGeneralAdcChannel_async(self):
        return super().disableGeneralAdcChannel()

    async def enableTemperatureMeasure_async(self):
        return super().enableTemperatureMeasure()

    async def disableTemperatureMeasure_async(self):
        return super().disableTemperatureMeasure()

    async def getTemperature_async(self):
        return super().getTemperature()

    async def enableSystemVoltageMeasure_async(self):
        return super().enableSystemVoltageMeasure()

    async def disableSystemVoltageMeasure_async(self):
        return super().disableSystemVoltageMeasure()

    async def getSystemVoltage_async(self):
        return super().getSystemVoltage()

    async def enableVbusVoltageMeasure_async(self):
        return super().enableVbusVoltageMeasure()

    async def disableVbusVoltageMeasure_async(self):
        return super().disableVbusVoltageMeasure()

    async def getVbusVoltage_async(self):
        return super().getVbusVoltage()

    async def enableTSPinMeasure_async(self):
        return super().enableTSPinMeasure()

    async def disableTSPinMeasure_async(self):
        return super().disableTSPinMeasure()

    async def enableTSPinLowFreqSample_async(self):
        return super().enableTSPinLowFreqSample()

    async def disableTSPinLowFreqSample_async(self):
        return super().disableTSPinLowFreqSample()

    async def getTsTemperature_async(self):
        return super().getTsTemperature()

    async def enableBattVoltageMeasure_async(self):
        return super().enableBattVoltageMeasure()

    async def disableBattVoltageMeasure_async(self):
        return super().disableBattVoltageMeasure()

    async def enableBattDetection_async(self):
        return super().enableBattDetection()

    async def disableBattDetection_async(self):
        return super().disableBattDetection()

    async def getBattVoltage_async(self):
        return super().getBattVoltage()

    async def getBatteryPercent_async(self):
        return super().getBatteryPercent()

    async def setChargingLedMode_async(self, mode: int):
        return super().setChargingLedMode(mode)

    async def getChargingLedMode_async(self):
        return super().getChargingLedMode()

    async def setPrechargeCurr_async(self, opt: int):
        return super().setPrechargeCurr(opt)

    async def getPrechargeCurr_async(self):
        return super().getPrechargeCurr()

    async def setChargerConstantCurr_async(self, opt: int):
        return super().setChargerConstantCurr(opt)

    async def getChargerConstantCurr_async(self):
        return super().getChargerConstantCurr()

    async def setChargerTerminationCurr_async(self, opt: int):
        return super().setChargerTerminationCurr(opt)

    async def getChargerTerminationCurr_async(self):
        return super().getChargerTerminationCurr()

    async def enableChargerTerminationLimit_async(self):
        return super().enableChargerTerminationLimit()

    async def disableChargerTerminationLimit_async(self):
        return super().disableChargerTerminationLimit()

    async def isChargerTerminationLimit_async(self):
        return super().isChargerTerminationLimit()

    async def setChargeTargetVoltage_async(self, opt: int):
        return super().setChargeTargetVoltage(opt)

    async def getChargeTargetVoltage_async(self):
        return super().getChargeTargetVoltage()

    async def setThermaThreshold_async(self, opt: int):
        return super().setThermaThreshold(opt)

    async def getThermaThreshold_async(self):
        return super().getThermaThreshold()

    async def getIrqStatus_async(self):
        return super().getIrqStatus()

    async def clearIrqStatus_async(self):
        return super().clearIrqStatus()

    async def enableIRQ_async(self, opt: int, debug=False):
        return super().enableIRQ(opt, debug)

    async def disableIRQ_async(self, opt: int, debug=False):
        return super().disableIRQ(opt, debug)

    async def isDropWarningLevel2Irq_async(self):
        return super().isDropWarningLevel2Irq()

    async def isDropWarningLevel1Irq_async(self):
        return super().isDropWarningLevel1Irq()

    async def isGaugeWdtTimeoutIrq_async(self):
        return super().isGaugeWdtTimeoutIrq()

    async def isStateOfChargeLowIrq_async(self):
        return super().isStateOfChargeLowIrq()

    async def isBatChargerOverTemperatureIrq_async(self):
        return super().isBatChargerOverTemperatureIrq()

    async def isBatChargerUnderTemperatureIrq_async(self):
        return super().isBatChargerUnderTemperatureIrq()

    async def isBatWorkOverTemperatureIrq_async(self):
        return super().isBatWorkOverTemperatureIrq()

    async def isBatWorkUnderTemperatureIrq_async(self):
        return super().isBatWorkUnderTemperatureIrq()

    async def isVbusInsertIrq_async(self):
        return super().isVbusInsertIrq()

    async def isVbusRemoveIrq_async(self):
        return super().isVbusRemoveIrq()

    async def isBatInsertIrq_async(self):
        return super().isBatInsertIrq()

    async def isBatRemoveIrq_async(self):
        return super().isBatRemoveIrq()

    async def isPekeyShortPressIrq_async(self):
        return super().isPekeyShortPressIrq()

    async def isPekeyLongPressIrq_async(self):
        return super().isPekeyLongPressIrq()

    async def isPekeyNegativeIrq_async(self):
        return super().isPekeyNegativeIrq()

    async def isPekeyPositiveIrq_async(self):
        return super().isPekeyPositiveIrq()

    async def isWdtExpireIrq_async(self):
        return super().isWdtExpireIrq()

    async def isLdoOverCurrentIrq_async(self):
        return super().isLdoOverCurrentIrq()

    async def isBatfetOverCurrentIrq_async(self):
        return super().isBatfetOverCurrentIrq()

    async def isBatChargeDoneIrq_async(self):
        return super().isBatChargeDoneIrq()

    async def isBatChargeStartIrq_async(self):
        return super().isBatChargeStartIrq()

    async def isBatDieOverTemperatureIrq_async(self):
        return super().isBatDieOverTemperatureIrq()

    async def isChargeOverTimeoutIrq_async(self):
        return super().isChargeOverTimeoutIrq()

    async def isBatOverVoltageIrq_async(self):
        return super().isBatOverVoltageIrq()

    async def getChipID_async(self):
        return super().getChipID()

    async def printIntRegister_async(self):
        return super().printIntRegister()

    async def writeGaugeData_async(self, data: bytearray):
        return super().writeGaugeData(data)

    async def compareGaugeData_async(self, data: bytearray, length: int):
        return super().compareGaugeData(data, length)

    async def deinit_async(self):
        return await super().deinit()
