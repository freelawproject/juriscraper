What is this
============
Juriscrape is a scraper library that is used to scrape the American court system. 
It currently is able to scrape most state courts and all appellate Federal 
courts. 

Juriscrape is part of a two-part system. The second part is the 'caller', which
you can see a reference implementation of at [CourtListener.com][1]. While the 
caller is responsible for calling Juriscrape, and for processing its output, 
Juriscrape is responsible for the minimal amount of work possible that will 
return the meta data for a court.

Installation & dependencies
===========================
pip install chardet==1.0.1
pip install requests==0.10.2

Usage
======
Will document this soon.

Output
=========
Output from Juriscrape is available as XML if called with the to_xml() method. 
If this method is used, there is a schema available describing the output you 
can expect.

If Juriscrape is called from a Python function, it will return a Site object, 
which can be inspected and then manipulated by the caller.

License
========
Juriscrape is licensed under the permissive BSD license.

[1]: https://bitbucket.org/mlissner/search-and-awareness-platform-courtlistener/overview