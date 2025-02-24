from datetime import datetime

from juriscraper.opinions.united_states.federal_appellate import ca11_p, cadc, \
    ca11_u
from juriscraper.opinions.united_states.state import mo_min_or_sc

# Create a site object
site = mo_min_or_sc.Site()
site.execute_job("mo_min_or_sc")
# site.parse()
# Print out the object
# print(str(site))
# Print it out as JSON
# print(site.to_json())

# Iterate over the item
for opinion in site:
    print(opinion)
