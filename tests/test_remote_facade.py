from oscqam.models.xmlfactorymixin import XmlFactoryMixin

from .utils import load_fixture


def test_parse_flat_xml():
    xml = load_fixture("flat.xml")
    persons = XmlFactoryMixin.parse(None, xml, "person")
    john = persons[0]
    assert john.firstname == "John"
    assert john.lastname == "Smith"


def test_parse_nested_xml():
    xml = load_fixture("nested.xml")
    persons = XmlFactoryMixin.parse(None, xml, "person")
    john = persons[0]
    assert john.firstname == "John"
    assert john.lastname == "Smith"
    assert john.address.streetname == "Arcadiaavenue"
    assert john.address.streetnumber == "1"


def test_parse_nested_xml_multiple():
    xml = load_fixture("nested_multi.xml")
    persons = XmlFactoryMixin.parse(None, xml, "person")
    john = persons[0]
    assert john.firstname == "John"
    assert john.lastname == "Smith"
    assert len(john.address) == 2
    assert john.address[0].streetname == "Arcadiaavenue"
    assert john.address[0].streetnumber == "1"
    assert john.address[1].streetname == "Rassilonblvd"
    assert john.address[1].streetnumber == "2"


def test_parse_attributes():
    xml = load_fixture("attributes.xml")
    persons = XmlFactoryMixin.parse(None, xml, "person")
    john = persons[0]
    assert john.firstname == "John"
    assert john.lastname == "Smith"


def test_parse_multi_attributes():
    xml = load_fixture("attributes_multi.xml")
    persons = XmlFactoryMixin.parse(None, xml, "person")
    john = persons[0]
    assert john.firstname == "John"
    assert john.lastname == "Smith"
    clara = persons[1]
    assert clara.firstname == "Clara"
    assert clara.lastname == "Oswald"


def test_parse_nested_and_attributes():
    xml = load_fixture("nested_attributes.xml")
    persons = XmlFactoryMixin.parse(None, xml, "person")
    john = persons[0]
    assert john.id == "1"
    assert john.firstname == "John"
    assert john.lastname == "Smith"
    assert john.address.main == "True"
    assert john.address.streetname == "Arcadiaavenue"
    assert john.address.streetnumber == "1"


def test_remote_facade_get_and_post(monkeypatch):
    from io import BytesIO
    from urllib.error import HTTPError

    import osc.core
    import pytest

    from oscqam.remotes import RemoteError
    from oscqam.remotes.remotefacade import RemoteFacade

    class MockResponse:
        def __init__(self, data):
            self.data = data
            self.status = 200

        def read(self):
            return self.data

    def mock_http_GET(url):
        if "error" in url:
            raise HTTPError(url, 500, "Internal Server Error", {}, BytesIO(b""))
        return MockResponse(b"<flat>flat_response</flat>")

    def mock_http_POST(url, data=None):
        if "error" in url:
            raise HTTPError(url, 500, "Internal Server Error", {}, BytesIO(b""))
        return MockResponse(b"<post>post_response</post>")

    def mock_http_DELETE(url):
        if "error" in url:
            raise HTTPError(url, 500, "Internal Server Error", {}, BytesIO(b""))
        return MockResponse(b"<delete>delete_response</delete>")

    monkeypatch.setattr(osc.core, "http_GET", mock_http_GET)
    monkeypatch.setattr(osc.core, "http_POST", mock_http_POST)
    monkeypatch.setattr(osc.core, "http_DELETE", mock_http_DELETE)

    facade = RemoteFacade("https://api.example.com")

    # 1. Test delete
    res = facade.delete("delete_endpoint")
    assert res == b"<delete>delete_response</delete>"

    # 2. Test get with params
    res = facade.get("get_endpoint", params={"q": "test"})
    assert res == b"<flat>flat_response</flat>"

    # 3. Test post
    res = facade.post("post_endpoint", data=b"data")
    assert res == b"<post>post_response</post>"

    # 4. Test HTTPError handling in get
    with pytest.raises(RemoteError):
        facade.get("error_endpoint")

    # 5. Test HTTPError handling in post
    with pytest.raises(RemoteError):
        facade.post("error_endpoint")

    # 6. Test HTTPError handling in delete
    with pytest.raises(HTTPError):
        facade.delete("error_endpoint")
