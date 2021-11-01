from subprocess import STDOUT, Popen
import signal
import os
from pytest import fixture
from xprocess import XProcessInfo, XProcess
from pytest_xprocess import getrootdir


class FixedXProcessInfo(XProcessInfo):
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


class FixedXProcess(XProcess):
    def getinfo(self, name):
        """Return Process Info for the given external process."""

        return FixedXProcessInfo(self.rootdir, name)

    def ensure(self, name, preparefunc, restart=False):
        """Return (PID, logfile) from a newly started or already running process.
        @param name: name of the external process, used for caching info
                     across test runs.
        @param preparefunc:
                A subclass of ProcessStarter.
        @param restart: force restarting the process if it is running.
        @return: (PID, logfile) logfile will be seeked to the end if the
                 server was running, otherwise seeked to the line after
                 where the waitpattern matched."""

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
                "stderr": STDOUT,
                # this gives the user the ability to
                # override the previous keywords if
                # desired
                **starter.popen_kwargs,
            }

            kwargs["close_fds"] = True

            # keep references of all popen
            # and info objects for cleanup
            self._info_objects.append((info, starter.terminate_on_interrupt))
            self._popen_instances.append(Popen(args, **popen_kwargs, **kwargs))

            info.pid = pid = self._popen_instances[-1].pid
            info.pidpath.write(str(pid))
            self.log.debug("process %r started pid=%s", name, pid)
            stdout.close()

        # keep track of all file handles so we can
        # cleanup later during teardown phase
        self._file_handles.append(info.logpath.open())

        if not restart:
            self._file_handles[-1].seek(0, 2)
        else:
            if not starter.wait(self._file_handles[-1]):
                raise RuntimeError(
                    "Could not start process {}, the specified "
                    "log pattern was not found within {} lines.".format(
                        name, starter.max_read_lines
                    )
                )
            self.log.debug("%s process startup detected", name)

        pytest_extlogfiles = self.config.__dict__.setdefault("_extlogfiles", {})
        pytest_extlogfiles[name] = self._file_handles[-1]
        self.getinfo(name)

        return info.pid, info.logpath


@fixture(scope="session")
def fixed_xprocess(request):
    """yield session-scoped XProcess helper to manage long-running
    processes required for testing."""

    rootdir = getrootdir(request.config)
    with FixedXProcess(request.config, rootdir) as xproc:
        # pass in xprocess object into pytest_unconfigure
        # through config for proper cleanup during teardown
        request.config._xprocess = xproc
        yield xproc
