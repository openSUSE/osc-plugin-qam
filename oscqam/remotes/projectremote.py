"""Provides a class for interacting with projects on the remote."""

from ..models import Attribute


class ProjectRemote:
    """Interacts with projects on the remote.

    Attributes:
        create_body: The XML body for creating an attribute.
        endpoint: The API endpoint for projects.
        remote: A remote facade.
    """

    create_body = """<attributes>
    {attribute}
    </attributes>
    """

    endpoint = "source"

    def __init__(self, remote):
        """Initializes a ProjectRemote.

        Args:
            remote: A remote facade.
        """
        self.remote = remote

    def get_attribute(self, project, attribute_name):
        """Return the attribute value for the given project.

        Args:
            project: The name of the project.
            attribute_name: The name of the attribute to get.

        Returns:
            An Attribute object.
        """
        url = f"{self.endpoint}/{project}/_attribute/{attribute_name}"
        return Attribute.parse(self.remote, self.remote.get(url))

    def set_attribute(self, project, attribute):
        """Sets an attribute for a project.

        Args:
            project: The name of the project.
            attribute: The Attribute object to set.
        """
        endpoint = f"{self.endpoint}/{project}/_attribute/{attribute.namespace}:{attribute.name}"
        self.remote.post(endpoint, self.create_body.format(attribute=attribute.xml()))
