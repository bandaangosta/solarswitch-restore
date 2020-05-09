#! /usr/bin/env python3
import os
import sys

# Activate Python virtual environment containing all needed libraries and dependencies
try:
    CURRENT_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))

    if os.path.exists(os.path.join(CURRENT_DIR, 'venv/bin/activate_this.py')):
        activate_this = os.path.join(CURRENT_DIR, 'venv', 'bin', 'activate_this.py')
    else:
        raise Exception('Virtual environment not found. Try "make venv" first.')
    try:
        # Python 2
        execfile(activate_this, dict(__file__=activate_this))
    except NameError:
        # Python 3
        exec(open(activate_this).read(), {'__file__': activate_this})
except:
    raise

import re
from datetime import datetime
from tqdm import tqdm
from pprint import pprint
import csv
import click

# For click object
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

# Name of measurements to extract from logs
MEASUREMENTS = ['current', 'voltage', 'frequency', 'energy', 'power', 'powerFactor']
MEASUREMENT_RELAYS = ['relays']

def convertDate(strDate):
    try:
        date = datetime.strptime(strDate, '%Y-%m-%dT%H:%M:%S')
        return date
    except ValueError:
        try:
            date = datetime.strptime(strDate, '%Y-%m-%dT%H:%M:%S.%f')
            return date
        except:
            return None
    except:
        return None


@click.command(short_help='Process SolarSwitch prototype system logs to extract data measurements to InfluxDB-compatible CSV files.')
@click.argument('path_to_log')
@click.option('-s', '--timestamp_from', help='(optional) Limit log extraction to start from this UTC timestamp in format yyyy-mm-ddTHH:MM:SS')
@click.option('-e', '--timestamp_to', help='(optional) Limit log extraction to end up to this UTC timestamp in format yyyy-mm-ddTHH:MM:SS')
def main(path_to_log, timestamp_from, timestamp_to):
    '''Process SolarSwitch prototype system logs to extract data measurements to InfluxDB-compatible CSV files.

    Path to log file is required as argument. Typically, log file is named /data/logs/solarwitch.log or similar.'
    '''

    with open(path_to_log) as file:
        data_logs = file.read()

    ## PROCESSING ALL MEASUREMENTS EXCEPT 'relays'

    # Regular expression pattern used to find measurements values in solarswitch logs
    # Used for all measurements except 'relays'
    # It matches and returns strings like:
    #   voltage,flow=DC,location=inverter value=0.034,value_raw=0.014 1588110508
    #   current,flow=DC,location=solar_panel value=-1.492,value_raw=2.179 1588110508
    #   ...
    #
    #   Returned strings have measurement name, tags (keys and values), fields (keys and values) and timestamp (UTC, precision in seconds)
    #
    pattern = re.compile('(?:{}),.*'.format('|'.join(MEASUREMENTS)))
    results = pattern.findall(data_logs)

    full_measurements = set()
    full_tags_per_measurement = dict()
    full_fields_per_measurement = dict()

    # First, for each measurement, extract all tags and fields
    print('Analyzing log file to extract all measurements, tags and fields...')
    for row in tqdm(results):
        dictRow = {}
        sections = row.split(' ')

        measurement_tags = sections[0].split(',')
        measurement = measurement_tags[0]
        dictRow['measurement'] = measurement
        dictRow['tags'] = {}
        for tag in measurement_tags[1:]:
            tag_key, tag_value = tag.split('=')
            dictRow['tags'][tag_key] = tag_value

        fields = sections[1].split(',')
        dictRow['fields'] = {}
        for field in fields:
            field_key, field_value = field.split('=')
            dictRow['fields'][field_key] = field_value

        utctimestamp = datetime.utcfromtimestamp(int(sections[2])).strftime('%Y-%m-%dT%H:%M:%SZ')
        dictRow['timestamp'] = utctimestamp

        # Example:
        # dictRow = {'measurement': 'voltage',
        #  'tags': {'flow': 'DC', 'location': 'control_GND'},
        #  'fields': {'value': '0.000', 'value_raw': '-0.000'},
        #  'timestamp': '2020-05-02T20:38:55Z'
        # }

        # Ignore rows outside required minimum time range, if defined
        if timestamp_from:
            conv_timestamp_from = convertDate(timestamp_from)
            if not datetime.utcfromtimestamp(int(sections[2])) > conv_timestamp_from:
                continue

        # Ignore rows outside required maximum time range, if defined
        if timestamp_to:
            conv_timestamp_to = convertDate(timestamp_to)
            if not datetime.utcfromtimestamp(int(sections[2])) < conv_timestamp_to:
                continue

        full_measurements.add(dictRow['measurement'])
        if dictRow['measurement'] in full_tags_per_measurement:
            full_tags_per_measurement[dictRow['measurement']] = full_tags_per_measurement[dictRow['measurement']].union(list(dictRow['tags'].keys()))
        else:
            full_tags_per_measurement[dictRow['measurement']] = set()
            full_tags_per_measurement[dictRow['measurement']] = full_tags_per_measurement[dictRow['measurement']].union(list(dictRow['tags'].keys()))

        if dictRow['measurement'] in full_fields_per_measurement:
            full_fields_per_measurement[dictRow['measurement']] = full_fields_per_measurement[dictRow['measurement']].union(list(dictRow['fields'].keys()))
        else:
            full_fields_per_measurement[dictRow['measurement']] = set()
            full_fields_per_measurement[dictRow['measurement']] = full_fields_per_measurement[dictRow['measurement']].union(list(dictRow['fields'].keys()))

    # print('Measurements found: ', sorted(full_measurements))
    # print('Tags found: ', full_tags_per_measurement)
    # print('Fields found: ', full_fields_per_measurement)

    if len(full_measurements) == 0:
        print('No measurements found')

    # Extract rows of data and reformat it for CSV file
    for _measurement in sorted(full_measurements):
        print(f"Processing measurement {_measurement} and generating CSV file...")

        data = []
        header = ['name', 'time']
        header.extend(sorted(list(full_tags_per_measurement[_measurement])))
        header.extend(sorted(list(full_fields_per_measurement[_measurement])))

        for row in tqdm(results):
            dictRow = {}
            sections = row.split(' ')

            measurement_tags = sections[0].split(',')
            measurement = measurement_tags[0]

            if measurement != _measurement:
                continue

            dictRow['measurement'] = measurement
            dictRow['tags'] = {}
            for tag in measurement_tags[1:]:
                tag_key, tag_value = tag.split('=')
                dictRow['tags'][tag_key] = tag_value

            fields = sections[1].split(',')
            dictRow['fields'] = {}
            for field in fields:
                field_key, field_value = field.split('=')
                dictRow['fields'][field_key] = field_value

            utctimestamp = datetime.utcfromtimestamp(int(sections[2])).strftime('%Y-%m-%dT%H:%M:%SZ')
            dictRow['timestamp'] = utctimestamp

            # Example:
            # dictRow = {'measurement': 'voltage',
            #  'tags': {'flow': 'DC', 'location': 'control_GND'},
            #  'fields': {'value': '0.000', 'value_raw': '-0.000'},
            #  'timestamp': '2020-05-02T20:38:55Z'
            # }

            # Ignore rows outside required minimum time range, if defined
            if timestamp_from:
                conv_timestamp_from = convertDate(timestamp_from)
                if not datetime.utcfromtimestamp(int(sections[2])) > conv_timestamp_from:
                    continue

            # Ignore rows outside required maximum time range, if defined
            if timestamp_to:
                conv_timestamp_to = convertDate(timestamp_to)
                if not datetime.utcfromtimestamp(int(sections[2])) < conv_timestamp_to:
                    continue

            row = [measurement, dictRow['timestamp']]
            for tag_key in sorted(list(full_tags_per_measurement[measurement])):
                row.append(dictRow['tags'][tag_key])

            for field_key in sorted(list(full_fields_per_measurement[measurement])):
                row.append(dictRow['fields'].get(field_key))

            data.append(row)

        if len(data) > 0:
            with open(f'backup_{_measurement}.csv', 'w') as file:
                csv_writer = csv.writer(file)
                csv_writer.writerow(header)
                # Sort data by timestamp before writing to disk for improved DB insertion
                data.sort(key = lambda y: y[1])
                csv_writer.writerows(data)
            print(f'Wrote backup_{_measurement}.csv')
        else:
            print(f'No data to write for measurement {_measurement}')


    ## PROCESSING 'relays' MEASUREMENTS ONLY

    # Regular expression pattern for 'relays' measurements only
    # It matches and returns strings like:
    #   relays value=3227 1588446863
    #
    #   Returned strings have "relays" measurement name, one field ("value") and timestamp (UTC, precision in seconds)
    #
    pattern = re.compile('relays value.*')
    results = pattern.findall(data_logs)

    # Extract rows of data and reformat it for CSV file
    for _measurement in ['relays']:
        print(f"Processing measurement {_measurement} and generating CSV file...")

        data = []
        header = ['name', 'time', 'value']

        for row in tqdm(results):
            sections = row.split(' ')
            measurement = sections[0]

            if measurement != _measurement:
                continue

            value = sections[1].split('=')[1]

            utctimestamp = datetime.utcfromtimestamp(int(sections[2])).strftime('%Y-%m-%dT%H:%M:%SZ')

            # Ignore rows outside required minimum time range, if defined
            if timestamp_from:
                conv_timestamp_from = convertDate(timestamp_from)
                if not datetime.utcfromtimestamp(int(sections[2])) > conv_timestamp_from:
                    continue

            # Ignore rows outside required maximum time range, if defined
            if timestamp_to:
                conv_timestamp_to = convertDate(timestamp_to)
                if not datetime.utcfromtimestamp(int(sections[2])) < conv_timestamp_to:
                    continue

            data.append([measurement, utctimestamp, value])

        if len(data) > 0:
            with open(f'backup_{_measurement}.csv', 'w') as file:
                csv_writer = csv.writer(file)
                csv_writer.writerow(header)
                # Sort data by timestamp before writing to disk for improved DB insertion
                data.sort(key = lambda y: y[1])
                csv_writer.writerows(data)
            print(f'Wrote backup_{_measurement}.csv')
        else:
            print(f'No data to write for measurement {_measurement}')


if __name__ == '__main__':
    sys.exit(main())