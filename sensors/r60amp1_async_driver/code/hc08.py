class HC08:
    """Minimal transparent UART status sender retained from the source demo."""

    def __init__(self, uart, rx_timeout_ms=600):
        if not hasattr(uart, "write"):
            raise ValueError("uart must provide write")
        self._uart = uart
        self.rx_timeout_ms = rx_timeout_ms

    def send_data(self, data):
        if isinstance(data, str):
            data = data.encode()
        try:
            return True, self._uart.write(data)
        except OSError:
            return False, "uart write error"

