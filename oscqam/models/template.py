from ..errors import TemplateNotFoundError
from ..errors import TestResultMismatchError
from ..errors import TestPlanReviewerNotSetError
from ..parsers import TemplateParser
from ..utils import https


def get_testreport_web(log_path):
    """Load the template belonging to the request from
    https://qam.suse.de/testreports/.

    :param request: The request this template is associated with.
    :type request: :class:`oscqam.models.Request`

    :return: Content of the log-file as string.

    """
    report = https(log_path)
    if not report:
        raise TemplateNotFoundError(log_path)
    return report.read()


class Template:
    """Facade to web-based templates."""

    STATUS_SUCCESS = 0
    STATUS_FAILURE = 1
    STATUS_UNKNOWN = 2
    # Machine readable reports
    base_url = "https://qam2.suse.de/testreports/"
    # Human readable reports
    fancy_base_url = "https://qam2.suse.de/reports/"

    def __init__(self, request, tr_getter=get_testreport_web, parser=TemplateParser()):
        """Create a template from the given request.

        :param request: The request the template is associated with.
        :type request: :class:`oscqam.models.Request`.

        :param tr_getter: Function that can load the template's log file based
                          on the request. Will default to loading testreports
                          from http://qam.suse.de.

        :type tr_getter: Function: :class:`oscqam.models.Request` ->
                         :class:`str`

        :param parser: Class that can parse the data returned by tr_getter.
        :type parser: :class:`oscqam.parsers.TemplateParser`

        """
        self._request = request
        self._log_path = self.url()
        self.log_entries = parser(tr_getter(self._log_path))

    def failed(self):
        """Assert that this template is from a failed test.

        If the template says the test did not fail this will raise an error.

        """
        if self.status != Template.STATUS_FAILURE:
            raise TestResultMismatchError("FAILED", self._log_path)

    def passed(self):
        """Assert that this template is from a successful test.

        :raises: :class:`oscqam.models.TestResultMismatchError` if template is
            not set to PASSED.
        """
        if self.status != Template.STATUS_SUCCESS:
            raise TestResultMismatchError("PASSED", self._log_path)

    def testplanreviewer(self):
        """Assert that the Test Plan Reviewer for the template is set.

        :raises: :class:`oscqam.models.TestPlanReviewerNotSetError` if reviewer
            is not set or empty.
        """
        reviewer = self.log_entries.get("Test Plan Reviewer", "")
        reviewer = self.log_entries.get("Test Plan Reviewers", reviewer)
        reviewer = reviewer.strip()
        if reviewer:
            return reviewer
        raise TestPlanReviewerNotSetError(self._log_path)

    @property
    def status(self):
        summary = self.log_entries["SUMMARY"]
        if summary.upper() == "PASSED":
            return Template.STATUS_SUCCESS
        elif summary.upper() == "FAILED":
            return Template.STATUS_FAILURE
        return Template.STATUS_UNKNOWN

    def url(self):
        """Return URL to machine readable version of the report."""
        return "{base}{prj}:{reqid}/log".format(
            base=self.base_url, prj=self._request.src_project, reqid=self._request.reqid
        )

    def fancy_url(self):
        """Return URL to human readable version of the report."""
        return "{base}{prj}:{reqid}/log".format(
            base=self.fancy_base_url,
            prj=self._request.src_project,
            reqid=self._request.reqid,
        )
