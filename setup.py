import codecs
import os
import re

from setuptools import setup, find_packages


####################################################################

NAME = "juriscraper"
# PACKAGES = find_packages(exclude=["tests*"])
PACKAGES = find_packages()
META_PATH = os.path.join("__init__.py")
KEYWORDS = ["scraping", "legal"]
CLASSIFIERS = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "Natural Language :: English",
    "License :: OSI Approved :: BSD License",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 2.6",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: Implementation :: CPython",
    "Programming Language :: Python :: Implementation :: PyPy",
    "Topic :: Software Development :: Libraries :: Python Modules",
]
INSTALL_REQUIRES = [
    'argparse', #==1.2.1
    'cchardet',
    'certifi',
    'chardet',
    'geonamescache', #==0.20
    'lxml', #==3.0.1
    'pkginfo', #==1.2.1
    'python-dateutil', #==1.5
    'requests', #==2.2.1
    'selenium', #==2.43.0
    'twine', #==1.6.1
    'unicode-nazi', #==1.1
    'wheel', #==0.26.0
    'wsgiref' #==0.1.2
]

###################################################################

HERE = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    """
    Build an absolute path from *parts* and and return the contents of the
    resulting file.  Assume UTF-8 encoding.
    """
    with codecs.open(os.path.join(HERE, *parts), "rb", "utf-8") as f:
        return f.read()


META_FILE = read(META_PATH)


def find_meta(meta):
    """
    Extract __*meta*__ from META_FILE.
    """
    meta_match = re.search(
        r"^__{meta}__ = ['\"]([^'\"]*)['\"]".format(meta=meta),
        META_FILE, re.M
    )
    if meta_match:
        return meta_match.group(1)
    raise RuntimeError("Unable to find __{meta}__ string.".format(meta=meta))


if __name__ == "__main__":
    setup(
        name=NAME,
        description=find_meta("description"),
        license=find_meta("license"),
        url=find_meta("uri"),
        version=find_meta("version"),
        author=find_meta("author"),
        author_email=find_meta("email"),
        maintainer=find_meta("author"),
        maintainer_email=find_meta("email"),
        keywords=KEYWORDS,
        long_description=read("readme.md"),
        packages=PACKAGES,
        zip_safe=False,
        classifiers=CLASSIFIERS,
        install_requires=INSTALL_REQUIRES,
        include_package_data=True,
    )
