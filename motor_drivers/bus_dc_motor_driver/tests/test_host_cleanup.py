"""Host shutdown fault tests use a real worker and fake video/serial surfaces."""

import json
import runpy
import sys
import types
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from host_cleanup import capture_cleanup, ensure_lib


class HostCleanupTests(unittest.TestCase):
    def test_main_failure_signals_and_joins_worker_before_video_and_plot_close(self):
        for failure in (BrokenPipeError("ffmpeg pipe"), OSError("CSV write"), RuntimeError("plot drawing")):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as directory:
                cancelled = threading.Event()
                order = []

                def run():
                    cancelled.wait(2)
                    order.append("device-stop-cleanup")

                thread = threading.Thread(target=run)
                recorder = Mock()
                recorder.stdin.close.side_effect = lambda: order.append("video-close")
                recorder.wait.return_value = 0
                path = Path(directory) / "shutdown.json"
                with self.assertRaises(type(failure)) as caught:
                    with capture_cleanup(
                        cancelled, thread, recorder, lambda: order.append("plot-close"), lambda: order.append("interrupt"), [], path
                    ):
                        thread.start()
                        raise failure
                self.assertIs(caught.exception, failure)
                self.assertFalse(thread.is_alive())
                self.assertLess(order.index("device-stop-cleanup"), order.index("video-close"))
                self.assertEqual(order[-1], "plot-close")
                self.assertTrue(json.loads(path.read_text())["worker_joined"])

    def test_real_pc_main_broken_pipe_interrupts_running_transport(self):
        running = threading.Event()
        interrupted = threading.Event()
        stopped = threading.Event()
        closed = threading.Event()
        real_event = threading.Event

        class Transport:
            def __init__(self, *args, **kwargs):
                self.files = {}
                self.serial = Mock()
                self.serial.write.side_effect = lambda data: interrupted.set()

            def enter_raw_repl(self, **kwargs):
                pass

            def fs_exists(self, path):
                return path == "/lib" or path in self.files

            def fs_isdir(self, path):
                return True

            def fs_writefile(self, path, data):
                self.files[path] = data

            def fs_readfile(self, path):
                return self.files[path]

            def exec_raw(self, *args, **kwargs):
                running.set()
                if not interrupted.wait(3):
                    raise TimeoutError("Host failed to interrupt running device")
                return b"", b""

            def exec(self, *args, **kwargs):
                stopped.set()

            def close(self):
                closed.set()

        def event():
            result = real_event()
            wait = result.wait
            result.wait = lambda timeout=None: False if timeout == 15 else wait(timeout)
            return result

        fig = Mock()
        fig.canvas.get_width_height.return_value = (1, 1)
        fig.canvas.buffer_rgba.return_value = b"0000"
        axes = types.SimpleNamespace(flat=[Mock() for _ in range(4)])
        for ax in axes.flat:
            ax.plot.return_value = (Mock(),)
        plt = types.ModuleType("matplotlib.pyplot")
        plt.rcParams = {}
        plt.subplots = Mock(return_value=(fig, axes))
        plt.show, plt.close = Mock(), Mock()
        plt.fignum_exists = Mock(return_value=True)
        mpl = types.ModuleType("matplotlib")
        mpl.pyplot = plt
        pil = types.ModuleType("PIL")
        pil.Image = Mock()
        pil.Image.frombuffer.return_value.resize.return_value.tobytes.return_value = b"0000"
        mpremote = types.ModuleType("mpremote")
        serial_module = types.ModuleType("mpremote.transport_serial")
        serial_module.SerialTransport = Transport
        recorder = Mock()
        recorder.wait.return_value = 0
        failure = BrokenPipeError("ffmpeg died while device running")

        def broken_write(data):
            self.assertTrue(running.wait(3))
            raise failure

        recorder.stdin.write.side_effect = broken_write
        modules = {
            "matplotlib": mpl,
            "matplotlib.pyplot": plt,
            "numpy": types.ModuleType("numpy"),
            "PIL": pil,
            "mpremote": mpremote,
            "mpremote.transport_serial": serial_module,
        }
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "capture"
            script = Path(__file__).with_name("pc_live_plot.py")
            with patch.dict(sys.modules, modules), patch.object(sys, "argv", [str(script), "--run", "--out", str(out)]):
                with patch("subprocess.Popen", return_value=recorder), patch("threading.Event", side_effect=event):
                    with self.assertRaises(BrokenPipeError) as caught:
                        runpy.run_path(str(script), run_name="__main__")
            self.assertIs(caught.exception, failure)
            self.assertTrue(interrupted.is_set())
            self.assertTrue(stopped.is_set())
            self.assertTrue(closed.is_set())
            self.assertTrue(json.loads((out / "shutdown.json").read_text())["worker_joined"])
            plt.close.assert_called_once_with(fig)

    def test_cleanup_failure_does_not_mask_primary_or_skip_plot(self):
        with tempfile.TemporaryDirectory() as directory:
            recorder = Mock()
            recorder.stdin.close.side_effect = BrokenPipeError("already broken")
            recorder.wait.return_value = 1
            close_plot = Mock()
            failure = OSError("original")
            with self.assertRaises(OSError) as caught:
                with capture_cleanup(threading.Event(), threading.Thread(), recorder, close_plot, Mock(), [], Path(directory) / "status.json"):
                    raise failure
            self.assertIs(caught.exception, failure)
            close_plot.assert_called_once()

    def test_join_timeout_is_reported_not_confirmed_as_stop(self):
        with tempfile.TemporaryDirectory() as directory:
            thread = Mock(ident=1)
            thread.is_alive.return_value = True
            recorder = Mock()
            recorder.wait.return_value = 0
            status = Path(directory) / "status.json"
            with self.assertRaisesRegex(RuntimeError, "unconfirmed"):
                with capture_cleanup(threading.Event(), thread, recorder, Mock(), Mock(), [], status, join_timeout=0.01):
                    pass
            self.assertFalse(json.loads(status.read_text())["worker_joined"])

    def test_lib_creation_and_existing_directory(self):
        for exists in (False, True):
            transport = Mock()
            transport.fs_exists.return_value = exists
            transport.fs_isdir.return_value = True
            ensure_lib(transport)
            self.assertEqual(transport.fs_mkdir.call_count, 0 if exists else 1)
        transport.fs_isdir.return_value = False
        with self.assertRaises(NotADirectoryError):
            ensure_lib(transport)
