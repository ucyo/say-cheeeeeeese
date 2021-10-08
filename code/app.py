import intake
import geopandas as gpd
import rasterio
from rasterio.mask import mask
from satsearch import Search
from const import germany_bbox, selection
from matplotlib import pyplot as plt

cloud_coverage = 5  # 0 - 100%
data_coverage = 80  # 0 - 100%
dates = "2017-01-01/2018-05-01"
URL = "https://earth-search.aws.element84.com/v0"

# def show_image(fp):
#     src = rasterio.open(fp)
#     plt.figure(figsize=(6,6))
#     plt.title('Final Image')
#     plt.imshow(src.read()[0,:,:], interpolation=None)
#     print(src.read()[0,:,:].max())
#     plt.savefig('test.pdf')

def main():
    catalog = get_intake_catalog(dates, germany_bbox, cloud_coverage, data_coverage)
    pv_labels = gpd.read_file('labels/labels.geojson')
    uid = selection[3]
    band = 'B02'
    output = f'./mask_{uid}_{band}.tif'
    create_mask(uid, catalog, band, pv_labels, output)
    # show_image(output)

def create_mask(uid, catalog, band, labels, output):
    item = catalog[uid]
    fp = getattr(item, band).metadata['href']

    print("Masking ...")
    with rasterio.open(fp) as src:
        labels.to_crs({'init': src.crs}, inplace=True)
        out_image, out_transform = mask(src, labels.geometry, crop=True)
        out_image = out_image.astype(bool)
        out_meta = src.meta.copy()
        out_meta.update({"driver": "GTiff",
                    "height": out_image.shape[1],
                    "width": out_image.shape[2],
                    "transform": out_transform})

    print(f"Writing mask to '{output}'")
    with rasterio.open(output, "w", **out_meta) as final:
        final.write(out_image)  # 1 if pv, 0 else

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
