Download and preprocess Sentinel-2 data for PV detection.

# Code
The code is split into two parts: (1) Downloading the data tiles from the s3 storage
and (2) generating masks for each resolution level for each tile.

## Sentinel-2 data and downloading the data
Sentinel-2 uses a 100x100 km^2 tile structure depicted
[here](https://eatlas.org.au/data/uuid/f7468d15-12be-4e3f-a246-b2882a324f59)
and [here](https://sentinel.esa.int/web/sentinel/missions/sentinel-2/data-products).
All recorded data is corrected and mapped to this tile structure.
The data consists of 13 bands with three resolutions: 10m, 20m and 60m.
Details can be found [here](https://sentinel.esa.int/web/sentinel/missions/sentinel-2/instrument-payload/resolution-and-swath).
The bands 2, 3, 4 and 8 are 10m resolution;
5, 6, 7, 8a, 11 and 12 are 20m resolution; and
1, 9, and 10 are 60m resolution.

### Searching and downloading the data
The library uses [`satsearch`](https://github.com/sat-utils/sat-search) for searching the
Sentinel-2 data on s3 and [`intake`](https://pypi.org/project/intake/) for accessing the data.
The search function is defined [here](./code/app.py#L67-L75).
Currently the search defines parameters for a date range,
max. cloud coverage percentage and min. data coverage. Data coverage defines
how much of the tile is actually covered with valid data. Since the path
of the satellite does not cross the tiles as a whole every time, there are missing data in the tiles.
How much of the tile is actually filled with data, is given by this parameter.

Germany is covered by roughly 70 tiles. Executing the search defined [here](./code/app.py#L31) might return several data for a single tile. Since for the use case of PV coverage only a single tile for an area is needed, there is a preselection of [tiles](./code/const.py#L3). Further, a download script is prepared which downloads exactly these data.

### Downloading the data

0. Enter container
```shell
docker-compose run code bash
```
1. Generate the download script
```shell
links <script save location>
```
2. Start download
```shell
bash download.py
```
All files will be saved in `pwd` with the folder structure `<TILEID_YYYYMMDD>` e.g. `32UQD_20180417`.
Within this folder each band has its own `tif` file. Additionally there are (all 20m resolution):

- True Colour Image (TCI)
- Scene Classification Layer (SCL)
- Water Vapour map (WVP)
- Preview Image (L2A - PVI)
- Aerosol Optical Thickness (AOT)

The SCL layer has 12 classifications:

|Integer|Meaning|
|--|--|
| 0| No data|
| 1| Saturated/Defective|
| 2| Dark Area|
| 3| Cloud Shadows|
| 4| Vegetation|
| 5| Bare Soils|
| 6| Water|
| 7| Clouds low prob.|
| 8| Clouds medium prob.|
| 9| Clouds high prob.|
| 10| Cirrus|
| 11| Snow|

Details about the classification be found [here](https://www.sentinel-hub.com/faq/how-get-s2a-scene-classification-sentinel-2/).

## Masking the data
The repository uses [`rasterio`](https://pypi.org/project/rasterio/) for reading the Sentinel-2 data and
[`geopandas`](https://geopandas.org/) for reading the [labels](./code/labels/labels.geojson).
The masking algorithm is defined [here](./code/app.py#L17-L24).

The masking algorithm defines masks based on the labels and resolution of the data.
It generates a mask for each of the three resolutions of the data set (10m, 20m, 60m).
The masks have value `0` if the pixel is **not** a PV location and `255` if it **is** a  PV location based on the label data. The bands 2, 5 and 1 are used for generating the 10m, 20m and 60m resolution masks (see [here](./code/app.py#L19))

### Generating the masks

0. Enter container
```shell
docker-compose run code bash
```
1. Generate the masks
```shell
masks <folder with data from tiles>
```
The masks are added to the tile next to the bands and are named `mask_{10m,20m,60m}.tif`.

## Usage

All the tif files can be read with `rasterio` using `rasterio.open(fp)`
