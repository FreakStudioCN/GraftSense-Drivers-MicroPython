
import time
import machine
def _u16_be(b0, b1):
        return ((b0 & 0xFF) << 8) | (b1 & 0xFF)

def _s16_be(b0, b1):
        v = _u16_be(b0, b1)
        return v - 0x10000 if (v & 0x8000) else v
def _q_u8(self, ctl, cmd):
    """通用：返回 1字节无符号整数"""
    data = self.query_and_wait(ctl, cmd, b"\x0F")
    if not data:
        return None
    return data[0]

def _q_u16(self, ctl, cmd):
    """通用：返回 2字节无符号整数（大端）"""
    data = self.query_and_wait(ctl, cmd, b"\x0F")
    if data is None or len(data) < 2:
        return None
    return self._u16_be(data[0], data[1])

def _q_wave(self, ctl, cmd):
    """通用：返回波形数组 list[int]"""
    data = self.query_and_wait(ctl, cmd, b"\x0F")
    if data is None:
        return None
    return list(data)

class R60ABD1:
    def __init__(self, uart):
            if uart is None:
                raise ValueError("uart 不能为空")
            self.uart = uart

            # 协议固定量（写死即可，用不到就别暴露）
            self._control = 0x80
            self._timeout_ms = 300

            # 非阻塞解析的滚动缓冲（recv_response 用）
            self._rx_buf = bytearray()

            # 清掉上电残留
            n = self.uart.any()
            if n:
                self.uart.read(n)

        # 其余：build_frame / parse_response / recv_response / send_frame ...

    def build_frame(self, control: int, cmd: int, data: bytes = b"") -> bytes:
        # 参数与类型检查
        control = int(control)
        cmd = int(cmd)
        if not isinstance(data, (bytes, bytearray)):
            raise ValueError("data 必须为 bytes 或 bytearray")

        n = len(data)
        # 总长度 = 2头 +1ctl +1cmd +2len +n数据 +1sum +2尾
        frame = bytearray(2 + 1 + 1 + 2 + n + 1 + 2)
        frame[0] = 0x53  # 'S'
        frame[1] = 0x59  # 'Y'
        frame[2] = control
        frame[3] = cmd
        frame[4] = (n >> 8) & 0xFF  # LEN_H，大端
        frame[5] = n & 0xFF         # LEN_L
        if n:
            frame[6:6 + n] = data

        # 低 8 位累加和（含帧头，不含校验与尾部）
        s = 0
        for b in frame[:6 + n]:
            s = (s + b) & 0xFF
        frame[6 + n] = s

        frame[-2] = 0x54  # 'T'
        frame[-1] = 0x43  # 'C'
        return bytes(frame)


    def parse_response(self, resp: bytes):
        # 基础长度检查：最小 2头+1ctl+1cmd+2len+1sum+2尾 = 9
        if not resp or len(resp) < 9:
            raise ValueError("响应过短")

        if not (resp[0] == 0x53 and resp[1] == 0x59):
            raise ValueError("帧头错误")
        if not (resp[-2] == 0x54 and resp[-1] == 0x43):
            raise ValueError("帧尾错误")

        control = resp[2]
        cmd = resp[3]
        n = (resp[4] << 8) | resp[5]

        expected_len = 2 + 1 + 1 + 2 + n + 1 + 2  # = 9 + n
        if len(resp) != expected_len:
            raise ValueError("长度不匹配")

        data = resp[6:6 + n] if n else b""

        s = 0
        for b in resp[:6 + n]:  # 含头到数据末
            s = (s + b) & 0xFF
        if s != resp[6 + n]:
            raise ValueError("校验和不匹配")

        return {"control": control, "cmd": cmd, "data": data}

    def recv_response(self):
        """
        返回 (cmd:int, data:bytes)；超时返回 None。
        仅校验帧头/帧尾/长度/低8位和校验，格式不对就丢弃继续找。
        """
        timeout_ms = getattr(self, "timeout_ms", 300)

        t0 = time.ticks_ms()
        buf = bytearray()
        state = 0  # 0:找0x53, 1:找0x59, 2:已得6字节头, 3:收满
        need_total = None  # 全帧长度 = 2头+1ctl+1cmd+2len+n+1sum+2尾 = 9+n

        while time.ticks_diff(time.ticks_ms(), t0) < timeout_ms:
            b = self.uart.read(1)
            if not b:
                time.sleep_ms(1)
                continue
            x = b[0]

            if state == 0:
                if x == 0x53:  # 'S'
                    buf = bytearray([0x53]);
                    state = 1
                else:
                    continue
            elif state == 1:
                if x == 0x59:  # 'Y'
                    buf.append(0x59);
                    state = 2
                else:
                    state = 0;
                    buf = bytearray()
            elif state == 2:
                buf.append(x)
                if len(buf) == 6:
                    n = (buf[4] << 8) | buf[5]
                    need_total = 9 + n
                    state = 3
            elif state == 3:
                buf.append(x)
                if need_total is not None and len(buf) == need_total:
                    # 校验并解析
                    try:
                        if not (buf[0] == 0x53 and buf[1] == 0x59): raise ValueError
                        if not (buf[-2] == 0x54 and buf[-1] == 0x43): raise ValueError
                        n = (buf[4] << 8) | buf[5]
                        data = bytes(buf[6:6 + n]) if n else b""
                        s = 0
                        for v in buf[:6 + n]:
                            s = (s + v) & 0xFF
                        if s != buf[6 + n]: raise ValueError
                        ctrl = buf[2]
                        cmd = buf[3]  # 返回命令字

                        return (ctrl,cmd, data)
                    except ValueError:
                        # 坏帧：丢弃并重新找帧头
                        state = 0;
                        buf = bytearray();
                        need_total = None
                        continue
        return None
    def send_frame(self, control: int, cmd: int, data: bytes = b""):
        try:
            self.uart.write(self.build_frame(control, cmd, data))
        except IOError as e:
            raise IOError("UART 写入失败") from e

    def query_and_wait(self, control: int, command: int, send_data: bytes = b""):
        while True:
            # 1) 发送
            self.send_frame(control, command, send_data)

            # 2) 接收一次（recv_response 内部自带等待/超时）
            ret = self.recv_response()  # -> (ctrl, cmd, data) 或 None
            if ret is not None:
                ctrl, cmd, data = ret
                if (ctrl & 0xFF) == (control & 0xFF) and (cmd & 0xFF) == (command & 0xFF):
                    return data  # 命中，返回 data




    def disable_all_reports_and_check(self):
        self.query_and_wait(0x80, 0x00, b"\x00")
        self.query_and_wait(0x81, 0x00, b"\x00")
        self.query_and_wait(0x84, 0x00, b"\x00")
        self.query_and_wait(0x85, 0x00, b"\x00")


    # ===== 人体存在 / 体动 / 距离 / 方位 =====
    def q_presence(self):
        """存在信息：返回 0 或 1，超时/无数据返回 None"""
        data = self.query_and_wait(0x80, 0x81, b"\x0F")
        if not data:  # None 或 空
            return None
        return 1 if data[0] == 1 else 0

    def q_motion_param(self):
        """体动参数：0~100"""
        data = self.query_and_wait(0x80, 0x83, b"\x0F")
        if not data:
            return None
        return data[0]

    def q_distance(self):
        """人体距离：整数 cm"""
        data = self.query_and_wait(0x80, 0x84, b"\x0F")
        if data is None or len(data) < 2:
            return None
        return _u16_be(data[0], data[1])

    def q_position(self):
        """人体方位：返回 (x, y, z)；各为有符号16位"""
        data = self.query_and_wait(0x80, 0x85, b"\x0F")
        if data is None or len(data) < 6:
            return None
        x = _s16_be(data[0], data[1])
        y = _s16_be(data[2], data[3])
        z = _s16_be(data[4], data[5])
        return (x, y, z)

    # ===== 心率（查询类） =====
    def q_hr_value(self):
        """心率数值：bpm"""
        data = self.query_and_wait(0x85, 0x82, b"\x0F")
        if not data:
            return None
        return data[0]

    def q_hr_waveform(self):
        """心率波形：list[int]（去直流，原始值-128；长度5，约5Hz）"""
        data = self.query_and_wait(0x85, 0x85, b"\x0F")
        # 超时 / 无数据
        if data is None:
            return None
        # 期望 5 字节；不足则判为无效
        if len(data) < 5:
            return None
        # 解析：原始[0..255]，协议基线为128，减去128得到中心化波形
        return [data[0] - 128, data[1] - 128, data[2] - 128, data[3] - 128, data[4] - 128]

    # ===== 睡眠（查询类） =====
    def q_sleep_end_time(self):
        """睡眠截止时间：分钟"""
        data = self.query_and_wait(0x84, 0x96, b"\x0F")
        if not data:
            return None
        return data[0]

    def q_struggle_sensitivity(self):
        """挣扎灵敏度：0/1/2"""
        data = self.query_and_wait(0x84, 0x91, b"\x0F")
        if not data:
            return None
        return data[0]
