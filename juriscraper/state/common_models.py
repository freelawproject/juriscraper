from typing import Annotated

from pydantic import BeforeValidator

from juriscraper.lib.html_utils import clean_html
from juriscraper.lib.string_utils import harmonize

CleanString = Annotated[str, BeforeValidator(clean_html)]
HarmonizedCaseName = Annotated[str, BeforeValidator(harmonize)]
