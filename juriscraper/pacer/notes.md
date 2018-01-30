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
          
          We always coerce this value to zero to avoid duplicates in our
          database.
          
    6951218: The remaining numbers appear to just be a serial number for each 
          item. So far no patterns detected.

It's my belief (mlr) that the doc1 URLs have this name because of their fourth 
digit.


## APIs

### possible_case_numbers.pl

PACER has an API that you can use to look up case numbers and get case names and PACER docket IDs in XML as the result. This API is used by the main PACER query page when you past in a case number and press the button for "Find this Case". This needs further inspection, requests look like:

    GET 'https://ecf.cand.uscourts.gov/cgi-bin/possible_case_numbers.pl?3:12-cv-3879;number=0.1258953044538912'
    
Which returns:

    <request number='3:12-cv-3879'>
        <case number='3:12-cv-3879' 
              id='257622' 
              title='3:12-cv-03879-VC Technology Properties Limited LLC et al v. Novatel Wireless, Inc. (closed 07/14/2015)' 
              sortable='3:2012-cv-03879-VC'/>
    </request>

The `number=0.1258953044538912` parameter is used to defeat browser caching (cf. https://ecf.cand.uscourts.gov/lib/validate_case_number.js l.1499: "This random number causes the browser to never cache case number results."), so you can ignore it. Removing or tweaking it doesn't seem to make a difference.

### mobile_query.pl

The mobile query page, e.g. https://ecf.mad.uscourts.gov/cgi-bin/mobile_query.pl, returns the number of docket entries in a case without charging a fee, as:

```
<a id="entriesLink" href="/cgi-bin/mobile_query.pl?search=dktEntry&amp;caseid=191474&amp;caseNum=1:17-cv-11577-PBS" data-transition="slide" class="ui-link-inherit">
                            Docket Entries
                            <span class="ui-li-count ui-btn-up-c ui-btn-corner-all">
                                52
                            </span>
                        </a>
```

However, this count includes unnumbered minute entries. So the number may well be higher than the highest numbered docket entry in a case.

### DocVerify.pl

This page is only available on CM/ECF, but provides several pieces of interesting information. This page is supposed to do some sort of document verification. As described in [this handy PDF][pdf], you can input a case number and a document number from that case, and it will give you some hashes about that document. This sounds very useful as a form of verification, but it's entirely unclear what the hashes represent. 

The only use that the page seems to have is that it allows you to see if the current hashes (as computed by PACER) match the original hashes (as computed by PACER). I guess this helps you to understand whether the item has changed, but a simple "has this item changed" button seems more obvious.

Anyway, the page also provides the docket entry text and file size, which is potentially quite useful. 

[pdf]: http://www.ilnd.uscourts.gov/_assets/_documents/_forms/_cmecf/pdfs/v60/v6_verify_document.pdf
  
### document_link.pl

Now (apparently) deprecated from District CMECF, but possibly still current in Bankruptcy CMECF, an `href` link to a document in a Docket Report or Claims Register may come with an `id` property that encodes various link parameters, with `K` delimiting parameters (`&` function) and `V` delimiting assignments (`=` function). The `CMECF.widget.DocLink()` function (in `dls_url.js`, see below) calls document_link.pl` to rewrite these into `/doc1` URLs which are then bare of such metadata.

For instance:

```
  <a
    href="/cgi-bin/show_doc.pl?caseid=605035&amp;claim_id=43976411&amp;claim_num=70-1&amp;magic_num=MAGIC"
    id="documentKcaseidV605035Kclaim_idV43976411Kclaim_numV70-1Kmagic_numVMAGIC">
    70-1
  </a>
  <script>
    CMECF.widget.DocLink('documentKcaseidV605035Kclaim_idV43976411Kclaim_numV70-1Kmagic_numVMAGIC');
  </script>
```

whereupon

```
  https://ecf.caeb.uscourts.gov/cgi-bin/document_link.pl?documentKcaseidV605035Kclaim_idV43976411Kclaim_numV70-1Kmagic_numVMAGIC
```

returns

```
  https://ecf.caeb.uscourts.gov/doc1/032026913922
```

### show_case_doc

Discovered in the EDNY RSS feed, the `show_case_doc` script (no terminal `.pl`) allows looking up a `doc1` URL (DLS) in District CMECF (no BK support) given the case ID and document number. E.g.:

```
  https://ecf.nyed.uscourts.gov/cgi-bin/show_case_doc?90,406590,,,
```

returns a `302` redirect to

```
   https://ecf.nyed.uscourts.gov/doc1/123013711961?caseid=406590&pdf_header=2
```

## JavaScript on PACER

All of the JavaScript in PACER has been compressed making it difficult to understand. However, you can often find a comment before the compressed file saying where the uncompressed version lives. In case that changes, here's the District goDLS function, as available here: https://ecf.mad.uscourts.gov/lib/dls_url.js:

    ////////////////////////////////////////
    // My understanding of the parameters //
    ////////////////////////////////////////
    // Generates a form, appends it to the end of the document, and then
    // submits it.
    //
    // hyperlink: Where the form is posted to. The HTML 'action' attribute.
    // de_caseid: The internal PACER ID for the case.
    // de_seqno: The internal PACER document number within the case. This
    //   differs from the number that we see for reasons unknown.
    // got_receipt: If set to '1', this will bypass the receipt page and
    //   download the PDF immediately. This is set to 1 *after* the user has
    //   seen the receipt. If receipts are disabled, I believe this will always
    //   be the empty string.
    // pdf_header: ??
    // pdf_toggle_possible: ??
    // magic_num: ??
    // hdr: ??
    
    function goDLS(hyperlink, de_caseid, de_seqno, got_receipt, pdf_header, pdf_toggle_possible, magic_num, hdr) {
        var form_id  = 'go_dls_url';
        var form_element;
    
        if (document.getElementById(form_id)) {
            var old_form = document.getElementById(form_id);
            document.body.removeChild(old_form);
        }
    
        var url_form = document.createElement('form');
        url_form.setAttribute('action', hyperlink);
        url_form.setAttribute('enctype', 'multipart/form-data');
        url_form.setAttribute('method', 'post');
        url_form.setAttribute('id'	, form_id);
        document.body.appendChild(url_form);
    
        // optional additional parameters
    
        if (de_caseid.length > 0) {
            // always supplied when following links from application
            form_element = document.createElement('input');
            form_element.setAttribute('type', 'hidden');
            form_element.setAttribute('name', 'caseid');
            form_element.setAttribute('value', de_caseid);
            url_form.appendChild(form_element);
        }
    
        if (de_seqno.length > 0) {
            // always supplied when following links from application
            form_element = document.createElement('input');
            form_element.setAttribute('type', 'hidden');
            form_element.setAttribute('name', 'de_seq_num');
            form_element.setAttribute('value', de_seqno);
            url_form.appendChild(form_element);
        }
    
        if (got_receipt.length > 0) {
            // supplied from receipt page displayed before document viewing
            form_element = document.createElement('input');
            form_element.setAttribute('type', 'hidden');
            form_element.setAttribute('name', 'got_receipt');
            form_element.setAttribute('value', got_receipt);
            url_form.appendChild(form_element);
        }
    
        if (pdf_header.length > 0) {
            // optional user preference (overrideable by application defaults)
            form_element = document.createElement('input');
            form_element.setAttribute('type', 'hidden');
            form_element.setAttribute('name', 'pdf_header');
            form_element.setAttribute('value', pdf_header);
            url_form.appendChild(form_element);
        }
    
        if (pdf_toggle_possible.length > 0) {
            // optional user preference (overrideable by application defaults)
            form_element = document.createElement('input');
            form_element.setAttribute('type', 'hidden');
            form_element.setAttribute('name', 'pdf_toggle_possible');
            form_element.setAttribute('value', pdf_toggle_possible);
            url_form.appendChild(form_element);
        }
    
        if (magic_num.length > 0) {
            // only provided from application when NEF hyperlink clicked on multi-document filing
            form_element = document.createElement('input');
            form_element.setAttribute('type', 'hidden');
            form_element.setAttribute('name', 'magic_num');
            form_element.setAttribute('value', magic_num);
            url_form.appendChild(form_element);
        }
    
        if (hdr.length > 0) {
            // only provided from application when NEF hyperlink clicked on ROA/Appendix
            form_element = document.createElement('input');
            form_element.setAttribute('type', 'hidden');
            form_element.setAttribute('name', 'hdr');
            form_element.setAttribute('value', hdr);
            url_form.appendChild(form_element);
        }
    
        document.getElementById(form_id).submit();
    }

In Bankruptcy CMECF, the function signature is different, replacing the `hdr` parameter with various bankruptcy-specific parameters for claim documents. https://ecf.caeb.uscourts.gov/lib/dls_url.js:

  function goDLS(hyperlink, de_caseid, de_seqno, got_receipt, pdf_header, pdf_toggle_possible, magic_num, claim_id, claim_num, claim_doc_seq) {
