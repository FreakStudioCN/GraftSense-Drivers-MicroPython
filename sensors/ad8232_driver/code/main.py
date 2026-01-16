from data_flow_processor import DataFlowProcessor
from ad8232 import AD8232
from machine import UART, Pin, Timer
from ecg_module_cmd import AD8232_DataFlowProcessor
uart1 = UART(1, baudrate=115200, tx=Pin(8), rx=Pin(9))
processordata=DataFlowProcessor(uart1)
ad8232=AD8232(adc_pin=26, loff_plus_pin=16, loff_minus_pin=17,sdn_pin=14)
edg=AD8232_DataFlowProcessor(processordata,ad8232)