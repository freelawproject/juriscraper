Here's a summary of my findings: 

### Docket purchase 

- Currently, CL uses the [`query`](https://github.com/freelawproject/juriscraper/blob/dde9d687c6c1051585c03d3baf8c6b27b81a0898/juriscraper/pacer/docket_report.py#L1466) method from the [`DocketReport`](https://github.com/freelawproject/juriscraper/blob/dde9d687c6c1051585c03d3baf8c6b27b81a0898/juriscraper/pacer/docket_report.py#L402) class to purchase dockets (within the [`fetch_docket_by_pacer_case_id`](https://github.com/freelawproject/courtlistener/blob/cb012e831429fba71e426fb76a4a7eda99308627/cl/recap/tasks.py#L2032) function).

- I identified a function named [`get_appellate_docket_by_docket_number`](https://github.com/freelawproject/courtlistener/blob/cb012e831429fba71e426fb76a4a7eda99308627/cl/corpus_importer/tasks.py#L1699) in CL. Its docstring suggests it can retrieve dockets using a docket number and court ID combination. This function uses the [`AppellateDocketReport`](https://github.com/freelawproject/juriscraper/blob/dde9d687c6c1051585c03d3baf8c6b27b81a0898/juriscraper/pacer/appellate_docket.py#L28) class.

- Since [`AppellateDocketReport`](https://github.com/freelawproject/juriscraper/blob/dde9d687c6c1051585c03d3baf8c6b27b81a0898/juriscraper/pacer/appellate_docket.py#L28) is not actively used in CL (used in a few commands a few years ago), I tested its functionality to ensure it remains operational for appellate docket purchases. I attempted to purchase dockets for various courts using the class. Here's a summary of the results:

    | Court ID | System | Docket | Result |
    | -------- | ------- | ------- | ------- |
    | ca1  | CM/ECF | [24-8033](https://www.courtlistener.com/docket/69461760/ortiz-v-saba-university-school-of-medicine/) | ✅ |
    | ca2 | ACMS | [24-3279](https://www.courtlistener.com/docket/69479713/robinson-v-aetna/) | ❌ |
    | ca3    | CM/ECF | [24-3311](https://www.courtlistener.com/docket/69486898/r-s-v-east-brunswick-township-school-district/) | ✅ |
    | ca9    | ACMS | [24-7497](https://www.courtlistener.com/docket/69464577/yurok-tribe-et-al-v-united-states-environmental-protection-agency/) | ❌ |

  Looks like it works with CM/ECF, but not ACMS. No surprise there.

- The `query` method signatures differ between [`AppellateDocketReport`](https://github.com/freelawproject/juriscraper/blob/dde9d687c6c1051585c03d3baf8c6b27b81a0898/juriscraper/pacer/appellate_docket.py#L28) and [`DocketReport`](https://github.com/freelawproject/juriscraper/blob/dde9d687c6c1051585c03d3baf8c6b27b81a0898/juriscraper/pacer/docket_report.py#L402) classes.

- Some fields from the [`PacerFetchQueue`](https://github.com/freelawproject/courtlistener/blob/cb012e831429fba71e426fb76a4a7eda99308627/cl/recap/models.py#L309) model align with the signature used in [`DocketReport`](https://github.com/freelawproject/juriscraper/blob/dde9d687c6c1051585c03d3baf8c6b27b81a0898/juriscraper/pacer/docket_report.py#L402). A mapping might be required to use data from [`PacerFetchQueue`](https://github.com/freelawproject/courtlistener/blob/cb012e831429fba71e426fb76a4a7eda99308627/cl/recap/models.py#L309) with [`AppellateDocketReport`](https://github.com/freelawproject/juriscraper/blob/dde9d687c6c1051585c03d3baf8c6b27b81a0898/juriscraper/pacer/appellate_docket.py#L28).

- A crucial difference is that [`DocketReport.query`](https://github.com/freelawproject/juriscraper/blob/dde9d687c6c1051585c03d3baf8c6b27b81a0898/juriscraper/pacer/docket_report.py#L1466) uses `pacer_case_id` to retrieve dockets, whereas [`AppellateDocketReport.query`](https://github.com/freelawproject/juriscraper/blob/dde9d687c6c1051585c03d3baf8c6b27b81a0898/juriscraper/pacer/appellate_docket.py#L86) uses the docket number.

- the `query` method from the `AppellateDocketReport` class has a different signature from the one in the `DocketReport` class. Some fields from the [`PacerFetchQueue`](https://github.com/freelawproject/courtlistener/blob/cb012e831429fba71e426fb76a4a7eda99308627/cl/recap/models.py#L309) model aligns with the signature used in the `DocketReport` class. We might need a mapping to use the data from the `PacerFetchQueue`.

- The current fetch endpoint relies on a hidden API to obtain the `pacer_case_id` for cases where this data is missing from the docket record and not included in the fetch request. This API consistently returns "not found" for appellate records. We should bypass this step for appellate docket purchases and ensure we have the `pacer_case_id` beforehand.

- the previous step is important in the current implementation of the fetch endpoint because we're just purchasing dockets from district courts but in 3 is highlighted that we just need the docket number to try to retrieve appellate dockets 

- This step is relevant in the current implementation because we only purchase district court dockets. As highlighted earlier, retrieving appellate dockets only requires the docket number.

- Once Juriscraper successfully parses the docket data, we can use the existing helper functions in CourtListener to create or update the corresponding docket records

### Attachments pages purchase 

This appears to be straightforward.

- Both the `AttachmentPage` and `AppellateAttachmentPage` classes have `query` methods with identical signatures, each accepting only the `pacer_doc_id` as an argument.

- I successfully tested retrieving an attachment page using the `AppellateAttachmentPage` class.

- I believe that after parsing the data using Juriscraper, we can leverage existing helper methods to create or update records in our database.


### PDF purchase 

- I noticed a difference between the behavior of the `AppellateDocketReport.download_pdf` method and what's documented in the changes.md file.

  According to the `changes.md` file, the `download_pdf` method should return a tuple containing two elements:

  - The response object (which could be None if there's an error).
  - A string containing the error message (if there is an error).

  However, the current implementation of the `download_pdf` method doesn't seem to follow this documented behavior.

- The `download_pdf` method in `BaseReport` accepts more arguments compared to `AppellateDocketReport`. However, this difference shouldn't cause issues since `AppellateDocketReport` uses a subset of the same attributes.

- The `appellate` argument in `BaseReport.download_pdf` seems irrelevant as it doesn't support retrieving appellate PDFs. The current implementation attempts to use a doc1 URL to fetch the PDF, which is not the URL structure used for downloading appellate PDFs. Appellate download pages use a completely different URL format

- I successfully purchased a document (entry 3) from [24-3235](https://www.courtlistener.com/docket/69463607/jasminder-singh-v-rachel-thompson/) using the `download_pdf` helper from `AppellateDocketReport`.

- I think we can easily integrate the download method from the AppellateDocketReport class into CourtListener. After we get the PDF as binary data, we should be able to reuse the existing CourtListener helpers to extract the info we need.


[get_appellate_docket_by_docket_number]: 
