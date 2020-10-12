import os
from ebaysdk.exception import ConnectionError
from ebaysdk.finding import Connection as Finding
from ebaysdk.shopping import Connection as Shopping

PRODUCTION_DOMAIN = "svcs.ebay.com"
SANDBOX_DOMAIN = "svcs.sandbox.ebay.com"

SHOPPING_SANDBOX_DOMAIN = "open.api.sandbox.ebay.com"
SHOPPING_DOMAIN = "open.api.ebay.com"

request = {
    'categoryId': '619',
    'paginationInput': {
        'entriesPerPage': 10,
        'pageNumber': 1
    }
}

try:
    api = Finding(domain=PRODUCTION_DOMAIN, config_file='ebay.yaml')
    # response = api.execute('findItemsByKeywords', {'keywords': 'baseball'})
    response = api.execute('findItemsByCategory', request)
except ConnectionError as e:
    print("exception:", e)

file = open("results.txt", "w")
file.write(str(response.dict()))
file.close()