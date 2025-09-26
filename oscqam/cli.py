"""OSC-QAM command line interface."""

import osc.commandline


from oscqam import __version__ as strict_version


class QAMCommand(osc.commandline.OscCommand):
    """QE-Maintenace rewiew workflow helper.

    This class provides the main entry point for the qam command.

    Attributes:
        name: The name of the command.

    """

    name = "qam"

    def run(self, _):
        """Run the command.

        This method is called when the command is executed.

        Args:
            _: The arguments passed to the command.

        """
        pass
