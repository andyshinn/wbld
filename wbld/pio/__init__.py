import os

from sh import Command

PIO_COMMAND_NAME = "pio"

current_env = os.environ.copy()
current_env["PLATFORMIO_DISABLE_COLOR"] = "true"
current_env["CI"] = "true"


class PioCommand:
    def __new__(cls, out=None, err_to_out=True, return_command=False):
        return Command(PIO_COMMAND_NAME).bake(
            _return_cmd=return_command,
            _out=out,
            _err_to_out=err_to_out,
            _env=current_env,
        )
