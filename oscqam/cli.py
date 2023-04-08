import osc.commandline


from oscqam import __version__ as strict_version


class QAMCommand(osc.commandline.OscCommand):
    """QE-Maintenace rewiew workflow helper"""

    name = "qam"
