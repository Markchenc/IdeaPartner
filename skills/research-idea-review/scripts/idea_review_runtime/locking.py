from __future__ import annotations

import os
import time
from pathlib import Path
from types import TracebackType
from typing import BinaryIO


class FileLockTimeout(TimeoutError):
    pass


class InterProcessFileLock:
    """One-byte exclusive lock that works across local Python processes."""

    def __init__(self, path: Path, *, timeout: float = 30.0, poll_interval: float = 0.05) -> None:
        self.path = Path(path)
        self.timeout = timeout
        self.poll_interval = poll_interval
        self._handle: BinaryIO | None = None

    def __enter__(self) -> "InterProcessFileLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self.path.open("a+b")
        self._handle.seek(0, os.SEEK_END)
        if self._handle.tell() == 0:
            self._handle.write(b"\0")
            self._handle.flush()
        deadline = time.monotonic() + self.timeout
        while True:
            try:
                self._acquire_once()
                return self
            except (OSError, BlockingIOError):
                if time.monotonic() >= deadline:
                    self._handle.close()
                    self._handle = None
                    raise FileLockTimeout(f"Timed out waiting for run lock {self.path}")
                time.sleep(self.poll_interval)

    def _acquire_once(self) -> None:
        if self._handle is None:
            raise RuntimeError("Lock file is not open")
        self._handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(self._handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(self._handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._handle is None:
            return
        try:
            self._handle.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(self._handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(self._handle.fileno(), fcntl.LOCK_UN)
        finally:
            self._handle.close()
            self._handle = None
