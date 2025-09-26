"""Provides an exception for remote errors."""

from ..errors import ReportedError


class RemoteError(ReportedError):
    """Indicates an error while communicating with the remote service.

    Attributes:
        url: The URL that was accessed.
        ret_code: The return code of the request.
        msg: The error message.
        headers: The headers of the response.
        fp: The file pointer of the response.
    """

    _msg = "Error accessing {url} - {ret_code}: {msg}"

    def __init__(self, url, ret_code, msg, headers, fp):
        """Initializes a RemoteError.

        Args:
            url: The URL that was accessed.
            ret_code: The return code of the request.
            msg: The error message.
            headers: The headers of the response.
            fp: The file pointer of the response.
        """
        self.url = url
        self.ret_code = ret_code
        self.msg = msg
        self.headers = headers
        self.fp = fp
        super().__init__(
            self._msg.format(url=self.url, ret_code=self.ret_code, msg=self.msg)
        )
