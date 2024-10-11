from juriscraper.opinions.united_states.federal_appellate import ca11_p, cadc, \
    ca11_u, scotus_slip
from juriscraper.opinions.united_states.state import ala, alaska, ark, cal, \
    calag, colo, dc

print("Above code has been removed by hitesh branch")

# Create a site object
site = dc.Site()

# site.execute_job("ca11_u")
# Populate it with data, downloading the page if necessary
site.parse()

# Print out the object
print(str(site))

# Print it out as JSON
print(site.to_json())

# Iterate over the item
for opinion in site:
    print(opinion)
