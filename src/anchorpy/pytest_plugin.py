"""This module provides the `localnet_fixture` fixture factory."""
from typing import AsyncGenerator, Callable, Literal, Optional, Union
import subprocess
import signal
import os
from pathlib import Path
from pytest import fixture
from pytest_asyncio import fixture as async_fixture
from xprocess import XProcessInfo, XProcess, ProcessStarter
from pytest_xprocess import getrootdir
from anchorpy import create_workspace, close_workspace
from anchorpy.program.core import Program

_Scope = Literal["session", "package", "module", "class", "function"]


class _FixedXProcessInfo(XProcessInfo):
    def terminate(self, timeout=60):
        if not self.pid:
            return 0
        try:
            pgid = os.getpgid(self.pid)
        except ProcessLookupError:
            return 0
        try:
            os.killpg(pgid, signal.SIGTERM)
        except OSError as err:
            print(f"Error while terminating process {err}")  # noqa: WPS421
            return -1
        return 1


class _FixedXProcess(XProcess):
    def getinfo(self, name: str) -> _FixedXProcessInfo:
        """Return Process Info for the given external process.

        Args:
            name: Name of the external process.
        """
        return _FixedXProcessInfo(self.rootdir, name)

    def ensure(
        self, name: str, preparefunc: ProcessStarter, restart: bool = False
    ) -> tuple:
        """Return (PID, logfile) from a newly started or already running process.

        Args:
            name: Name of the external process, used for caching info across test runs.
            preparefunc: A subclass of ProcessStarter.
            restart: Force restarting the process if it is running.

        Raises:
            RuntimeError: If process fails to start within the required time.

        Returns:
            (PID, logfile) logfile will be seeked to the end if the
            server was running, otherwise seeked to the line after
            where the wait pattern matched.
        """
        info = self.getinfo(name)
        if not restart and not info.isrunning():
            restart = True

        if restart:
            # ensure the process is terminated first
            if info.pid is not None:
                info.terminate()

            controldir = info.controldir.ensure(dir=1)
            starter = preparefunc(controldir, self)
            args = [str(x) for x in starter.args]
            self.log.debug("%s$ %s", controldir, " ".join(args))
            stdout = open(str(info.logpath), "wb", 0)  # noqa: WPS515

            # is env still necessary? we could pass all in popen_kwargs
            kwargs = {"env": starter.env}

            popen_kwargs = {
                "stdout": stdout,
                "stderr": subprocess.STDOUT,
                # this gives the user the ability to
                # override the previous keywords if
                # desired
                **starter.popen_kwargs,
            }

            kwargs["close_fds"] = True

            # keep references of all popen
            # and info objects for cleanup
            self._info_objects.append((info, starter.terminate_on_interrupt))
            popen_instance = subprocess.Popen(  # noqa: S603
                args,
                **popen_kwargs,
                **kwargs,  # type: ignore
            )
            self._popen_instances.append(popen_instance)

            info.pid = pid = self._popen_instances[-1].pid  # noqa: WPS429
            info.pidpath.write(str(pid))
            self.log.debug("process %r started pid=%s", name, pid)  # noqa
            stdout.close()

        # keep track of all file handles so we can
        # cleanup later during teardown phase
        self._file_handles.append(info.logpath.open())

        if not restart:  # noqa: WPS504
            self._file_handles[-1].seek(0, 2)
        else:
            if not starter.wait(self._file_handles[-1]):
                raise RuntimeError(
                    f"Could not start process {name}, the specified "
                    f"log pattern was not found within {starter.max_read_lines} lines."
                )
            self.log.debug("%s process startup detected", name)

        pytest_extlogfiles = self.config.__dict__.setdefault(  # noqa: WPS609
            "_extlogfiles", {}
        )
        pytest_extlogfiles[name] = self._file_handles[-1]
        self.getinfo(name)

        return info.pid, info.logpath


@async_fixture(scope="session")
def _fixed_xprocess(request):
    """Yield session-scoped XProcess helper to manage long-running processes required for testing."""  # noqa: E501
    rootdir = getrootdir(request.config)  # noqa: DAR101,DAR301
    with _FixedXProcess(request.config, rootdir) as xproc:
        # pass in xprocess object into pytest_unconfigure
        # through config for proper cleanup during teardown
        request.config._xprocess = xproc  # noqa: WPS437
        yield xproc


def localnet_fixture(
    path: Path,
    scope: _Scope = "module",
    timeout_seconds: int = 60,
    build_cmd: Optional[str] = None,
) -> Callable:
    """Create a fixture that sets up and tears down a localnet instance with workspace programs deployed.

    Args:
        path: Path to root of the Anchor project.
        scope: Pytest fixture scope.
        timeout_seconds: Time to wait for Anchor localnet to start.
        build_cmd: Command to run before `anchor localnet`. Defaults to `anchor build`.

    Returns:
        A localnet fixture for use with pytest.
    """  # noqa: E501,D202

    @fixture(scope=scope)
    def _localnet_fixture(_fixed_xprocess):
        class Starter(ProcessStarter):
            # startup pattern
            pattern = "JSON RPC URL"
            terminate_on_interrupt = True
            # command to start process
            args = ["anchor", "localnet", "--skip-build"]
            timeout = timeout_seconds
            popen_kwargs = {
                "cwd": path,
                "start_new_session": True,
            }
            max_read_lines = 1_000
            # command to start process

        actual_build_cmd = "anchor build" if build_cmd is None else build_cmd
        subprocess.run(actual_build_cmd, cwd=path, check=True, shell=True)  # noqa: S603
        # ensure process is running and return its logfile
        logfile = _fixed_xprocess.ensure("localnet", Starter)

        yield logfile

        # clean up whole process tree afterwards
        _fixed_xprocess.getinfo("localnet").terminate()

    return _localnet_fixture


# Should figure out how to reuse localnet_fixture
# instead of copy-pasting (Pytest didn't like it).
def workspace_fixture(
    path: Union[Path, str],
    scope: _Scope = "module",
    timeout_seconds: int = 60,
    build_cmd: Optional[str] = None,
) -> Callable:
    """Create a fixture that sets up and tears down a localnet instance and returns a workspace dict.

    Equivalent to combining `localnet_fixture`, `create_workspace` and `close_workspace`.

    Args:
        path: Path to root of the Anchor project.
        scope: Pytest fixture scope.
        timeout_seconds: Time to wait for Anchor localnet to start.
        build_cmd: Command to run before `anchor localnet`. Defaults to `anchor build`.

    Returns:
        A workspace fixture for use with pytest.
    """  # noqa: E501,D202

    @async_fixture(scope=scope)
    async def _workspace_fixture(
        _fixed_xprocess,
    ) -> AsyncGenerator[dict[str, Program], None]:
        class Starter(ProcessStarter):
            # startup pattern
            pattern = "JSON RPC URL"
            terminate_on_interrupt = True
            # command to start process
            args = ["anchor", "localnet", "--skip-build"]
            timeout = timeout_seconds
            popen_kwargs = {
                "cwd": path,
                "start_new_session": True,
            }
            max_read_lines = 1_000
            # command to start process

        actual_build_cmd = "anchor build" if build_cmd is None else build_cmd
        subprocess.run(actual_build_cmd, cwd=path, check=True, shell=True)  # noqa: S603
        # ensure process is running
        _ = _fixed_xprocess.ensure("localnet", Starter)
        ws = create_workspace(path)
        yield ws
        await close_workspace(ws)

        # clean up whole process tree afterwards
        _fixed_xprocess.getinfo("localnet").terminate()

    return _workspace_fixture
