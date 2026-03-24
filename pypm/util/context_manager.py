import sys
import contextlib


class DummyFile(object):
    def write(self, x):
        pass

    def flush(self):
        pass


@contextlib.contextmanager
def suppress_stdout():
    """
    Context manager to suppres stdout
    """
    original_stdout = sys.stdout
    sys.stdout = DummyFile()
    try:
        yield
    finally:
        sys.stdout = original_stdout
