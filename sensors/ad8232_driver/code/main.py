from data_flow_processor import DataFlowProcessor
from ad8232 import AD8232
from machine import UART, Pin, Timer
from ecg_module_cmd import AD8232_DataFlowProcessor
from ecg_signal_processor import ECGSignalProcessor

uart1 = UART(1, baudrate=115200, tx=Pin(8), rx=Pin(9))
processordata = DataFlowProcessor(uart1)
ad8232=AD8232(adc_pin=27, loff_plus_pin=0, loff_minus_pin=1,sdn_pin=2)
edg_signal = ECGSignalProcessor(AD8232=ad8232, fs=100.0)
ad8232_processor = AD8232_DataFlowProcessor(DataFlowProcessor=processordata,AD8232=ad8232,ECGSignalProcessor=edg_signal)

ad8232_processor.ECGSignalProcessor.start()