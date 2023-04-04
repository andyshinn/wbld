from sh import Command

PIO_COMMAND_NAME = "pio"


class PioCommand:
    def __new__(cls, out=None, err_to_out=True):
        return Command(PIO_COMMAND_NAME).bake(
            _out=out, _err_to_out=err_to_out, _env={"PLATFORMIO_DISABLE_COLOR": "true", "CI": "true"}
        )
