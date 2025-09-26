"""Provides a class for interacting with test report templates."""

from ..errors import TemplateNotFoundError, TestResultMismatchError
from ..parsers import TemplateParser
from ..utils import https


def get_testreport_web(log_path, metadata_path):
    """Load the template belonging to the request from
    https://qam.suse.de/testreports/.

    Args:
        log_path: The path to the log file.
        metadata_path: The path to the metadata file.

    Returns:
        A tuple containing the content of the log file and metadata file as
        strings.

    Raises:
        TemplateNotFoundError: If the log file cannot be found.
    """
    report = https(log_path)
    if not report:
        raise TemplateNotFoundError(log_path)

    metadata = https(metadata_path)

    if not metadata:
        metadata = None
    else:
        metadata = metadata.read()

    report = report.read()

    return (report, metadata)


class Template:
    """Facade to web-based templates.

    Attributes:
        STATUS_SUCCESS: An integer representing a successful test status.
        STATUS_FAILURE: An integer representing a failed test status.
        STATUS_UNKNOWN: An integer representing an unknown test status.
        base_url: The base URL for machine-readable reports.
        fancy_base_url: The base URL for human-readable reports.
        log_entries: A dictionary of log entries from the template.
    """

    STATUS_SUCCESS = 0
    STATUS_FAILURE = 1
    STATUS_UNKNOWN = 2
    # Machine readable reports
    base_url = "https://qam.suse.de/testreports/"
    # Human readable reports
    fancy_base_url = "https://qam.suse.de/reports/"

    def __init__(self, request, tr_getter=get_testreport_web, parser=TemplateParser()):
        """Create a template from the given request.

        Args:
            request: The request the template is associated with.
            tr_getter: Function that can load the template's log file based
                on the request. Will default to loading testreports
                from http://qam.suse.de.
            parser: Class that can parse the data returned by tr_getter.
        """
        self._request = request
        self.log_entries = parser(*tr_getter(self.url, self.metadata_url))

    def failed(self):
        """Assert that this template is from a failed test.

        If the template says the test did not fail this will raise an error.

        Raises:
            TestResultMismatchError: If the test did not fail.
        """
        if self.status != Template.STATUS_FAILURE:
            raise TestResultMismatchError("FAILED", self.url)

    def passed(self):
        """Assert that this template is from a successful test.

        Raises:
            TestResultMismatchError: if template is not set to PASSED.
        """
        if self.status != Template.STATUS_SUCCESS:
            raise TestResultMismatchError("PASSED", self.url)

    @property
    def status(self):
        """The status of the test."""
        summary = self.log_entries["SUMMARY"]
        if summary.upper() == "PASSED":
            return Template.STATUS_SUCCESS
        elif summary.upper() == "FAILED":
            return Template.STATUS_FAILURE
        return Template.STATUS_UNKNOWN

    @property
    def url(self):
        """Return URL to machine readable version of the report."""
        return f"{self.base_url}{self._request.src_project_to_rrid}:{self._request.reqid}/log"

    @property
    def metadata_url(self):
        """The URL to the metadata file."""
        return f"{self.base_url}{self._request.src_project_to_rrid}:{self._request.reqid}/metadata.json"

    @property
    def fancy_url(self):
        """Return URL to human readable version of the report."""
        return f"{self.fancy_base_url}{self._request.src_project_to_rrid}:{self._request.reqid}/log"
