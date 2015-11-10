import os
import prettytable
from oscqam.fields import ReportFields


def output_list(sep, value):
    """Join lists on the given separator and return strings unaltered.

    :param sep: Separator to join a list on.
    :type list_transform: str

    :param value: Output value.
    :type value: :class:`str} or list(L{str`)

    :return: str
    """
    return sep.join(value) if isinstance(value, list) else value


def verbose_output(data, keys):
    """Output the data in verbose format."""
    length = max([len(str(k)) for k in keys])
    output = []
    str_template = "{{0:{length}s}}: {{1}}".format(length = length)
    for row in data:
        for i, datum in enumerate(row):
            key = keys[i]
            datum = output_list(", ", datum)
            output.append(str_template.format(key, datum))
        output.append("-----------------------")
    return os.linesep.join(output)


def tabular_output(data, headers):
    """Format data for output in a table.

    Args:
        - headers: Headers of the table.
        - data: The data to be printed as a table. The data is expected to be
                provided as a list of lists: [[row1], [row2], [row3]]
    """
    table_formatter = prettytable.PrettyTable(headers)
    table_formatter.align = 'l'
    table_formatter.border = True
    for row in data:
        row = [output_list(os.linesep, value) for value in row]
        table_formatter.add_row(row)
    return table_formatter
