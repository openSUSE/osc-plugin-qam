"""Provides a class for interacting with requests on the remote."""

from ..models import Request, RequestFilter


class RequestRemote:
    """Facade for retrieving Request objects from the buildservice API.

    Attributes:
        remote: A remote facade.
        endpoint: The API endpoint for requests.
    """

    def __init__(self, remote):
        """Initializes a RequestRemote.

        Args:
            remote: A remote facade.
        """
        self.remote = remote
        self.endpoint = "request"

    def _group_xpath(self, groups, state):
        """Builds an XPath expression to search for reviews by group and state.

        Args:
            groups: A list of groups to search for.
            state: The state of the review to search for.

        Returns:
            An XPath expression as a string.
        """

        def get_group_name(group):
            if isinstance(group, str):
                return group
            return group.name

        xpaths = []
        for group in groups:
            name = get_group_name(group)
            xpaths.append(
                "(review[@by_group='{0}' and @state='{1}'])".format(name, state)
            )
        xpath = " or ".join(xpaths)
        return "( {0} )".format(xpath)

    def _get_groups(self, groups, state, **kwargs):
        """Gets requests for a list of groups with a given state.

        Args:
            groups: A list of groups to get requests for.
            state: The state of the reviews to search for.
            **kwargs: Additional parameters for the search.

        Returns:
            A list of Request objects.
        """
        if not kwargs:
            kwargs = {"withfullhistory": "1"}
        xpaths = ["(state/@name='{0}')".format("review")]
        xpaths.append(self._group_xpath(groups, state))
        xpath = " and ".join(xpaths)
        params = {"match": xpath, "withfullhistory": "1"}
        params.update(kwargs)
        search = "/".join(["search", self.endpoint])
        requests = Request.parse(self.remote, self.remote.get(search, params))
        return RequestFilter.for_remote(self.remote).maintenance_requests(requests)

    def open_for_groups(self, groups, **kwargs):
        """Will return all requests of the given type for the given groups
        that are still open: the state of the review should be in state 'new'.

        Args:
            groups: The groups that should be used.
            **kwargs: additional parameters for the search.

        Returns:
            A list of open Request objects.
        """
        return self._get_groups(groups, "new", **kwargs)

    def review_for_groups(self, groups, **kwargs):
        """Will return all requests for the given groups that are in review.

        As there is no 'review' state, the state is determined as a group being
        'accepted', while a user is in state 'new' for that group.

        Args:
            groups: The groups that should be used.
            **kwargs: additional parameters for the search.

        Returns:
            A list of Request objects in review.
        """
        requests = self._get_groups(groups, "accepted", **kwargs)
        return [request for request in requests if request.assigned_roles]

    def for_user(self, user):
        """Will return all requests for the user if they are part of a
        SUSE:Maintenance project.

        Args:
            user: The user to get requests for.

        Returns:
            A list of Request objects.
        """
        params = {
            "user": user.login,
            "view": "collection",
            "states": "new,review",
            "withfullhistory": "1",
        }
        requests = Request.parse(self.remote, self.remote.get(self.endpoint, params))
        return RequestFilter.for_remote(self.remote).maintenance_requests(requests)

    def for_incident(self, incident):
        """Return all requests for the given incident that have a qam-group
        as reviewer.

        Args:
            incident: The incident to get requests for.

        Returns:
            A list of Request objects.
        """
        params = {"project": incident, "view": "collection", "withfullhistory": "1"}
        requests = Request.parse(self.remote, self.remote.get(self.endpoint, params))
        return [
            request
            for request in requests
            if any([r.reviewer.is_qam_group() for r in request.review_list()])
        ]

    def by_id(self, req_id):
        """Gets a request by its ID.

        Args:
            req_id: The ID of the request to get.

        Returns:
            A Request object.
        """
        req_id = Request.parse_request_id(req_id)
        endpoint = "/".join([self.endpoint, req_id])
        req = Request.parse(
            self.remote, self.remote.get(endpoint, {"withfullhistory": 1})
        )
        return req[0]
