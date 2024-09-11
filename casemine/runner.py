from juriscraper.opinions.united_states.federal_appellate import (
    ca1,
    ca2_p,
    ca2_u,
    ca3_p,
    ca3_u,
    ca4,
    ca5,
    ca6,
    ca7,
    ca8,
    ca9_p,
    ca9_u,
    ca10,
    ca11_p,
    ca11_u,
    cadc,
    cadc_pi,
    cafc,
)
from juriscraper.opinions.united_states.state import (
    ala,
    ark,
    cal,
    colo,
    conn,
    dc,
    delch,
    fla,
    ga,
    haw,
    hawapp,
    idaho_civil,
    idaho_criminal,
    ill,
    iowa,
    kan_p,
    ky,
    la,
    mass,
)
from juriscraper.oral_args.united_states.federal_appellate import ca3

# Create a site object
site = cafc.Site()

site.execute_job("cafc")

# Populate it with data, downloading the page if necessary
# site.parse()

# Print out the object
print(str(site))

# Print it out as JSON
# print(site.to_json())

# Iterate over the item
for opinion in site:
    print(opinion)
