from opinions.united_states.state import nv_supreme


# Create a site object
site = nv_supreme.Site()

# Populate it with data
site.parse()

# Print out the object
print str(site)
