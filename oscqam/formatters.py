"""Formatters used to generate nice looking output.
"""
import os

import prettytable

from .fields import ReportField


class Formatter(object):
    """Base class for specialised formatters.
    """
    def __init__(self, listsep, formatters = {}):
        """
        :param listsep: Seperator for lists.
        :type listsep: str

        :param formatters: Alternative formatter to use for certain keys.
        :type formatters: dict(ReportField, formatter)
        """
        self.listsep = listsep
        self._formatters = {
            ReportField.bugs: self.list_formatter,
            ReportField.package_streams: self.list_formatter,
            ReportField.products: self.list_formatter,
            ReportField.srcrpms: self.list_formatter,
        }
        for formatter in formatters:
            self._formatters[formatter] = formatters[formatter]
        self.default_format = str

    def output(keys, reports):
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

    def list_formatter(self, value):
        return self.listsep.join(value)


class VerboseOutput(Formatter):
    """Formats reports in a blocks:

    <key>: <value>+
    --------------
    """
    def __init__(self):
        super(VerboseOutput, self).__init__(',')

    def output(self, keys, reports):
        length = max([len(str(k)) for k in keys])
        output = []
        str_template = "{{0:{length}s}}: {{1}}".format(length = length)
        for report in reports:
            values = []
            for key in keys:
                formatter = self.formatter(key)
                value = formatter(report.value(key))
                values.append(str_template.format(str(key), value))
            output.append(os.linesep.join(values))
            output.append('----------------------------')
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
        super(TabularOutput, self).__init__(
            os.linesep,
            {ReportField.comments:  self.comment_formatter}
        )
        pass

    def output(self, keys, reports):
        table_formatter = prettytable.PrettyTable(keys)
        table_formatter.align = 'l'
        table_formatter.border = True
        for report in reports:
            values = []
            for key in keys:
                formatter = self.formatter(key)
                value = formatter(report.value(key))
                values.append(value)
            table_formatter.add_row(values)
        return table_formatter
