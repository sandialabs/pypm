import contextlib

@contextlib.contextmanager
def suppress_stdout():
    original_stdout = sys.stdout
    sys.stdout = DummyFile()
    try:
        yield
    finally:
        sys.stdout = original_stdout
