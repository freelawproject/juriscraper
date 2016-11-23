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


## CSRF Tokens

It appears that PACER uses CSRF tokens. These seem to take the form of a random string appended to forms so that they submit to random locations. I assume these expire after some period of time, but I cannot be sure. In any case, if you find that your form is not submitting properly, try looking at the code in `free_documents.get_written_report_token`.
