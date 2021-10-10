import intake
import geopandas as gpd
import rasterio
from rasterio.mask import mask
from rasterio.enums import Resampling
from satsearch import Search
from const import germany_bbox, selection
from matplotlib import pyplot as plt
import os
import sys

cloud_coverage = 5  # 0 - 100%
data_coverage = 80  # 0 - 100%
dates = "2017-01-01/2018-05-01"
URL = "https://earth-search.aws.element84.com/v0"
ref_10m = "B02.tif"
ref_20m = "B05.tif"
ref_60m = "B01.tif"


def generate_base_masks():
    base = sys.argv[1]
    resolution_repr = {"10m": ref_10m, "20m": ref_20m, "60m": ref_60m}
    pv_labels = gpd.read_file("labels/labels.geojson")
    for res, band in resolution_repr.items():
        fp = os.path.join(base, band)
        out = os.path.join(base, f"mask_{res}.tif")
        _create_mask(fp, pv_labels, out)


def generate_download_script():
    base = sys.argv[1]
    lines = ["#!/bin/bash"]
    print("Searching for links...")
    catalog = _get_intake_catalog(dates, germany_bbox, cloud_coverage, data_coverage)
    print("Generating aws cmds...")
    for tile in selection:
        item = catalog[tile]
        fp = getattr(item, "B04").metadata["href"]
        fp = fp.replace("https", "s3")
        fp = fp.replace("sentinel-cogs.s3.us-west-2.amazonaws.com", "sentinel-cogs")
        fp, out, _ = fp.rsplit("/", 2)
        fp += f"/{out}"
        out = os.path.join(base, out[4:-6])
        fp = f"aws s3 sync {fp} {out} --no-sign-request"
        lines += [fp]
    print("Writing to file...")
    with open("download.sh", "w") as dst:
        dst.write("\n".join(lines))


def _create_mask(fp, labels, output):
    print("Masking ...")
    with rasterio.open(fp) as src:
        labels.to_crs({"init": src.crs}, inplace=True)
        out_image, out_transform = mask(src, labels.geometry, crop=True)
        out_image[out_image > 0] = 255
        out_image = out_image.astype("uint8")
        out_meta = src.meta.copy()
        print(out_meta)
        out_meta.update(
            {"driver": "GTiff", "height": out_image.shape[1], "width": out_image.shape[2], "transform": out_transform, "dtype": "uint8"}
        )
        print(out_meta)

    print(f"Writing mask to '{output}'")
    with rasterio.open(output, "w", **out_meta) as final:
        final.write(out_image)  # 1 if pv, 0 else


def _get_intake_catalog(dates, bbox, cc, dc):
    results = Search.search(
        url=URL,
        collections=["sentinel-s2-l2a-cogs"],  # note collection='sentinel-s2-l2a-cogs' doesn't work
        datetime=dates,
        bbox=bbox,
        query=[f"eo:cloud_cover<{cc}", f"sentinel:data_coverage>{dc}"],
        sort=["<datetime"],
    )
    items = results.items()
    return intake.open_stac_item_collection(items)


def _scl_resampling(folder, mode):
    scl_fp = os.path.join(folder, "SCL.tif")
    if mode == "10m":
        ref = rasterio.open(os.path.join(folder, ref_10m))
    elif mode == "60m":
        ref = rasterio.open(os.path.join(folder, ref_60m))
    else:
        raise Exception("Mode not recognised")
    return rasterio.open(scl_fp).read(out_shape=(ref.count, ref.height, ref.width), resampling=Resampling.nearest)
