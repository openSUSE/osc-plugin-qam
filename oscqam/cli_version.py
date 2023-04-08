import osc.commandline

from oscqam import __version__ as version


class QAMVersionCommand(osc.commandline.OscCommand):
    """Print version of osc-plugin-qam"""

    name = "version"
    parent = "QAMCommand"

    def run(self, _):
        print(version)
