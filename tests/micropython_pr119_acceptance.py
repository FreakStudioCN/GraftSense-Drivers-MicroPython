"""Real MicroPython contracts for final-review fixes, using injected peripherals.

Run like micropython_pr119_smoke.py; this is not electrical board acceptance.
"""
import micropython_pr119_smoke as env
import asyncio
import json
import time

load,Bus=env.load,env.Bus

def blank(cls):
    class Blank(cls):
        def __init__(self): pass
    return Blank()

async def heartbeat_during(operation):
    beats=[]
    async def heartbeat():
        while True:
            beats.append(1)
            await asyncio.sleep_ms(0)
    task=asyncio.create_task(heartbeat())
    try:
        value=await operation()
        return value,len(beats)
    finally:
        task.cancel()
        try:await task
        except asyncio.CancelledError:pass

class ReadyBus(Bus):
    def __init__(self,ready=True):
        super().__init__({0:0x48,0x75:0x71,0x0d:0x10,0x10:128,0x11:128,0x12:128})
        self.ready=ready
    def readfrom_mem(self,address,reg,count,**kwargs):
        if reg==8:
            return bytes([(self.registers.get(8,0)&15)|(0xb0 if self.ready else 0)])
        return super().readfrom_mem(address,reg,count,**kwargs)

async def main():
    rtc=load('misc/DS1307_async_driver','ds1307_async').DS1307Async(Bus())
    date=(2026,10,20,12,34,56,1)
    await rtc.set_datetime_async(date)
    assert (await rtc.get_datetime_async())[:7]==date
    assert len(await rtc.get_datetime_rtc_async())==8
    await rtc.set_disable_oscillator_async(True)
    assert await rtc.get_disable_oscillator_async()
    await rtc.set_disable_oscillator_async(False)
    assert not await rtc.get_disable_oscillator_async()

    ip=load('misc/ip5306_async_driver','ip5306_async').IP5306Async(Bus({0x78:0x80}))
    assert await ip.level_async()==75

    adt=load('sensors/adt7410_async_driver','adt7410_async').ADT7410Async(Bus({0x0b:0xcb}))
    for name in ('temperature','operation_mode','resolution_mode','comparator_mode','alert_status',
                 'high_temperature','low_temperature','critical_temperature','hysteresis_temperature'):
        method='temperature_async' if name=='temperature' else 'alert_status_async' if name=='alert_status' else 'get_'+name+'_async'
        assert await getattr(adt,method)()==getattr(adt,name)
    for name,value in [('resolution_mode',1),('comparator_mode',1),('high_temperature',30),
                       ('low_temperature',10),('critical_temperature',60),('hysteresis_temperature',3)]:
        await getattr(adt,'set_'+name+'_async')(value)
        assert await getattr(adt,'get_'+name+'_async')()==getattr(adt,name)

    bme=load('sensors/bme680_async_driver','bme680_async').BME680_I2CAsync(Bus({0xd0:0x61,0x1d:0x80}))
    await bme.initialize_async()
    # A valid simulated pressure calibration avoids a physically invalid zero divisor.
    bme._pressure_calibration[0]=30000
    result=await bme.measurements_async()
    assert len(result)==5 and not bme._async_sample_ready
    bme._async_sample_ready=True
    try:assert result==(bme.temperature,bme.humidity,bme.pressure,bme.gas,bme.altitude)
    finally:bme._async_sample_ready=False

    dps_module=load('sensors/dps310_async_driver','dps310_async')
    bus=ReadyBus();sensor=dps_module.DPS310Async(bus)
    assert bus.writes==[]
    await sensor.initialize_async()
    reference_bus=ReadyBus();reference=dps_module.source.DPS310(reference_bus)
    assert bus.writes==reference_bus.writes
    assert await sensor.get_temperature_async()==reference.temperature
    assert await sensor.get_pressure_async()==reference.pressure
    bad=dps_module.DPS310Async(ReadyBus(False))
    async def timeout():
        try:await bad.initialize_async(10)
        except asyncio.TimeoutError:return
        raise AssertionError('DPS310 unready startup did not time out')
    _,beats=await heartbeat_during(timeout)
    assert beats>0
    await env.cancel_after_first_yield(bad.initialize_async())
    assert not bad._initialized
    bad._i2c.ready=True
    await bad.initialize_async()

    apds_module=load('sensors/apds9960_async_driver','apds9960_async')
    bus=Bus();apds=apds_module.APDS9960Async(bus)
    assert bus.writes==[]
    _,beats=await heartbeat_during(apds.initialize_async)
    assert beats>0
    reference_bus=Bus();apds_module.APDS9960(reference_bus)
    assert bus.writes==reference_bus.writes
    await apds.aclose();await apds.aclose()

    si_module=load('sensors/si1145_async_driver','si1145_async')
    bus=Bus();si=si_module.SI1145Async(bus)
    assert bus.writes==[]
    _,beats=await heartbeat_during(si.initialize_async)
    assert beats>0
    reference_bus=Bus();si_module.SI1145(reference_bus)
    assert bus.writes==reference_bus.writes

    mpu_module=load('sensors/mpu9250_async_driver','ak8963_async')
    for name in ('MPU6500','AK8963'):
        cls=getattr(mpu_module,name+'Async')
        bus=ReadyBus();sensor=cls(bus)
        assert bus.writes==[]
        _,beats=await heartbeat_during(sensor.initialize_async)
        assert beats>0
        reference_bus=ReadyBus();getattr(mpu_module,name)(reference_bus)
        assert bus.writes==reference_bus.writes
        await sensor.aclose();await sensor.aclose()
        sensor=cls(ReadyBus())
        await env.cancel_after_first_yield(sensor.initialize_async())
        assert not sensor._initialized

    composite=mpu_module.MPU9250Async(ReadyBus(),blank(mpu_module.MPU6500),blank(mpu_module.AK8963))
    await composite.start_async()
    assert composite.mpu6500._initialized and composite.ak8963._initialized
    children=(composite.mpu6500,composite.ak8963)
    await composite.start_async()
    assert (composite.mpu6500,composite.ak8963)==children
    await composite.aclose()

    for name in ('lis2mdl','lis3mdl'):
        module=load('sensors/'+name+'_async_driver','_gs_'+name+'_micropython_'+name+'.'+name+'_async')
        sensor=blank(getattr(module,name.upper()+'Async'))
        sensor._i2c=Bus();sensor._address=0x1e
        _,beats=await heartbeat_during(sensor.reset_async)
        assert beats>0 and sensor._i2c.writes

    fde=load('sensors/fde_frost_async_driver','fde_frost_modbus_rtu_async')
    mcp=load('sensors/mcp1081_async_driver','mcp1081_modbus_rtu_async')
    mse=load('sensors/mse_soil_sensor_async_driver','mse_soil_modbus_rtu_async')
    assert fde.FDEFrostTransportAsync and mcp.ModbusRTUMasterAsync and mse.CDS1081Async
    mcp1=load('sensors/mcp1081_async_driver','mcp1081_mer_async')
    mcp2=load('sensors/mcp_async_driver','mcp_mer_async')
    class Transport:
        async def transaction_async(self,*args):pass
    assert mcp1.MERAsync(Transport(),slave_addr=1) is not None
    assert mcp1.MERAsync is not mcp2.MERAsync
    print(json.dumps({'passed':True,'runtime':env.sys.version,'contract_modules':len(env.loaded),
                      'hardware_tested':False,'properties':26,'source_startup_order':True,'mixed_entries':True}))

if __name__=='__main__':asyncio.run(main())
