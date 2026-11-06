"""Host-only shutdown helpers; no plotting or serial dependency required."""

from contextlib import contextmanager
import json
import subprocess


def ensure_lib(transport):
    if not transport.fs_exists("/lib"):
        transport.fs_mkdir("/lib")
    elif not transport.fs_isdir("/lib"):
        raise NotADirectoryError("Device /lib exists but is not a directory")


@contextmanager
def capture_cleanup(cancelled, worker, recorder, close_plot, interrupt, errors, status_path, join_timeout=5):
    """Request stop on every exit; preserve a primary exception over cleanup errors.

    A joined worker only confirms host cleanup finished, not physical motor state.
    Serial disconnection or cleanup failure must remain visible in errors/status.
    """
    failed = False
    try:
        yield
    except BaseException:
        failed = True
        raise
    finally:
        cancelled.set()
        try:
            interrupt()
        except Exception as exc:
            errors.append("Stop notification: " + str(exc))
        try:
            if worker.ident is not None:
                worker.join(join_timeout)
        except Exception as exc:
            errors.append("Worker join: " + str(exc))
        joined = not worker.is_alive()
        if not joined:
            errors.append("Worker stop cleanup timed out; device stop is unconfirmed")
        try:
            if recorder.stdin is not None:
                recorder.stdin.close()
        except Exception as exc:
            errors.append("Video pipe close: " + str(exc))
        try:
            if recorder.wait(timeout=5) != 0:
                errors.append("Video encoder failed")
        except subprocess.TimeoutExpired:
            try:
                recorder.terminate()
                recorder.wait(timeout=2)
            except subprocess.TimeoutExpired:
                try:
                    recorder.kill()
                    recorder.wait(timeout=2)
                except Exception as exc:
                    errors.append("Video kill: " + str(exc))
            except Exception as exc:
                errors.append("Video terminate: " + str(exc))
        except Exception as exc:
            errors.append("Video shutdown: " + str(exc))
        finally:
            try:
                close_plot()
            except Exception as exc:
                errors.append("Plot shutdown: " + str(exc))
            try:
                status_path.write_text(json.dumps(dict(cancel_requested=True, worker_joined=joined, errors=list(errors)), indent=2), encoding="utf-8")
            except Exception as exc:
                errors.append("Shutdown status write: " + str(exc))
        if errors and not failed:
            raise RuntimeError(errors)
