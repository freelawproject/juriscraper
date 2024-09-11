from juriscraper.opinions.united_states.federal_appellate import ca3_u, ca3_p, \
    ca1, ca2_p, ca2_u, ca4, ca5, ca6, ca7, ca8, ca9_p, ca10, ca9_u, ca11_u, \
    ca11_p, cadc, cadc_pi, cafc
from juriscraper.opinions.united_states.state import mass, la, ky, kan_p, iowa, \
    ill, idaho_civil, idaho_criminal, hawapp, haw, ga, fla, delch, dc, conn, \
    colo, cal, ark, ala
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
