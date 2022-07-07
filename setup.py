from setuptools import setup
from oscqam import __version__

package = 'python-oscqam'
version = __version__

setup(
    name=package,
    version=version,
    description='Plugin for OSC to support the workflow for the QA ' +
    'maintenance department when using the new request / review osc ' +
    'abstractions.',
    long_description=open("README.rst").read(),
    url='https://gitlab.suse.de/qa-maintenance/qam-oscplugin',
    install_requires=['osc', 'python-dateutil', 'prettytable'],
    packages=['oscqam'],
)
