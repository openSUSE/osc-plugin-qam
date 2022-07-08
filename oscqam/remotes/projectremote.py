from ..models import Attribute


class ProjectRemote:
    create_body = """<attributes>
    {attribute}
    </attributes>
    """

    endpoint = "source"

    def __init__(self, remote):
        self.remote = remote

    def get_attribute(self, project, attribute_name):
        """Return the attribute value for the given project."""
        url = f"{self.endpoint}/{project}/_attribute/{attribute_name}"
        return Attribute.parse(self.remote, self.remote.get(url))

    def set_attribute(self, project, attribute):
        endpoint = f"{self.endpoint}/{project}/_attribute/{attribute.namespace}:{attribute.name}"
        self.remote.post(endpoint, self.create_body.format(attribute=attribute.xml()))
