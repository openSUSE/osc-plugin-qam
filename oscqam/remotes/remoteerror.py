from ..errors import ReportedError


class RemoteError(ReportedError):
    """Indicates an error while communicating with the remote service."""

    _msg = "Error accessing {url} - {ret_code}: {msg}"

    def __init__(self, url, ret_code, msg, headers, fp):
        self.url = url
        self.ret_code = ret_code
        self.msg = msg
        self.headers = headers
        self.fp = fp
        super().__init__(
            self._msg.format(url=self.url, ret_code=self.ret_code, msg=self.msg)
        )
