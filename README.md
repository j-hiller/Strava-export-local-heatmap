# Strava Data Export Heatmap
_Based upon [github.com/remisalmon/Strava-local-heatmap-browser](https://github.com/remisalmon/Strava-local-heatmap) but strongly varied to fit my liking_

This repository contains scripts to create heatmaps based on your Strava data export.
I modified and created the scripts to create a monthly overview of my cycling activities.
That part is still WIP. 
Therefore, there are various filtering options available to filter by activity, gear, month and year.
Others might follow, depending on what kind of interesting data I find in my further exports.

## Usage

* Download your GPX files from Strava and add them to the `gpx` folder  
(see https://support.strava.com/hc/en-us/articles/216918437-Exporting-your-Data-and-Bulk-Export)
* Run `python3 strava_local_heatmap.py --activity-csv ~/strava_export/activities.csv`
* The heatmap is saved to `heatmap.png`

### Command-line options

```
usage: strava_local_heatmap.py [-h] [--activity-csv ACTIVITY_CSV] [--year YEAR] [--month MONTH]
                               [--bound BOUND BOUND BOUND BOUND] [--output FILE]
                               [--zoom {0,...,19}] [--sigma SIGMA]
                               [--verbose] [--gear GEAR] [--activity ACTIVITY]

Generate a local heatmap from a Strava data export

optional arguments:
  -h, --help            show this help message and exit
  --activity-csv ACTIVITY_CSV
                        Specify the acitvities.csv that comes with the Strava export
  --year YEAR           Files year filter, coded as four digits, e.g. 2020 (default: all)
  --month MONTH         Files month filter coded as number, e.g. 4 for April. Use 0 to get a heatmap for
                        each month (default: all)
  --bound BOUND BOUND BOUND BOUND
                        heatmap bounding box coordinates as lat_min, lat_max, lon_min, lon_max (default:
                        -90 +90 -180 +180)
  --output FILE         heatmap name. .png and year and month will be added (default: heatmap)
  --zoom {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19}
                        heatmap zoom level 0-19 (default: 10)
  --sigma SIGMA         heatmap Gaussian kernel sigma in pixels (default: 1)
  --verbose             Verbosity flag
  --gear GEAR           Used to filter by gear that you might have set up in Strava (default: )
  --activity ACTIVITY   Used to filter by activity type (default: )
```

 :warning: `--zoom` is OpenStreetMap's zoom level, first number after `map=` in [www.openstreetmap.org/#map=](https://www.openstreetmap.org)

Example:  
`strava_local_heatmap.py --activity-csv ~/strava-export/activities.csv`

For an explanation on the cumulative distribution function, see:  
https://medium.com/strava-engineering/the-global-heatmap-now-6x-hotter-23fc01d301de

## Output

**heatmap.png**  
![example_heatmap.png](example_heatmap.png)

### Python dependencies

```
matplotlib==3.2.2
numpy==1.19.0
pandas==1.0.5
fitdecode==0.6.0
requests==2.24.0
progressbar2==3.51.4
```

## TODOs:

- [ ] Improve Readme
- [ ] Add option to select multiple months for a heatmap
- [ ] Add overlays of activity information over the heatmap
- [ ] Add option to generate an overview of year per
    - [ ] month
    - [ ] cumulative distance
    - [ ] cumulative duration
- [ ] Display yearly overview as poster?
- [ ] Add more tests
- [ ] Add option to exclude zone (privacy)
- [ ] Add option to split heatmaps if they are geographically far apart (e.g. you ride at home and at your parents' place across the country)
- [ ] Bug fixing
