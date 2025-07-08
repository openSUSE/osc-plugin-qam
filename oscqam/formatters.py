"""Formatters used to generate nice looking output."""

import fcntl
import os
import platform
import struct
import sys
import termios

import prettytable

from .fields import ReportField


def terminal_dimensions(fd=None):
    """Return dimensions of the terminal.

    :param fd: filedescriptor of the terminal.
    :type fd: int.

    :returns: (int, int) tuple with rows and columns.
    """
    if not fd:
        if not sys.stdout.isatty():
            return (0, 0)
        fd = sys.stdout.fileno()
    dim = fcntl.ioctl(fd, termios.TIOCGWINSZ, "0000")
    rows, columns = struct.unpack("hh", dim)
    if rows == 0 and columns == 0:
        try:
            rows, columns = (int(os.getenv(v)) for v in ["LINES", "COLUMNS"])
        except Exception:
            pass
    return rows, columns


def os_lineseps(value, target=None):
    """Adjust the lineseperators in value to match the ones used by the current
    system.

    :param value: The text to modify
    :type value: str

    :param target: The system identifier whose line-endings should be
    substituted.
    :type target: str

    """

    def _windows_to_linux(value):
        return value.replace("\r\n", "\n")

    def _linux_to_windows(value):
        if "\r\n" in value:
            # Seems there are already the correct lines present
            return value
        return value.replace("\n", "\r\n")

    target = target if target else platform.system()

    if target == "Linux":
        value = _windows_to_linux(value)
    elif target == "Windows":
        value = _linux_to_windows(value)
    else:
        return value
    return value


class Formatter:
    """Base class for specialised formatters."""

    def __init__(self, listsep, formatters={}):
        """
        :param listsep: Seperator for lists.
        :type listsep: str

        :param formatters: Alternative formatter to use for certain keys.
        :type formatters: dict(ReportField, formatter)
        """
        self.listsep = listsep
        self._formatters = {
            ReportField.bugs: self.list_formatter,
            ReportField.comments: self.comment_formatter,
            ReportField.package_streams: self.list_formatter,
            ReportField.products: self.list_formatter,
            ReportField.srcrpms: self.list_formatter,
            ReportField.unassigned_roles: self.list_formatter,
            ReportField.assigned_roles: self.list_formatter,
        }
        for formatter in formatters:
            self._formatters[formatter] = formatters[formatter]
        self.default_format = str

    def output(self, keys, reports):
        """Format the reports for output based on the keys.

        :param keys: The fields to output for each report.
        :type keys: [:class:`oscqam.fields.ReportField`]

        :param reports: The reports to format for outputting.
        :type reports: [:class:`oscqam.actions.Report`]

        :returns: Value that can be passed to print.
        """
        pass

    def formatter(self, key):
        return self._formatters.get(key, self.default_format)

    def comment_formatter(self, value):
        return self.listsep.join([os_lineseps(str(v)) for v in value])

    def list_formatter(self, value):
        return self.listsep.join(value)


class VerboseOutput(Formatter):
    """Formats reports in a blocks:

    <key>: <value>+
    --------------
    """

    def __init__(self):
        super().__init__(",")
        self.record_sep = "-" * terminal_dimensions()[1]

    def output(self, keys, reports):
        output = []
        str_template = "{{0:{length}s}}: {{1}}".format(
            length=max([len(str(k)) for k in keys])
        )
        for report in reports:
            values = []
            for key in keys:
                formatter = self.formatter(key)
                value = formatter(report.value(key))
                values.append(str_template.format(str(key), value))
            output.append(os.linesep.join(values))
            output.append(self.record_sep)
        return os.linesep.join(output)


class TabularOutput(Formatter):
    """Formats reports in a table

    +--------+--------+
    | <key1> | <key2> |
    +--------+--------+
    | <v1>   | <v2>   |
    +--------+--------+
    """

    def __init__(self):
        super().__init__(os.linesep, {ReportField.comments: self.comment_formatter})

    def output(self, keys, reports):
        table_formatter = prettytable.PrettyTable(keys)
        table_formatter.align = "l"
        table_formatter.border = True
        for report in reports:
            values = []
            for key in keys:
                formatter = self.formatter(key)
                value = formatter(report.value(key))
                values.append(value)
            table_formatter.add_row(values)
        return table_formatter
