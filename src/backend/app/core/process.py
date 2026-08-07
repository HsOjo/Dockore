"""Utilities for monitoring the parent process and exiting when it dies."""

import asyncio
import os
import platform


def is_process_alive(pid: int) -> bool:
    """Check whether a process with the given PID is still running."""
    if platform.system() == "Windows":
        import ctypes
        from ctypes import wintypes

        SYNCHRONIZE = 0x00100000
        PROCESS_QUERY_INFORMATION = 0x00000400
        STILL_ACTIVE = 259

        # Use a dedicated DLL instance and set correct types so 64-bit HANDLEs are not
        # truncated to 32-bit c_int, which broke parent-process detection on x64 Windows.
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.argtypes = [
            wintypes.DWORD,
            wintypes.BOOL,
            wintypes.DWORD,
        ]
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.GetExitCodeProcess.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(wintypes.DWORD),
        ]
        kernel32.GetExitCodeProcess.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL

        handle = kernel32.OpenProcess(
            SYNCHRONIZE | PROCESS_QUERY_INFORMATION, False, pid
        )
        if not handle:
            return False
        try:
            exit_code = wintypes.DWORD()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                return False
            return exit_code.value == STILL_ACTIVE
        finally:
            kernel32.CloseHandle(handle)
    else:
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            return True


def _wait_for_parent_death_windows(parent_pid: int, timeout_ms: int) -> bool:
    """Windows-only: wait up to timeout_ms for the parent process to exit.

    Returns True if the parent died or is no longer accessible.
    """
    import ctypes
    from ctypes import wintypes

    SYNCHRONIZE = 0x00100000
    WAIT_TIMEOUT = 0x00000102

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel32.WaitForSingleObject.restype = wintypes.DWORD
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL

    handle = kernel32.OpenProcess(SYNCHRONIZE, False, parent_pid)
    if not handle:
        # Parent already dead or we cannot access it; treat as dead.
        return True
    try:
        result = kernel32.WaitForSingleObject(handle, timeout_ms)
        return result != WAIT_TIMEOUT
    finally:
        kernel32.CloseHandle(handle)


async def monitor_parent(parent_pid: int) -> None:
    """Exit the process if the parent process dies."""
    if platform.system() == "Windows":
        # Block on the parent process handle in a thread with a short timeout so we
        # get near-instant detection while still allowing graceful cancellation.
        while True:
            parent_died = await asyncio.to_thread(
                _wait_for_parent_death_windows, parent_pid, 1000
            )
            if parent_died:
                print(f"Parent process {parent_pid} died, exiting")
                os._exit(1)
            await asyncio.sleep(0)
    else:
        while True:
            await asyncio.sleep(5)
            if not is_process_alive(parent_pid):
                print(f"Parent process {parent_pid} died, exiting")
                os._exit(1)
