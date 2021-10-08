import intake
import geopandas as gpd
from satsearch import Search
from const import germany_bbox, selection

cloud_coverage = 5  # 0 - 100%
data_coverage = 80  # 0 - 100%
dates = "2017-01-01/2018-05-01"
URL = "https://earth-search.aws.element84.com/v0"


def main():
    catalog = get_intake_catalog(dates, germany_bbox, cloud_coverage, data_coverage)
    pv_labels = gpd.read_file('labels/labels.geojson')


def get_intake_catalog(dates, bbox, cc, dc):
    results = Search.search(
        url=URL,
        collections=["sentinel-s2-l2a-cogs"],  # note collection='sentinel-s2-l2a-cogs' doesn't work
        datetime=dates,
        bbox=bbox,
        query=[f"eo:cloud_cover<{cc}", f"sentinel:data_coverage>{dc}"],
        sort=["<datetime"],
    )
    print(f"{results.found()} items")
    items = results.items()
    return intake.open_stac_item_collection(items)


if __name__ == "__main__":
    main()
