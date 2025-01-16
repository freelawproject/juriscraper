import requests
import json

court_ids = ['arwd', 'cacd', 'caed', 'cand', 'casd', 'cod', 'ctd', 'ded', 'flmd', 'flnd', 'flsd', 'gamd', 'gand', 'gasd', 'hid', 'idd', 'ilcd', 'ilnd', 'ilsd', 'innd', 'insd', 'iand', 'iasd', 'ksd', 'kyed', 'kywd', 'laed', 'lamd', 'lawd', 'med', 'mdd', 'mad', 'mied', 'miwd', 'mnd', 'msnd', 'mssd', 'moed', 'mowd', 'mtd', 'ned', 'nvd', 'nhd', 'njd', 'nmd', 'nyed', 'nynd', 'nysd', 'nywd', 'nced', 'ncmd', 'ncwd', 'ndd', 'ohnd', 'ohsd', 'oked', 'oknd', 'okwd', 'ord', 'paed', 'pamd', 'pawd', 'rid', 'scd', 'sdd', 'tned', 'tnmd', 'tnwd', 'txed', 'txnd', 'txsd', 'txwd', 'utd', 'vtd', 'vaed', 'vawd', 'waed', 'wawd', 'wvnd', 'wvsd', 'wied', 'wiwd', 'wyd', 'gud', 'nmid', 'prd', 'vid', 'okd', 'jpml']

documents = []
for c_id in court_ids:
    print(c_id)
    url = f"https://www.courtlistener.com/api/rest/v4/search/?q=court_id:{c_id}&type=rd&order_by=entry_date_filed%20desc"
    r = requests.get(url)
    response = r.json()
    if not response['count']:
        continue

    document = response['results'][0]
    document['court_id'] = c_id
    del document['snippet']

    docket_id = document['docket_id']
    url = f"https://www.courtlistener.com/api/rest/v4/search/?q=docket_id:{docket_id}&type=d"
    r = requests.get(url)
    response = r.json()
    if not response['count']:
        continue

    docket = response['results'][0]

    document['pacer_case_id'] = docket["pacer_case_id"]
    documents.append(document)

    with open('outputfile_4.json', 'w') as file:
        file.write(json.dumps(documents, indent=4, default=str))



