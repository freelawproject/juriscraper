from requests import HTTPError
import os


def build_module_list(court_id):
    """Takes a string and builds up a list of modules to import.

    This is a simple recursive function that iteratively looks for __all__
    attributes in packages. If it finds one, it inspects each of the items in
    it to see if each of those has an __all__ attribute. If they lack it, the
    item is added to a list of modules.

    Returns either a list of modules or in the case of errors, an empty list.

    *N.B.*: For the most part, this re-creates the `walk` function from the
    pkgutil library. At some point, it's probably worth replacing this with
    that. Live and learn.

    https://docs.python.org/2/library/pkgutil.html#pkgutil.walk_packages
    """
    module_strings = []

    def find_all_attr_or_punt(court_id):
        """Checks that we have an __all__ attribute. If so, recurses. If not,
        adds the item to our list
        """
        try:
            # Test that we have an __all__ attribute (proving that it's a
            # package) something like: opinions.united_states.federal
            all_attr = __import__(court_id, globals(), locals(), ["*"]).__all__

            # Build the modules back up to full imports
            all_attr = ["%s.%s" % (court_id, item) for item in all_attr]
            for module in all_attr:
                # If we've made it this far, we have an __all__ attribute, so
                # we should see if the items within that attribute do too. And
                # so forth, recursively...
                find_all_attr_or_punt(module)
        except AttributeError:
            # Lacks the __all__ attribute. Probably of the form:
            # juriscraper.opinions.united_states.federal_appellate.ca1,
            # therefore, we add it to our list!
            module_strings.append(court_id)
        # except ImportError as e:
        #    # Something has gone wrong with the import
        #    print("Import error: %s" % e)
        #    return []

    find_all_attr_or_punt(court_id)

    return module_strings


def get_module_by_name(name):
    db_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "opinions")
    )
    for dirName, subdirList, fileList in os.walk(db_root):
        for fname in fileList:
            if "%s.py" % name == fname:
                package, module = (
                    dirName.split("/juriscraper/", 1)[1].replace("/", "."),
                    fname[:-3],
                )
                juriscraper_module = __import__(
                    "juriscraper.%s.%s" % (package, module),
                    globals(),
                    locals(),
                    [module],
                )
                return juriscraper_module.Site()


def site_yielder(iterable, mod):

    site = mod.Site()
    for i in iterable:
        try:
            site._download_backwards(i)
            yield site
        except HTTPError as e:
            continue
