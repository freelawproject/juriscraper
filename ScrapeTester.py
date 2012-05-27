from opinions.united_states.state import or_supreme


# Create a site object
site = or_supreme.Site()

# Populate it with data
site.parse()

# Print out the object
print str(site)
