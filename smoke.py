from datetime import datetime, timedelta
from quaker import Query, Client

import os

OUT =  "scrap.foo.csv"
if os.path.exists(OUT):
    os.remove(OUT)

client = Client()
query = Query(starttime=datetime.now() - timedelta(days=100))

foo = client.execute(query, OUT)


