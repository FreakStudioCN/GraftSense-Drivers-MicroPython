from data_flow_processor import DataFlowProcessor
from ad8232 import AD8232
uart1 = UART(1, baudrate=115200, tx=Pin(8), rx=Pin(9))
processordata = DataFlowProcessor(uart1)
