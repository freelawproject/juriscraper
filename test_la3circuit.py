import json

from juriscraper.opinions.united_states.state import la3circuit

# Initialize the scraper
scraper = la3circuit.Site()

# Parse the latest opinions
scraper.parse()

# Convert the cases to a JSON-formatted string
cases_json = json.dumps(scraper.cases, indent=4, default=str)

# Print the JSON collection
print(cases_json)
