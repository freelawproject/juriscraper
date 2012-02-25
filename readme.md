What is this?
=============
Juriscraper is a scraper library that is used to scrape the American court system. 
It is currently able to scrape all appellate Federal courts, and state courts
are planned soon.

Juriscraper is part of a two-part system. The second part is the 'caller', which 
should be developed by the system using Juriscraper. The caller is responsible 
for calling a scraper, downloading and saving its results. A reference 
implementation of the caller is being developed at [CourtListener.com][1].


Installation & dependencies
===========================
    pip install chardet==1.0.1
    pip install requests==0.10.2


Usage
======
The caller written in Python can can scrape a court as follows:

    from opinions.united_states.federal import ca1
    
    # Create a site object 
    site = ca1.Site()
    
    # Populate it with data
    site.parse()
    
    # Print out the object
    print str(site)

Development of a `to_xml()` or `to_json()` method has not yet been completed, as 
all callers have thus far been able to work directly with the Python objects.

Version History
===============
**Current**  
0.1 - Supports all common Federal Appeals courts

**Roadmap**  
0.2 - Support for all possible Federal District courts and small Federal Appeals courts  
0.3 - Support for all state appeals courts

**Beyond**  
 - add oral arguments  
 - add video  
 - add other countries

License
========
Juriscraper is licensed under the permissive BSD license.

[1]: https://bitbucket.org/mlissner/search-and-awareness-platform-courtlistener/overview