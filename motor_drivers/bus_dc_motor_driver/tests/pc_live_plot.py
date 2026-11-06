"""Live USB-serial PID plots, measured timing, CSV and live-canvas recording.

Install: pip install matplotlib numpy pyserial mpremote
Run: python pc_live_plot.py --port COM8 --baud 921600 --run --seconds 10 --out results
Explicit --run deploys the current package and moves the motors for a bounded test.
USB CDC/JTAG baud is a host request, not a guarantee of UART bit rate.
"""

import argparse
import csv
import json
import queue
import subprocess
import threading
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from pid_response_metrics import response_metrics, last_reference_segment
from host_cleanup import capture_cleanup, ensure_lib

ROOT = Path(__file__).resolve().parents[1]
COLUMNS = ["phase", "period_ms", "elapsed_ms"] + [f"target{i}" for i in range(1, 5)] + [f"rpm{i}" for i in range(1, 5)]
COLUMNS += [f"pwm{i}" for i in range(1, 5)] + ["voltage", "loop_us", "i2c_us", "pid_us", "previous_print_us", "control_dt_ms"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile",
        choices=("performance_profile", "tuning_profile", "realtime_audit", "realtime_audit_light", "i2c_benchmark"),
        default="performance_profile",
    )
    parser.add_argument("--reuse", action="store_true", help="reuse already verified device libraries; upload experiment scripts only")
    parser.add_argument("--port", default="COM8")
    parser.add_argument("--baud", type=int, default=921600)
    parser.add_argument("--seconds", type=int, default=10)
    parser.add_argument("--out", type=Path, default=Path("pid-results"))
    parser.add_argument("--run", action="store_true", help="deploy and move motors; required")
    args = parser.parse_args()
    if not 5 <= args.seconds <= 20:
        parser.error("Duration must be 5..20 seconds")
    if not args.run:
        parser.error("Use --run only after preparing the connected motor bench")
    args.out.mkdir(parents=True, exist_ok=False)
    events = queue.Queue()
    done = threading.Event()
    cancelled = threading.Event()
    errors = []
    rows = []
    device_stats = {}
    configs = {}
    motor_configs = {}
    startup_i = {}
    bus_configs = {}
    active_transport = {}

    def worker_body():
        from mpremote.transport_serial import SerialTransport

        transport = None
        pending = bytearray()
        with (args.out / "serial.log").open("wb") as log:

            def consume(chunk):
                log.write(chunk)
                log.flush()
                pending.extend(chunk)
                while b"\n" in pending:
                    line, _, rest = pending.partition(b"\n")
                    pending[:] = rest
                    text = line.decode(errors="replace").strip("\r\x04")
                    if text.startswith("D,"):
                        values = list(map(float, text[2:].split(",")))
                        if len(values) == len(COLUMNS):
                            events.put(values)
                    elif text:
                        if text.startswith("BUS_CONFIG,"):
                            fields = text.split(",")
                            bus_configs[int(fields[1])] = dict(frequency=int(fields[2]), mode=fields[3])
                        if text.startswith("STARTUP_I,"):
                            fields = text.split(",")
                            startup_i[int(fields[1])] = float(fields[2])
                        if text.startswith("MOTOR_CONFIG,"):
                            config = list(map(float, text.split(",")[1:]))
                            motor_configs.setdefault(int(config[0]), {})[int(config[1])] = config[2:]
                        if text.startswith("CONFIG,"):
                            config = list(map(float, text.split(",")[1:]))
                            configs[int(config[0])] = config[1:]
                        if text.startswith("TIMING,"):
                            data = list(map(int, text.split(",")[1:]))
                            device_stats[data[0]] = data[1:]
                        print(text, flush=True)
                if cancelled.is_set():
                    raise KeyboardInterrupt("Plot closed")

            try:
                transport = SerialTransport(args.port, baudrate=args.baud)
                transport.serial.write_timeout = 1
                transport.enter_raw_repl(soft_reset=False)
                ensure_lib(transport)
                backup = args.out / "device-backup"
                backup.mkdir()
                uploaded = args.out / "uploaded-source"
                uploaded.mkdir()
                sources = ([] if args.reuse else list((ROOT / "code").glob("*.py"))) + [
                    ROOT / "examples" / n
                    for n in (
                        "board_setup.py",
                        "performance_profile.py",
                        "tuning_profile.py",
                        "timing_audit.py",
                        "realtime_audit.py",
                        "realtime_audit_light.py",
                        "i2c_strategies.py",
                        "i2c_benchmark.py",
                    )
                ]
                for source in sources:
                    if cancelled.is_set():
                        raise KeyboardInterrupt("Upload cancelled")
                    if source.name == "main.py":
                        continue
                    dest = "/lib/" + source.name
                    if transport.fs_exists(dest):
                        (backup / source.name).write_bytes(transport.fs_readfile(dest))
                    (uploaded / source.name).write_bytes(source.read_bytes())
                    transport.fs_writefile(dest, source.read_bytes())
                    if transport.fs_readfile(dest) != source.read_bytes():
                        raise RuntimeError("Upload verify failed: " + source.name)
                print("Upload verified. Starting in 15 seconds.", flush=True)
                if cancelled.wait(15):
                    raise KeyboardInterrupt("Plot closed before motion")
                code = "import sys\n"
                code += "for n in ('i2c_strategies','i2c_benchmark','board_setup','performance_profile','tuning_profile','realtime_audit','realtime_audit_light','timing_audit','pca9685','motor','encoder','pid','motor_controller','voltage_monitor','bus_dc_motor'):\n if n in sys.modules: del sys.modules[n]\n if n in globals(): del globals()[n]\n"
                code += "import gc; gc.collect()\n"
                code += f"import {args.profile}\n{args.profile}.run(True,{args.seconds})\n"
                active_transport["running"] = transport
                _, error = transport.exec_raw(code, timeout=10, data_consumer=consume)
                if error:
                    raise RuntimeError(error.decode(errors="replace"))
            except BaseException as exc:
                errors.append(str(exc))
            finally:
                active_transport.pop("running", None)
                if transport is not None:
                    try:
                        transport.serial.write(b"\x03\x03")
                        transport.enter_raw_repl(soft_reset=False)
                        transport.exec(
                            "from machine import I2C,Pin\ni=I2C(0,scl=Pin(9),sda=Pin(10),freq=400000)\ni.writeto_mem(0x4f,0,b'\\x20')\nfor c in range(8): i.writeto_mem(0x4f,6+4*c,b'\\x00\\x00\\x00\\x10')\nprint('OUTPUTS_OFF')",
                            data_consumer=lambda b: log.write(b),
                        )
                    except BaseException as exc:
                        errors.append("Emergency stop: " + str(exc))
                    finally:
                        transport.close()
                done.set()

    def worker():
        try:
            worker_body()
        except BaseException as exc:
            errors.append("Worker: " + str(exc))
        finally:
            done.set()

    def interrupt():
        transport = active_transport.get("running")
        if transport is not None:
            transport.serial.write(b"\x03\x03")

    plt.rcParams.update({"font.size": 11})
    fig, axes = plt.subplots(2, 2, figsize=(14, 9), dpi=100)
    fig.canvas.manager.set_window_title("Motor PID - live measured response")
    fig.subplots_adjust(top=0.87, bottom=0.16, hspace=0.35, wspace=0.23)
    info = fig.text(0.05, 0.04, "Uploading and verifying current device modules...", fontsize=11)
    lines = []
    labels = []
    for i, ax in enumerate(axes.flat):
        ax.set(title=f"M{i + 1}: target vs measured", xlabel="Time in phase (s)", ylabel="RPM", ylim=(-100, 100), xlim=(0, args.seconds + 1))
        ax.grid(alpha=0.25)
        (target,) = ax.plot([], [], "--", color="#e17c20", label="Target")
        (actual,) = ax.plot([], [], color="#147eb8", lw=1.3, label="Measured (raw)")
        ax.legend(loc="lower right")
        lines.append((target, actual))
        labels.append(ax.text(0.02, 0.96, "Waiting for data", transform=ax.transAxes, va="top", fontsize=10))
    title = fig.suptitle("4-motor PID: live serial plot | gains only roughly adjusted", fontsize=15)
    recorder = subprocess.Popen(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgba",
            "-s",
            "1400x900",
            "-r",
            "5",
            "-i",
            "-",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "22",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(args.out / "live-plot.mp4"),
        ],
        stdin=subprocess.PIPE,
    )
    worker_thread = threading.Thread(target=worker, daemon=False)
    with capture_cleanup(cancelled, worker_thread, recorder, lambda: plt.close(fig), interrupt, errors, args.out / "shutdown.json"):
        worker_thread.start()
        plt.show(block=False)
        count = 0
        record_start = time.monotonic()
        with (args.out / "samples.csv").open("w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(COLUMNS)
            while not done.is_set() or not events.empty():
                tick = time.monotonic()
                while not events.empty():
                    row = events.get_nowait()
                    rows.append(row)
                    writer.writerow(row)
                csvfile.flush()
                if not plt.fignum_exists(fig.number):
                    cancelled.set()
                    done.wait(2)
                    continue
                if rows:
                    phase = rows[-1][0]
                    selected = [r for r in rows if r[0] == phase]
                    a = np.asarray(selected)
                    mode = (
                        "cached PWM + explicit 80 ms speed window"
                        if phase == 5
                        else ("cached repeated PWM writes" if phase == 4 else "original PWM writes")
                    )
                    title.set_text(
                        f"Phase {int(phase)}/5 | {a[-1, 1]:.0f} ms control | {mode}"
                        if not configs
                        else (
                            f"Per-motor PI tuning: phase {int(phase)} | see gains in each panel"
                            if motor_configs
                            else f"PI tuning: phase {int(phase)} | Kp,Ki,Kd,window = {configs.get(int(phase))}"
                        )
                    )
                    if bus_configs:
                        title.set_text(f"I2C case {int(phase)}/7 | {bus_configs[int(phase)]} | fixed per-motor PI")
                    for i, (target, actual) in enumerate(lines):
                        target.set_data(a[:, 2] / 1000, a[:, 3 + i])
                        actual.set_data(a[:, 2] / 1000, a[:, 7 + i])
                        actual.set_label(
                            f"Measured ({motor_configs.get(int(phase), {}).get(i + 1, configs[int(phase)])[3]:.0f}ms window)"
                            if configs
                            else ("Measured (80ms window)" if phase == 5 else "Measured (raw)")
                        )
                        axes.flat[i].get_legend().get_texts()[1].set_text(actual.get_label())
                        m = response_metrics(last_reference_segment(selected, i), i)
                        if m:
                            steady = f"{m['settling_s']:.2f}s" if m["settling_s"] is not None else "not settled in +/-5% band"
                            labels[i].set_text(
                                f"Observed overshoot: {m['overshoot_pct']:.1f}%\nSettling: {steady}\n"
                                + (
                                    f"P/I/D/window: {motor_configs[int(phase)][i + 1]}"
                                    if motor_configs
                                    else "Live estimate; final result uses full record"
                                )
                            )
                    costs = np.mean(a[-min(50, len(a)) :, 16:20], axis=0) / 1000
                    feedback_note = (
                        "Phase 5 uses an explicit 80ms speed window; phases 1-4 use raw feedback. Timing includes profiling overhead."
                        if not configs
                        else "Tuning uses the explicitly labelled speed window in every phase."
                    )
                    info.set_text(
                        f"USB serial requested: {args.baud} | I2C: see case title | Gains: see panel configuration\n"
                        f"4-loop update {costs[0]:.3f} ms | I2C {costs[1]:.3f} ms | PID {costs[2]:.3f} ms | previous serial print {costs[3]:.3f} ms\n"
                        + feedback_note
                    )
                fig.canvas.draw()
                w, h = fig.canvas.get_width_height(physical=True)
                frame = Image.frombuffer("RGBA", (w, h), fig.canvas.buffer_rgba(), "raw", "RGBA", 0, 1)
                payload = frame.resize((1400, 900)).tobytes()
                target_frames = max(count + 1, int((time.monotonic() - record_start) * 5))
                for _ in range(target_frames - count):
                    recorder.stdin.write(payload)
                count = target_frames
                plt.pause(max(0.001, 0.2 - (time.monotonic() - tick)))
        summary = {}
        for phase in sorted({int(r[0]) for r in rows}):
            selected = [r for r in rows if r[0] == phase]
            a = np.asarray(selected)
            summary[phase] = dict(
                period_ms=a[-1, 1], samples=len(a), motors=[response_metrics(last_reference_segment(selected, i), i) for i in range(4)]
            )
            summary[phase]["timing_ms"] = {
                name: dict(mean=float(np.mean(a[:, col]) / 1000), p95=float(np.percentile(a[:, col], 95) / 1000), max=float(np.max(a[:, col]) / 1000))
                for name, col in zip(COLUMNS[16:20], range(16, 20))
            }
            dt = a[:, 20]
            summary[phase]["actual_period_ms"] = dict(mean=float(np.mean(dt)), p95=float(np.percentile(dt, 95)), max=float(np.max(dt)))
            if phase in device_stats:
                st = device_stats[phase]
                summary[phase]["all_control_cycles"] = dict(
                    count=st[0],
                    loop_mean_ms=st[1] / st[0] / 1000,
                    i2c_mean_ms=st[2] / st[0] / 1000,
                    pid_mean_ms=st[3] / st[0] / 1000,
                    loop_max_ms=st[4] / 1000,
                    i2c_max_ms=st[5] / 1000,
                    pid_max_ms=st[6] / 1000,
                    actual_period_mean_ms=st[7] / st[0],
                    actual_period_max_ms=st[8],
                    late_cycles_over_2ms=st[9],
                    print_mean_ms=st[10] / max(1, st[12]) / 1000,
                    print_max_ms=st[11] / 1000,
                )
        (args.out / "summary.json").write_text(
            json.dumps(
                dict(
                    phases=summary,
                    configs=configs,
                    bus_configs=bus_configs,
                    response_metrics_scope="latest_constant_reference_segment",
                    motor_configs=motor_configs,
                    startup_i_percent=startup_i,
                    errors=errors,
                    video_frames=count,
                ),
                indent=2,
            ),
            encoding="utf-8",
        )
        fig.savefig(args.out / "last-phase.png")
        print(json.dumps(summary), flush=True)
        if errors:
            raise RuntimeError(errors)


if __name__ == "__main__":
    main()
