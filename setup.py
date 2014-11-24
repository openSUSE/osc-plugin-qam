from setuptools import setup

package = 'oscqam'
version = '0.1'

setup(
    name=package,
    version=version,
    description='Plugin for OSC to support the workflow for the QA ' +
    'maintenance department when using the new request / review osc ' +
    'abstractions.',
    long_description=open("README.txt").read(),
    url='https://wiki.innerweb.novell.com/index.php/RD-OPS_QA/Maintenance/osc-for-qam',
    install_requires=['osc'],
    packages=['oscqam'],
)
