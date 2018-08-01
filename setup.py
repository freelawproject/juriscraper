import codecs
import os

try:  # for pip >= 10
    from pip._internal.req import parse_requirements
except ImportError:  # for pip <= 9.0.3
    from pip.req import parse_requirements

from setuptools import setup, find_packages

VERSION = "1.21.2"
AUTHOR = "Mike Lissner"
EMAIL = "info@free.law"
HERE = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    """
    Build an absolute path from *parts* and and return the contents of the
    resulting file.  Assume UTF-8 encoding.
    """
    with codecs.open(os.path.join(HERE, *parts), "rb", "utf-8") as f:
        return f.read()

requirements = [
    str(r.req) for r in
    parse_requirements('requirements.txt', session=False)
]

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
    packages=find_packages(exclude=['tests*']),
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
    install_requires=requirements,
    tests_require=['jsondate', 'mock', 'vcrpy'],
    include_package_data=True,
    test_suite='tests',
)
