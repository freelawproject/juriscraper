from datetime import datetime

from juriscraper.opinions.united_states.state import mich, michctapp, \
    mich_orders, michctapp, michctapp_orders, md, mdctspecapp

# Create a site object
site = mdctspecapp.Site()

# site.execute_job("md")

site.parse()

# Print out the object
# print(str(site))

# Print it out as JSON
# print(site.to_json())

# Iterate over the item
# i=1
for opinion in site:
    print(opinion)
    # print(f"{opinion.get('case_dates')} || {opinion.get('case_names')} || {opinion.get('download_urls')} || {opinion.get('docket_numbers')}")
    # i=i+1

# print(f"total docs - {i}")
