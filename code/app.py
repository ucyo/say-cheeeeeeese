from satsearch import Search
from const import germany_bbox

cloud_coverage = 5  # 0 - 100%
data_coverage = 80  # 0 - 100%
dates = "2017-01-01/2018-05-01"
URL = "https://earth-search.aws.element84.com/v0"


def main():
    results = Search.search(
        url=URL,
        collections=["sentinel-s2-l2a-cogs"],  # note collection='sentinel-s2-l2a-cogs' doesn't work
        datetime=dates,
        bbox=germany_bbox,
        query=[f"eo:cloud_cover<{cloud_coverage}", f"sentinel:data_coverage>{data_coverage}"],
        sort=["<datetime"],
    )
    print("%s items" % results.found())
    items = results.items()


if __name__ == "__main__":
    main()
