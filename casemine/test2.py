# import os
# import sys
#
# import certifi
# import requests
#
# pdfurl = "https://www.azcourts.gov/opinions/Search-Opinions-Memo-Decs"
# proxies = {"http": "p.webshare.io:9999", "https": "p.webshare.io:9999", }
# headers = {
#     "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0"}
#
# page=1
# while(True):
#     parameters = {}
#
#
#     print("hiting url")
#     response = requests.post(url=pdfurl, proxies=proxies, data=parameters, headers=headers, timeout=120)
#     print(response.status_code)
#     path = "/home/gaugedata/Documents/testings"
#     download_pdf_path = os.path.join(path, "ariz.html")
#     os.makedirs(path, exist_ok=True)
#     filename="/home/gaugedata/Documents/testings/ariz.html"
#     with open(filename, 'wb') as file:
#         file.write(response.content)
#     print('content has been written')
#
#     if(page==10):
#         break
#     page=page+1

from juriscraper.opinions.united_states.federal_appellate import ca11_p, cadc, \
    ca11_u, scotus_slip
from juriscraper.opinions.united_states.state import ala, alaska, ark, cal, \
    calag

# Create a site object
site = calag.Site()

# site.execute_job("ca11_u")
# Populate it with data, downloading the page if necessary
site.parse()

# Print out the object
# print(str(site))

# Print it out as JSON
print(site.to_json())

# Iterate over the item
for opinion in site:
    print(opinion)
