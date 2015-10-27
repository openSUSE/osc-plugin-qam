"""Parsers to turn (external) data into a more usable formats.
"""
import logging
import re

from .domains import Rating


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def until(snippet, lines):
    """Return lines until the snippet is matched at the beginning of the line.

    :param snippet: snippet to match at the beginning of a line.
    :type snippet: str

    :param lines: lines to return until snippet matches.
    :type lines: [str]
    """
    return list(takewhile(lambda line: not line.startswith(snippet), lines))


def split_packages(package_line):
    """Parse a 'Packages' line from a template-log into a list of individual
    packages.

    :type package_line: str

    :returns: [str]

    """
    return [v.strip() for v in package_line.split(",")]


def split_products(product_line):
    """Split products into a list and strip SLE-prefix from each product.

    :type product_line: str

    :returns: [str]
    """
    products = map(str.strip, product_line.split("),"))
    products = [p if p.endswith(")") else p + ")" for p in products]
    return [re.sub("^SLE-", "", product, 1) for product in products]


def split_srcrpms(srcrpm_line):
    """Parse 'SRCRPMs' from a template-log into a list.

    :type srcrpm_line: str

    :returns: [str]
    """
    return map(str.strip, srcrpm_line.split(","))


class TemplateParser(object):
    """Parses a template-logs header-fields.
    """
    end_marker = '#############################'

    def __init__(self, log):
        """
        :param log: The log-file contents.
        :type log: str
        """
        self.log = log

    def __call__(self):
        """Return dictionary of headers from the log-file and values.

        :returns: {str: object}
        """
        return self._parse_headers(self._read_headers())

    def parse_log(self):
        """Parses the header of the log into a dictionary.

        """
        log_entries = {}
        for line in self.log.splitlines():
            # We end parsing at the results block.
            # We only need the header information.
            if "Test results by" in line:
                break
            line = line.strip()
            if not line or ":" not in line:
                continue
            key, value = map(str.strip, line.split(":", 1))
            if key == 'Packages':
                value = split_packages(value)
            elif key == 'Products':
                value = split_products(value)
            elif key == "SRCRPMs":
                value = split_srcrpms(value)
            elif key == "Rating":
                value = Rating(value)
            else:
                value = value.strip()
            log_entries[key] = value
        return log_entries
