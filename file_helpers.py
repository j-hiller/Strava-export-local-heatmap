import fitdecode
import numpy as np
import re
import progressbar
import pandas as pd
import gzip

import osm_helpers


def prepare_act_csv(act_csv, verbose=False) -> pd.DataFrame:
    """
    Load the summary csv which is contained in the Strava export. This can then be used for easy filtering of the
    activities. Additionally, some helpful columns such as the cumulated distance per month and year are added. The
    result is a dataframe that can be used for easy further processing
    :param act_csv: Activity csv in the Strava export. Should be `activities.csv` and located on the top-level folder of
    your Strava export
    :param verbose: Verbosity flag
    :return: Pandas dataframe with all the activities from the `activities.csv`
    """
    activities = pd.read_csv(act_csv)
    if verbose:
        print('{} contains {} activities'.format(str(act_csv), len(activities)))
    activities['Activity Date'] = pd.to_datetime(activities['Activity Date'])
    activities.index = activities['Activity Date']
    activities['Yearly Distance'] = activities.groupby(by=[activities.index.year, 'Activity Type']).Distance.cumsum()
    activities['Yearly Start Distance'] = activities['Yearly Distance'] - activities.Distance
    activities['Monthly Distance'] = activities.groupby(by=[activities.index.month, 'Activity Type']).Distance.cumsum()
    activities['Monthly Start Distance'] = activities['Monthly Distance'] - activities.Distance
    activities['Yearly Duration'] = activities.groupby(by=[activities.index.year, 'Activity Type'])[
        'Elapsed Time'].cumsum()
    activities['Yearly Start Duration'] = activities['Yearly Duration'] - activities['Elapsed Time']
    activities['Monthly Duration'] = activities.groupby(by=[activities.index.month, 'Activity Type'])[
        'Elapsed Time'].cumsum()
    activities['Monthly Start Duration'] = activities['Monthly Duration'] - activities['Elapsed Time']
    if verbose:
        print('Using {} activities for further processing'.format(len(activities)))
    return activities


def extract_lat_lon_from_fit(file, verbose=False) -> list:
    """
    Extracts latitude and longitude from `.fit` files. Handling of FIT files is unfortunately not quite intuitive, but
    seems to work
    :param file: The FIT file
    :param verbose: Verbosity flag
    :return: A list of latitude and longitude values in the order they appear in the file
    """
    fit_lat_lon_data = []
    with fitdecode.FitReader(file) as fit:
        for frame in fit:
            if isinstance(frame, fitdecode.FitDataMessage):
                if frame.name == 'record':
                    if frame.has_field('position_lat') and frame.has_field('position_long'):
                        try:
                            fit_lat_lon_data.append([
                                osm_helpers.sc2deg(frame.get_value('position_lat')),
                                osm_helpers.sc2deg(frame.get_value('position_long'))
                            ])
                        except TypeError:
                            if verbose:
                                print('Had the following value: {}, {}'.format(
                                    frame.get_value('position_lat'), frame.get_value('position_long')))
    return fit_lat_lon_data


def extract_lat_lon_from_gpx(file, verbose=False) -> list:
    """
    Extract latitude and longitude values from gpx values.
    :param file: The gpx file
    :param verbose: Verbosity flag. Well, unused
    :return: A list of the latitude and longitude values in the file
    """
    gpx_lat_lon_data = []
    with open(file, encoding='utf-8') as file:
        for line in file:
            if '<trkpt' in line:
                tmp = re.findall('-?[0-9]*[.]?[0-9]+', line)

                gpx_lat_lon_data.append([float(tmp[0]), float(tmp[1])])
    return gpx_lat_lon_data


def extract_lat_lon_from_file_list(file_list, base_folder, verbose=False) -> np.array:
    """
    Extracts latitude and longitude values from the list of files. This list of files can be manually generated or taken
    from the `activities.csv` using the `get_lat_lon_from_df` function
    :param file_list: Simple list of files
    :param base_folder: The folder in which the `activities.csv` is located TODO: fix this
    :param verbose: Verbosity flag
    :return: An array of all the latitude and longitude values
    """
    lat_lon_data = []
    print('Extracting GPS values...')
    with progressbar.ProgressBar(max_value=len(file_list)) as bar:
        for i, af in enumerate(file_list):
            if isinstance(af, float) and np.isnan(af):
                if verbose:
                    print('Found nan value in file list, skipping...')
                continue
            tf = base_folder.joinpath(af)
            if verbose:
                print('Processing {}'.format(tf))
            if tf.suffix == '.gpx':
                lat_lon_data.extend(extract_lat_lon_from_gpx(tf.absolute(), verbose))
            elif tf.suffix == '.gz':
                new_file = tf.absolute().parent.joinpath(tf.stem)
                with gzip.open(tf.absolute(), 'rb') as gzip_file:
                    with open(tf.absolute().parent.joinpath(tf.stem), 'wb') as f:
                        f.write(gzip_file.read())
                if new_file.suffix == '.gpx':
                    lat_lon_data.extend(extract_lat_lon_from_gpx(new_file, verbose))
                elif new_file.suffix == '.fit':
                    lat_lon_data.extend(extract_lat_lon_from_fit(new_file, verbose))
                new_file.unlink()
            elif tf.suffix == '.fit':
                lat_lon_data.extend(extract_lat_lon_from_fit(tf, verbose))
            else:
                print('Also found ' + tf)
            bar.update(i)
    lat_lon_data = np.array(lat_lon_data)
    return lat_lon_data


def get_lat_lon_from_df(activities, exp_folder, year, month, gear_filter='',
                        activity_filter='', verbose=False) -> (list, int):
    """
    Does all the filtering in the dataframe containing the activity overview. Filtering can be done by multiple
    parameters. Currently, those are gear, activity type, year and month
    :param activities: A dataframe containing an overview of the activites. This is generated by importing the
    `activities.csv` in the top-level folder of the Strava export
    :param exp_folder: The folder of the Strava export. Needed for file processing
    :param year: The year for which to extract values. Can be `all` or the year (2019, 2020, ...)
    :param month: The month for which to extract value. Can be `all` or the number of the month (1...12)
    :param gear_filter: Filtering by Gear (e.g. the name you gave your bike on Strava)
    :param activity_filter: Filter by activity (e.g. `Run`, `Ride`, etc.)
    :param verbose: Verbosity flag
    :return: An array containing latitude and longitude values. And the number of activities those values come from
    """
    # Filter the dataframe by gear, i.e. the name you gave it on Strava
    if gear_filter != '':
        activities = activities[activities['Activity Gear'] == gear_filter]
    # Filter the dataframe by type, e.g. 'Ride' or 'Run'
    if activity_filter != '':
        activities = activities[activities['Activity Type'] == activity_filter]
    if year != 'all':
        activities = activities[activities.index.year == int(year)]
    if month != 'all':
        activities = activities[activities.index.month == int(month)]
    if len(activities) == 0:
        return np.array([]), 0
    lat_lon_data = extract_lat_lon_from_file_list(activities['Filename'].tolist(), exp_folder, verbose=verbose)
    lat_lon_data = np.array(lat_lon_data)
    return lat_lon_data, len(activities)
