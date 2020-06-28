import numpy as np
import requests
import matplotlib as plt
import os
import glob
import progressbar

MAX_TILE_COUNT = 500  # maximum number of OSM tiles to download

# constants
OSM_TILE_SIZE = 256  # OSM tile size in pixels


def deg2xy(lat_deg, lon_deg, zoom) -> (float, float):
    """
    return OSM global x,y coordinates from lat,lon in degrees
    :param lat_deg: Latitude in degrees to convert to y coordinate
    :param lon_deg: Longitude in degrees to convert to x coordinate
    :param zoom: Zoom level needed
    :return: Global x and y coordinates
    """
    lat_rad = np.radians(lat_deg)
    n = 2.0 ** zoom
    x = (lon_deg + 180.0) / 360.0 * n
    y = (1.0 - np.log(np.tan(lat_rad) + (1 / np.cos(lat_rad))) / np.pi) / 2.0 * n
    return x, y


def deg2tile_coord(lat_deg, lon_deg, zoom) -> (int, int):
    """
    return OSM tile x,y from lat,lon in degrees (from https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames)
    Calls deg2xy and converts those values to integers
    :param lat_deg: Latitude in degrees
    :param lon_deg: Longitude in degrees
    :param zoom: Zoom level
    :return: The tile numbers for that location
    """
    x, y = deg2xy(lat_deg, lon_deg, zoom)
    return int(x), int(y)


def num2deg(x_tile, y_tile, zoom) -> (float, float):
    """
    return lat,lon in degrees from OSM tile x,y (from https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames)
    :param x_tile: X tile number
    :param y_tile: Y tile number
    :param zoom: Zoom level
    :return: Latitude and longitude in degrees
    """
    n = 2.0 ** zoom
    lon_deg = x_tile / n * 360.0 - 180.0
    lat_rad = np.arctan(np.sinh(np.pi * (1 - 2 * y_tile / n)))
    lat_deg = np.degrees(lat_rad)
    return lat_deg, lon_deg


def sc2deg(sc_value) -> float:
    """
    Calculate degrees from semicircle value
    :param sc_value:
    :return:
    """
    return np.float(sc_value) * 180 / 2**31


def get_tile_url(x, y, zoom, url='https://maps.wikimedia.org/osm-intl'):
    """
    Creates the tile url based upon the coordinates, the zoom and the base url
    Url is of the form {url}/{zoom}/{x}/{y}.png
    :param x: X coordinate
    :param y: Y coordinate
    :param zoom: Zoom level
    :param url: Base url, default is 'https://maps.wikimedia.org/osm-intl'
    :return: Returns the complete url
    """
    return '/'.join([url, str(zoom), str(x), str(y) + '.png'])


def download_tile_file(tile_url, tile_file, verbose=False) -> bool:
    """
    download image from url to file
    :param tile_url: The url of the tile to download
    :param tile_file: The file to save the tile to
    :param verbose: Verbosity flag
    :return: Returns true or false respectively
    """
    try:
        resp = requests.get(tile_url, headers={'User-Agent': 'Mozilla/5.0'}, stream=True)
    except requests.exceptions.RequestException as e:
        if verbose:
            print(e)
        return False

    if resp.ok:
        if verbose:
            print('Downloading ' +  tile_url)
        with open(tile_file, 'wb') as file:
            file.write(resp.content)
        return True


def download_tiles_for_area(x_tile_min, x_tile_max,
                            y_tile_min, y_tile_max,
                            zoom, url='https://maps.wikimedia.org/osm-intl'):
    """
    Download the tiles specified by the x, y and zoom values
    The tileservers are accessed using the pattern {url}/{zoom}/{x_tile}/{y_tile}.png and the tiles saved as
    {zoom}_{x_tile}_{y_tile}.png
    :param x_tile_min: Minimum x_tile value
    :param x_tile_max: Maximum x_tile value
    :param y_tile_min: Minimum y_tile value
    :param y_tile_max: Maximum y_tile value
    :param zoom: Zoom at which to download the tiles
    :param url: The url used to download the tiles.
    :return: No return value
    """
    # total number of tiles
    tile_count = (x_tile_max-x_tile_min+1)*(y_tile_max-y_tile_min+1)
    # Restrict the number of tiles that are downloaded
    if tile_count > MAX_TILE_COUNT:
        print('ERROR zoom value too high')
        return
    # download tiles
    if not os.path.exists('tiles'):
        os.makedirs('tiles')
    i = 0
    with progressbar.ProgressBar(max_value=tile_count) as bar:
        for x in range(x_tile_min, x_tile_max+1):
            for y in range(y_tile_min, y_tile_max+1):
                tile_url = '/'.join([url, str(zoom), str(x), str(y) + '.png'])
                tile_file = '_'.join(['tiles/tile', str(zoom), str(x), str(y) + '.png'])
                # check if tile already downloaded
                if not glob.glob(tile_file):
                    i += 1
                    bar.update(i)
                    if not download_tile_file(tile_url, tile_file):
                        tile_image = np.ones((OSM_TILE_SIZE, OSM_TILE_SIZE, 3))
                        plt.imsave(tile_file, tile_image)

