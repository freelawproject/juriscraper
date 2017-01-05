## Introduction

There are a lot of curiosities that you encounter while working with PACER. This document serves a spot to write them all down. 


## Form Submissions

So far, every form on PACER has been set to submit files, even though there are no files to be submitted. This means that in the HTML, you see things like:

    <FORM NAME=GetPass ENCTYPE='multipart/form-data' method=POST
              action="/cgi-bin/WrtOpRpt.pl">
 
To submit such a form using Python `requests` is pretty messy, but the general idea is that it looks like:

    r = s.post(
        url,
        headers={'User-Agent': 'Juriscraper'},
        verify=certifi.where(),
        timeout=30,
        files={
            'login': ('', username),
            'key': ('', password)
        },
    )
    
The weirdest part is that we're submitting form data (the keys, `username` and `password`) as if they are files. The empty strings in the `files` parameter are the filenames that would normally be submitted with these values. So in effect, the above submits two "files" with the keys `login` and `key`, and the contents of the "files" are your username and password.

Yes, this is weird.


## Cookies

The main cookie for PACER seems to be:

    PacerSession
    
Which tends to have a value like:

    r77EsXg47bLdBZEdpPOmWMAA75FOBhJs4nr1bhcdCManBHTjfaFVPkqXkhENscRtylDzyXW2xnsVZrh6ZNljiaqQaZ0P86yzusAjT7naq9OhyQwDWvLCP0a5BAZ87T1C

We've also seen evidence of these other cookies in the HTML of the Written Reports page for CAND:

    ClientDesc
    PacerClient
    PacerClientCode
    PacerPref
    PacerSession
    PublicTerminal
    REDIRECTINSIDE
    KEY


## doc1 URLs

Every document in PACER can be accessed with what we call a doc-one URL. It looks like:

    https://ecf.nysd.uscourts.gov/doc1/12716951218
    
This weird little URL has the following parts of interest:

    nysd: the jurisdiction of the item. These *mostly* correspond to the same 
          IDs we have in CourtListener, but they occassionally differ.
    
    127:  The first three digits of the number at the end correspond to the 
          court, with the earlier numbers going to circuit courts, and then the
          numbers being assigned alphabetically after that. For example, 127,
          above, corresponds to nysd. 128 corresponds to nywb.
    
    1:    The fourth digit in the URL indicates whether the item has attachments 
          or not. If it does not have attachments, this number will be a 1, and 
          you can download the item using the URL. If it does have attachments, 
          the number will be a zero, and clicking it will take you to the 
          attachments list. For items that have a zero, you can switch it to a 1 
          to bypass the attachments list screen and simply get the item you're 
          after.
          
    6951218: The remaining numbers appear to just be a serial number for each 
          item. So far no patterns detected.

It's my belief (mlr) that the doc1 URLs have this name because of their fourth 
digit.


## CSRF Tokens

It appears that PACER uses CSRF tokens. These seem to take the form of a random string appended to forms so that they submit to random locations. I assume these expire after some period of time, but I cannot be sure. In any case, if you find that your form is not submitting properly, try looking at the code in `free_documents.get_written_report_token`.


## Hidden APIs

PACER has an API that you can use to look up case numbers and get case names and PACER docket IDs in XML as the result. This API is used by the main PACER query page when you past in a case number and press the button for "Find this Case". This needs further inspection, requests look like:

    GET 'https://ecf.cand.uscourts.gov/cgi-bin/possible_case_numbers.pl?3:12-cv-3879;number=0.1258953044538912'
    
Which returns:

    <request number='3:12-cv-3879'>
        <case number='3:12-cv-3879' 
              id='257622' 
              title='3:12-cv-03879-VC Technology Properties Limited LLC et al v. Novatel Wireless, Inc. (closed 07/14/2015)' 
              sortable='3:2012-cv-03879-VC'/>
    </request>

Right now I don't know what the `number=0.1258953044538912` part of the request is, but it looks like you can ignore it. Removing or tweaking it doesn't seem to make a difference.
