from datetime import datetime
from venv import logger

from juriscraper.opinions.united_states.federal_appellate import ca11_p, cadc, \
    ca11_u, scotus_slip
from juriscraper.opinions.united_states.state import ala, alaska, ark, cal, \
    calag, colo, dc, conn, coloctapp, connappct, texag, nj, washctapp_p,ohioctcl_beginningofyear

# Create a site object
site = ohioctcl_beginningofyear.Site()
site.execute_job("ohioctcl_beginningofyear")
# site.parse()
logger.info("executed job successfully")

# Print out the object
print(str(site))
# Print it out as JSON
print(site.to_json())
print("faltu")

# Iterate over the item
for opinion in site:
    print(opinion)
