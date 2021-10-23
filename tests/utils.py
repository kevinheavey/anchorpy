from typing import Callable
from pytest import fixture
from xprocess import ProcessStarter


def get_localnet(path, scope="module", timeout_seconds=300) -> Callable:
    @fixture(scope=scope)
    def localnet_fixture(fixed_xprocess):
        class Starter(ProcessStarter):
            # startup pattern
            pattern = "JSON RPC URL"
            terminate_on_interrupt = True
            # command to start process
            args = ["anchor", "localnet"]
            timeout = timeout_seconds
            popen_kwargs = {
                "cwd": path,
                "start_new_session": True,
            }
            max_read_lines = 1_000
            # command to start process

        # ensure process is running and return its logfile
        logfile = fixed_xprocess.ensure("localnet", Starter)

        yield logfile

        # clean up whole process tree afterwards
        fixed_xprocess.getinfo("localnet").terminate()

    return localnet_fixture
