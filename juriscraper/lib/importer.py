import os
import traceback
from collections.abc import AsyncGenerator, Callable, Iterable
from logging import getLogger
from types import ModuleType

from httpx import HTTPError
from typing_extensions import Unpack

from juriscraper.AbstractSite import AbstractSite, SiteOptions
from juriscraper.lib.type_utils import AsyncClientOptions

logger = getLogger()


def build_module_list(court_id: str) -> list[str]:
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

    def find_all_attr_or_punt(court_id: str) -> None:
        """Checks that we have an __all__ attribute. If so, recurses. If not,
        adds the item to our list
        """
        try:
            # Test that we have an __all__ attribute (proving that it's a
            # package) something like: opinions.united_states.federal
            all_attr = __import__(court_id, globals(), locals(), ["*"]).__all__

            # Build the modules back up to full imports
            all_attr = [f"{court_id}.{item}" for item in all_attr]
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


def get_module_by_name(
    name: str, **kwargs: Unpack[SiteOptions]
) -> AbstractSite | None:
    db_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "opinions")
    )
    for dirName, _subdirList, fileList in os.walk(db_root):
        for fname in fileList:
            if f"{name}.py" == fname:
                package, module = (
                    os.path.relpath(dirName, os.path.dirname(db_root)).replace(
                        os.sep, "."
                    ),
                    fname[:-3],
                )
                juriscraper_module = __import__(
                    f"juriscraper.{package}.{module}",
                    globals(),
                    locals(),
                    [module],
                )
                site_class: object = getattr(juriscraper_module, "Site", None)
                if not isinstance(site_class, type) or not issubclass(
                    site_class, AbstractSite
                ):
                    raise TypeError(
                        f"{juriscraper_module.__name__}.Site must subclass AbstractSite"
                    )
                return site_class(**kwargs)
    return None


async def site_yielder(
    iterable: Iterable[object],
    mod: ModuleType,
    save_response_fn: Callable[[AbstractSite], None] | None = None,
    **kwargs: Unpack[AsyncClientOptions],
) -> AsyncGenerator[AbstractSite, None]:
    """Yield sites whose sessions stay open until iteration advances.

    Use ``contextlib.aclosing`` when consuming this generator so early exits
    also close the current site.
    """
    site_class: object = getattr(mod, "Site", None)
    if not isinstance(site_class, type) or not issubclass(
        site_class, AbstractSite
    ):
        raise TypeError(f"{mod.__name__}.Site must subclass AbstractSite")

    for i in iterable:
        async with site_class(
            save_response_fn=save_response_fn, **kwargs
        ) as site:
            # Empty pages are expected during historical backscrapes, so don't
            # let no_results_warning log an error for this court.
            site.should_have_results = False
            try:
                await site._download_backwards(i)
            except HTTPError:
                logger.debug("%s", traceback.format_exc())
                continue
            yield site
