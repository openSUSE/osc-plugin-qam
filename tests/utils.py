from collections import OrderedDict
from pathlib import Path

from oscqam.parsers import TemplateParser

path = Path(__file__).parent / "fixtures"


def load_fixture(name):
    file = path / name
    return file.read_text()


def create_template_data(**data):
    """Adds missing keys and values to the template data."""
    data = OrderedDict(**data)
    if "comment" not in data.keys():
        data["comment"] = ""
    if "Products" not in data.keys():
        data["Products"] = "none"
    if TemplateParser.end_marker not in data.keys():
        data[TemplateParser.end_marker] = ""
    return "\n".join(": ".join(v) for v in (zip(data.keys(), data.values())))
