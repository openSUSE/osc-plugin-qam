"""Parsers to turn (external) data into a more usable formats.
"""
from collections import defaultdict
import csv
from itertools import takewhile, dropwhile
import logging
import re

from .domains import Rating, UnknownPriority


def until(snippet, lines):
    """Return lines until the snippet is matched at the beginning of the line.

    :param snippet: snippet to match at the beginning of a line.
    :type snippet: str

    :param lines: lines to return until snippet matches.
    :type lines: [str]
    """
    return list(takewhile(lambda line: not line.startswith(snippet), lines))


def split_comma(line):
    """Parse a line from a template-log into a list.

    :type package_line: str

    :returns: [str]

    """
    return [v.strip() for v in line.split(",")]


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

    def __call__(self, log):
        """Return dictionary of headers from the log-file and values.

        :returns: {str: object}
        """
        self.log = log
        return self._parse_headers(self._read_headers())

    def _read_comment(self):
        prefix = 'comment:'
        comment = until("Products:",
                        dropwhile(lambda line: not line.startswith(prefix),
                                  self.log.splitlines()))
        return '\n'.join(comment)

    def _read_headers(self):
        """Reads the template headers into a dictionary.

        Accumulates comment entry into a list.
        """
        entries = defaultdict(list)
        comment = self._read_comment()
        log = self.log.replace(comment, "")
        entries['comment'] = [comment[len('comment:'):].strip()]

        lines = [line.strip() for line in log.splitlines() if line.strip()]
        header_end = len(until(self.end_marker, lines))
        lines = lines[:header_end]
        for line in lines:
            try:
                key, value = map(str.strip, line.split(":", 1))
                entries[key].append(value)
            except ValueError:
                logging.debug("Could not parse line: %s", line)
                continue
        return entries

    def _parse_headers(self, entries):
        """Parses the header-lists into objects or strings.

        :param entries: Dictionary of headers.
        :type entries: {str: list}

        :returns: Dictionary of header-fields: {str: object}
        """
        log_entries = {}
        for key in entries:
            value = '\n'.join(entries[key])
            if key == 'Packages':
                log_entries[key] = split_comma(value)
            elif key == 'Bugs':
                log_entries[key] = split_comma(value)
            elif key == 'Products':
                log_entries[key] = split_products(value)
            elif key == "SRCRPMs":
                log_entries[key] = split_srcrpms(value)
            elif key == "Rating":
                log_entries[key] = Rating(value)
            elif key == "comment" and value == 'NONE':
                log_entries[key] = None
            else:
                log_entries[key] = value
        return log_entries
