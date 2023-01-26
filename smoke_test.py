from datetime import datetime, timedelta
from quaker import Query, Client

client = Client()
query = Query(starttime=datetime.now() - timedelta(days=20))

foo = client.execute(query, "scrap.foo.csv")


