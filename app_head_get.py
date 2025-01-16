import json

documents = None
with open("/Users/eduardorosendo/Development/juriscraper/document.json", "r") as read_content:
    documents=json.load(read_content)


for doc in documents:

    doc['result'] = doc['pacer_doc_id'] ==

    with open('outputfile_4.json', 'w') as file:
        file.write(json.dumps(documents, indent=4, default=str))
