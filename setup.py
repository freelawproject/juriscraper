import codecs
import os
import sys
import unittest

from setuptools import setup, find_packages
from setuptools.command.install import install

VERSION = "1.26.30"
AUTHOR = "Free Law Project"
EMAIL = "info@free.law"
HERE = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    """
    Build an absolute path from *parts* and and return the contents of the
    resulting file.  Assume UTF-8 encoding.
    """
    with codecs.open(os.path.join(HERE, *parts), "rb", "utf-8") as f:
        return f.read()


class TestNetwork(install):
    """Run network test only"""

    description = "run isolated tests that hit the network"

    def run(self):
        loader = unittest.defaultTestLoader
        runner = unittest.TextTestRunner(verbosity=2)
        tests = loader.discover("./tests/network")
        runner.run(tests)


class VerifyVersion(install):
    """Custom command to verify that the git tag matches our version"""

    description = "verify that the git tag matches our version"

    def run(self):
        tag = os.getenv("CIRCLE_TAG")

        if tag is None:
            sys.exit(
                "The 'verify' option is only available in tagged CircleCI container"
            )

        if tag != VERSION:
            message = (
                "Git tag: {0} does not match the version of this app: {1}"
            )
            sys.exit(message.format(tag, VERSION))


setup(
    name="juriscraper",
    description="An API to scrape American court websites for metadata.",
    license="BSD",
    url="https://github.com/freelawproject/juriscraper",
    version=VERSION,
    author=AUTHOR,
    author_email=EMAIL,
    maintainer=AUTHOR,
    maintainer_email=EMAIL,
    keywords=["scraping", "legal", "pacer"],
    long_description=read("README.rst"),
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=["tests*"]),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    install_requires=[
        "six",
        "argparse",
        "cchardet>=1.1.2",
        "certifi>=2017.4.17",
        "chardet<3.1.0,>=3.0.2",
        "cssselect",
        "feedparser",
        "geonamescache==0.20",
        "html5lib",
        "lxml==3.5.0",
        "python-dateutil==2.5.0",
        "requests==2.20.0",
        "selenium==2.53.6",
        "tldextract",
    ],
    tests_require=["jsondate", "mock", "vcrpy"],
    include_package_data=True,
    test_suite="tests.test_local",
    cmdclass={"verify": VerifyVersion, "testnetwork": TestNetwork,},
)
