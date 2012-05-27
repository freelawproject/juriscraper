from opinions.united_states.state import wash_supreme


# Create a site object
site = wash_supreme.Site()

# Populate it with data
site.parse()

# Print out the object
print str(site)
