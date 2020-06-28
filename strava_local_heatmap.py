# Copyright (c) 2020 Johannes Hiller
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# imports
import argparse
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

import osm_helpers
import file_helpers

# parameters
PLT_COLORMAP = 'hot'  # matplotlib color map (from https://matplotlib.org/examples/color/colormaps_reference.html)


def box_filter(image, w_box) -> np.array:
    """
    return image filtered with box filter
    :param image: Image to filter
    :param w_box: Filter parameters
    :return: Retunrs the fft filtered image
    """
    box = np.ones((w_box, w_box)) / (w_box ** 2)
    image_fft = np.fft.rfft2(image)
    box_fft = np.fft.rfft2(box, s=image.shape)
    image = np.fft.irfft2(image_fft * box_fft)
    return image


def create_supertile(x_tile_min, x_tile_max, y_tile_min, y_tile_max, zoom) -> np.array:
    """
    Method that stitches together all the tiles needed for the heatmap and generates one "supertile" from it.
    Tiles are downloaded, if they are not in the tiles folder.
    :param x_tile_min: Minimum x tile value
    :param x_tile_max: Maximum x tile value
    :param y_tile_min: Minimum y tile value
    :param y_tile_max: Maximum y tile value
    :param zoom: The zoom level at which to download the tiles. This strongly impacts the resolution and the number of
    necessary tiles
    :return: An array with the image data of the supertile
    """
    supertile_size = ((y_tile_max - y_tile_min + 1) * osm_helpers.OSM_TILE_SIZE,
                      (x_tile_max - x_tile_min + 1) * osm_helpers.OSM_TILE_SIZE, 3)
    supertile = np.zeros(supertile_size)

    for x in range(x_tile_min, x_tile_max + 1):
        for y in range(y_tile_min, y_tile_max + 1):
            tile_filename = 'tiles/tile_' + str(zoom) + '_' + str(x) + '_' + str(y) + '.png'
            tile = plt.imread(tile_filename)  # float ([0,1])
            i = y - y_tile_min
            j = x - x_tile_min
            # fill supertile with tile image
            supertile[i * osm_helpers.OSM_TILE_SIZE:i * osm_helpers.OSM_TILE_SIZE + osm_helpers.OSM_TILE_SIZE,
            j * osm_helpers.OSM_TILE_SIZE:j * osm_helpers.OSM_TILE_SIZE + osm_helpers.OSM_TILE_SIZE,
            :] = tile[:, :, :3]

    # convert super_tile to grayscale and invert colors
    # convert to 1 channel grayscale image
    supertile = 0.2126 * supertile[:, :, 0] + 0.7152 * supertile[:, :, 1] + 0.0722 * supertile[:, :, 2]
    supertile = 1 - supertile  # invert colors
    # convert back to 3 channels image
    supertile = np.dstack((supertile, supertile, supertile))
    return supertile


def create_heatmap(lat_lon_data, nr_activities, lat_bound_min=-90, lat_bound_max=90,
                   lon_bound_min=-180, lon_bound_max=180, heatmap_zoom=10, sigma_pixels=1, equal=False,
                   url='https://maps.wikimedia.org/osm-intl') -> np.array:
    """
    Creates a heatmap using the data in the `lat_lon_data` array. The underlying tiles are downloaded from OSM and
    converted to a dark theme in order to make the map look cool.
    In order to get a map, that is always centered on the same point and has the same extents, no matter the data, set
    `equal` to True. This will then use the minimum and maximum boundary values for the tile downloading and loading.
    This way, it is possible to get heatmaps with identical extent for each month (or year, activity, etc.)
    :param lat_lon_data: Array containing latitude and longitude values
    :param nr_activities: The number of activities that sourced the latitude and longitude values
    :param lat_bound_min: Minimum latitude value to include in the heatmap. Default is -90
    :param lat_bound_max: Maximum latitude value to include in the heatmap. Default is 90
    :param lon_bound_min: Minimum longitude value to include in the heatmap. Default is -180
    :param lon_bound_max: Maximum longitude value to include in the heatmap. Default is 180.
    :param heatmap_zoom: The OSM zoom level to use. Affects number of tiles and resolution. Default is 10.
    :param sigma_pixels: Sigma value used for the binning of points. Default is 1.
    :param equal: Set this true to use the tile boundaries as heatmap extent. Default is False
    :param url: The tile base url. Default is https://maps.wikimedia.org/osm-intl
    :return: An array with the image data of the heatmap on the supertile
    """
    # crop data to bounding box
    lat_lon_data = lat_lon_data[np.logical_and(lat_lon_data[:, 0] > lat_bound_min,
                                               lat_lon_data[:, 0] < lat_bound_max), :]
    lat_lon_data = lat_lon_data[np.logical_and(lat_lon_data[:, 1] > lon_bound_min,
                                               lat_lon_data[:, 1] < lon_bound_max), :]

    if equal:
        x_tile_min, y_tile_max = osm_helpers.deg2tile_coord(lat_bound_min, lon_bound_min, heatmap_zoom)
        x_tile_max, y_tile_min = osm_helpers.deg2tile_coord(lat_bound_max, lon_bound_max, heatmap_zoom)
    else:
        # find min, max tile x,y coordinates
        lat_min = lat_lon_data[:, 0].min()
        lat_max = lat_lon_data[:, 0].max()
        lon_min = lat_lon_data[:, 1].min()
        lon_max = lat_lon_data[:, 1].max()
        x_tile_min, y_tile_max = osm_helpers.deg2tile_coord(lat_min, lon_min, heatmap_zoom)
        x_tile_max, y_tile_min = osm_helpers.deg2tile_coord(lat_max, lon_max, heatmap_zoom)

    osm_helpers.download_tiles_for_area(x_tile_min, x_tile_max, y_tile_min, y_tile_max, heatmap_zoom, url=url)

    print('creating heatmap...')

    # create supertile
    supertile = create_supertile(x_tile_min, x_tile_max, y_tile_min, y_tile_max, heatmap_zoom)
    # supertile_size = supertile.size()

    # fill trackpoints data
    data = np.zeros(supertile.shape[:2])
    # add w_pixels (= Gaussian kernel sigma) pixels of padding around the trackpoints for better visualization
    w_pixels = int(sigma_pixels)

    for k in range(len(lat_lon_data)):
        x, y = osm_helpers.deg2xy(lat_lon_data[k, 0], lat_lon_data[k, 1], heatmap_zoom)
        i = int(np.round((y - y_tile_min) * osm_helpers.OSM_TILE_SIZE))
        j = int(np.round((x - x_tile_min) * osm_helpers.OSM_TILE_SIZE))
        data[i - w_pixels:i + w_pixels + 1, j - w_pixels:j + w_pixels + 1] += 1  # pixels are centered on the trackpoint

    # threshold trackpoints accumulation to avoid large local maxima
    # pixel resolution (from https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames)
    pixel_res = 156543.03 * np.cos(np.radians(np.mean(lat_lon_data[:, 0]))) / (2 ** heatmap_zoom)
    # trackpoints max accumulation per pixel = 1/5 (trackpoints/meters) * pixel_res (meters/pixel) per activity
    # (Strava records trackpoints every 5 meters in average for cycling activities)
    m = (1.0 / 5.0) * pixel_res * nr_activities
    # threshold data to max accumulation of trackpoints
    data[data > m] = m

    # kernel density estimation = convolution with (almost-)Gaussian kernel
    # (from https://www.peterkovesi.com/papers/FastGaussianSmoothing.pdf)
    w_filter = int(np.sqrt(12.0 * sigma_pixels ** 2 + 1.0))
    data = box_filter(data, w_filter)

    # normalize data to [0,1]
    data = (data - data.min()) / (data.max() - data.min())

    cmap = plt.get_cmap(PLT_COLORMAP)
    # colorize data
    data_color = cmap(data)
    # remove background color
    data_color[(data_color == cmap(0)).all(2)] = [0.0, 0.0, 0.0, 1.0]
    # remove alpha channel
    data_color = data_color[:, :, :3]

    # create color overlay
    supertile_overlay = np.zeros(supertile.shape)
    for c in range(3):
        # fill color overlay
        supertile_overlay[:, :, c] = (1.0 - data_color[:, :, c]) * supertile[:, :, c] + data_color[:, :, c]
    return supertile_overlay


def save_supertile_as_image(supertile_overlay, file_name, ext='.png', verbose=False) -> Path:
    """
    Save the supertile as an image.
    :param supertile_overlay: Array containing the image data of the heatmap
    :param file_name: The file name for saving
    :param ext: The picture file extension. Default is .png
    :param verbose: Verbosity flag. Default is False.
    :return: The full path to the image
    """
    if verbose:
        print('saving ' + file_name + ext + '...')
    plt.imsave(file_name + ext, supertile_overlay)
    return Path(file_name, ext)


def extract_start_stop_from_month(month):
    """
    Extract the time range from the string specifying the month
    :param month: String containing the month. Should be 'x-x'
    :return: The start and and end value for the months. Note that stop will be end+1
    """
    tmp = month.split('-')
    if len(tmp) < 2 or tmp[0] == '' or tmp[-1] == '':
        return 1, 13
    start = int(tmp[0])
    stop = int(tmp[-1])
    if start > stop:
        start, stop = stop, start
    if start < 1:
        start = 1
    if start > 13:
        start = 13
    stop += 1
    if stop > 13:
        stop = 13
    if stop < 1:
        stop = 1
    return start, stop


def main(args) -> None:
    """
    The main function used to run all the different extractions and generations
    :param args: Struct passed from argparse
    :return: None
    """
    lat_bound_min, lat_bound_max, lon_bound_min, lon_bound_max = args.bound
    act_csv = Path(args.activity_csv)

    activities = file_helpers.prepare_act_csv(act_csv, verbose=args.verbose)

    if args.month == '0' or '-' in args.month:
        if '-' in args.month:
            start, stop = extract_start_stop_from_month(args.month)
        else:
            start = 1
            stop = 13
        print('creating heatmaps for months {} - {} in {} '.format(start, stop - 1, args.year))
        for i in range(start, stop):
            lat_lon_data, nr_activities = file_helpers.get_lat_lon_from_df(activities, act_csv.parent, args.year,
                                                                           str(i), gear_filter=args.gear,
                                                                           activity_filter=args.activity,
                                                                           verbose=args.verbose)
            if lat_lon_data.size == 0:
                print('No activities matching ' + args.activity + ' and ' + args.gear + ' in month ' + str(i) + ' of '
                      + str(args.year))
                continue
            st_o = create_heatmap(lat_lon_data, nr_activities, lat_bound_min, lat_bound_max, lon_bound_min,
                                  lon_bound_max, args.zoom, equal=True, sigma_pixels=args.sigma)
            hm_file = save_supertile_as_image(st_o, file_name=args.file + '_' + str(args.year) + '_' + str(i))
    else:
        lat_lon_data, nr_activities = file_helpers.get_lat_lon_from_df(activities, act_csv.parent, args.year,
                                                                       args.month, gear_filter=args.gear,
                                                                       activity_filter=args.activity,
                                                                       verbose=args.verbose)
        if lat_lon_data.size == 0:
            print('No activities matching ' + args.activity + ' and ' + args.gear + ' in month ' + str(args.month)
                  + ' of ' + str(args.year))
            return
        st_o = create_heatmap(lat_lon_data, nr_activities, lat_bound_min, lat_bound_max, lon_bound_min, lon_bound_max,
                              args.zoom, sigma_pixels=args.sigma)
        hm_file = save_supertile_as_image(st_o, file_name=args.file + '_' + str(args.year) + '_' + str(args.month),
                                          verbose=args.verbose)


if __name__ == '__main__':
    # command line parameters
    parser = argparse.ArgumentParser(description='Generate a local heatmap from a Strava data export',
                                     epilog='Report issues to https://github.com/j-hiller/strava-local-heatmap')

    parser.add_argument('--activity-csv', dest='activity_csv', default='',
                        help='Specify the acitvities.csv that comes with the Strava export')
    parser.add_argument('--year', dest='year', default='all',
                        help='Files year filter, coded as four digits, e.g. 2020 (default: all)')
    parser.add_argument('--month', dest='month', default='all',
                        help='Files month filter coded as number, e.g. 4 for April. Use 0 to get a heatmap for each '
                             'month (default: all)')
    parser.add_argument('--bound', dest='bound', type=float, nargs=4, default=[-90, +90, -180, +180],
                        help='heatmap bounding box coordinates as lat_min, lat_max, lon_min, lon_max '
                             '(default: -90 +90 -180 +180)')
    parser.add_argument('--output', dest='file', default='heatmap',
                        help='heatmap name. .png and year and month will be added (default: heatmap)')
    parser.add_argument('--zoom', dest='zoom', type=int, default=10, choices=range(0, 20),
                        help='heatmap zoom level 0-19 (default: 10)')
    parser.add_argument('--sigma', dest='sigma', type=int, default=1,
                        help='heatmap Gaussian kernel sigma in pixels (default: 1)')
    parser.add_argument('--verbose', dest='verbose', action='store_true',
                        help='Verbosity flag')
    parser.add_argument('--gear', dest='gear', default='',
                        help='Used to filter by gear that you might have set up in Strava (default: '')')
    parser.add_argument('--activity', dest='activity', default='', help='Used to filter by activity type (default: '')')

    args = parser.parse_args()

    # run main
    if args.activity_csv != '':
        main(args)
    else:
        parser.print_help()
