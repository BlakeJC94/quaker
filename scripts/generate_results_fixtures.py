
from datetime import datetime, timedelta
from quaker import Query, Client

client = Client()

N_PAGES = 3

for fmt in ["csv", "geojson", "kml", "xml", "quakeml", "text"]:
    for page in range(N_PAGES):
        print(f"{fmt=}, {page=}")

        starttime = datetime.now() - timedelta(days=30*(N_PAGES - page))
        endtime = datetime.now() - timedelta(days=30*(N_PAGES - 1 - page))

        query = Query(format=fmt, starttime=starttime, endtime=endtime, limit=20)
        resp = client._execute(query)

        lines = resp.text.split("\n")
        with open(f"scrap.page{page}.{fmt}", "w", encoding="utf-8") as f:
            for line in lines:
                f.writelines(line + "\n")
