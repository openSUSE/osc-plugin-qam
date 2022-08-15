from setuptools import find_packages, setup
from oscqam import __version__

package = "osc-plugin-qam"
version = __version__

setup(
    name=package,
    version=version,
    license="GPL-2.0",
    license_files=("LICENSE",),
    description="Plugin for OSC to support the workflow for the QA "
    + "maintenance department when using the new request / review osc "
    + "abstractions.",
    long_description=open("README.rst").read(),
    url="https://gitlab.suse.de/qa-maintenance/qam-oscplugin",
    install_requires=["osc", "python-dateutil", "prettytable", "requests"],
    packages=find_packages(exclude=["tests"]),
)
