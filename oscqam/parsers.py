"""Parsers to turn (external) data into a more usable formats."""

from collections import defaultdict
from itertools import dropwhile, takewhile
from json import loads
from json.decoder import JSONDecodeError
import logging
import re

from .domains import Rating


def until(snippet, lines):
    """Return lines until the snippet is matched at the beginning of the line.

    Args:
        snippet: snippet to match at the beginning of a line.
        lines: lines to return until snippet matches.

    Returns:
        A list of lines until the snippet is matched.
    """

    def condition(line):
        return not line.startswith(snippet)

    return list(takewhile(condition, lines))


def split_comma(line):
    """Parse a line from a template-log into a list.

    Args:
        line: The line to parse.

    Returns:
        A list of strings.
    """
    return [v.strip() for v in line.split(",")]


# TODO: this looks wrong, was valid maybe in beginning of SLE12
def split_products(product_line):
    """Split products into a list and strip SLE-prefix from each product.

    Args:
        product_line: The line to parse.

    Returns:
        A list of strings.
    """
    products = (
        p if p.endswith(")") else p + ")"
        for p in (l.strip() for l in product_line.split("),"))
    )
    return [re.sub("^SLE-", "", product, 1) for product in products]


def split_srcrpms(srcrpm_line):
    """Parse 'SRCRPMs' from a template-log into a list.

    Args:
        srcrpm_line: The line to parse.

    Returns:
        A list of strings.
    """
    return [xs.strip() for xs in srcrpm_line.split(",")]


def process_packages(pkgs):
    """Processes a dictionary of packages into a list of unique packages.

    Args:
        pkgs: A dictionary of packages.

    Returns:
        A list of unique packages.
    """
    ret = set()
    for key in pkgs.keys():
        for pkg in pkgs[key]:
            ret.add(pkg)
    return list(ret)


class TemplateParser:
    """Parses a template-logs header-fields.

    Attributes:
        end_marker: The marker for the end of the header.
        log: The log file content.
        metadata: The metadata file content.
    """

    end_marker = "#############################"

    def __call__(self, log, metadata):
        """Return dictionary of headers from the log-file and values.

        Args:
            log: The log file content.
            metadata: The metadata file content.

        Returns:
            A dictionary of headers and values.
        """
        if isinstance(log, bytes):
            self.log = log.decode()
        else:
            self.log = log
        if isinstance(metadata, bytes):
            self.metadata = metadata.decode()
        else:
            self.metadata = metadata

        log_entries = self._parse_headers(self._read_headers())

        data = None
        if metadata:
            try:
                data = loads(metadata)
            except JSONDecodeError:
                data = None
                pass

        if data:
            log_entries.update(self._read_metadata(data))

        return log_entries

    @staticmethod
    def _read_metadata(data):
        """Reads metadata from a dictionary.

        Args:
            data: A dictionary of metadata.

        Returns:
            A dictionary of log entries.
        """
        log_entries = {}
        log_entries["SRCRPMs"] = data.get("SRCRPMs")
        log_entries["Products"] = split_products(",".join(data.get("products")))
        log_entries["Rating"] = Rating(data.get("rating"))
        log_entries["Packages"] = process_packages(data.get("packages"))
        log_entries["Bugs"] = data.get("bugs")
        log_entries["ReviewRequestID"] = data.get("rrid")

        return log_entries

    def _read_comment(self):
        """Reads the comment from the log file.

        Returns:
            The comment as a string.
        """

        def condition(line):
            return not line.startswith(prefix)

        prefix = "comment:"
        comment = until(
            "Products:",
            dropwhile(condition, self.log.splitlines()),
        )
        return "\n".join(comment)

    def _read_headers(self):
        """Reads the template headers into a dictionary.

        Accumulates comment entry into a list.

        Returns:
            A dictionary of headers.
        """
        entries = defaultdict(list)
        comment = self._read_comment()
        log = self.log.replace(comment, "")
        entries["comment"] = [comment[len("comment:") :].strip()]

        lines = [line.strip() for line in log.splitlines() if line.strip()]
        header_end = len(until(self.end_marker, lines))
        lines = lines[:header_end]
        for line in lines:
            try:
                key, value = [l.strip() for l in line.split(":", 1)]
                entries[key].append(value)
            except ValueError:
                logging.debug("Could not parse line: %s", line)
                continue
        return entries

    def _parse_headers(self, entries):
        """Parses the header-lists into objects or strings.

        Args:
            entries: Dictionary of headers.

        Returns:
            Dictionary of header-fields.
        """
        log_entries = {}
        for key in entries:
            value = "\n".join(entries[key])
            if key == "Packages":
                log_entries[key] = split_comma(value)
            elif key == "Bugs":
                log_entries[key] = split_comma(value)
            elif key == "Products":
                log_entries[key] = split_products(value)
            elif key == "SRCRPMs":
                log_entries[key] = split_srcrpms(value)
            elif key == "Rating":
                log_entries[key] = Rating(value)
            elif key == "comment" and value == "NONE":
                log_entries[key] = None
            else:
                log_entries[key] = value
        return log_entries
