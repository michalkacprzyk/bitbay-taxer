#!/usr/bin/env python3
# mk (c) 2018

import argparse

# https://docs.python.org/3/library/csv.html
import csv

from datetime import datetime
import logging

#
# Command line call
ap = argparse.ArgumentParser(description='Program helps to workaround bitbay.net export history issues.'
                                         ' First there was no export support at all, then the support to CSV was'
                                         ' introduced but it is limited to last three months.')
ap.add_argument('inputfile', help='A "copy-paste" text file from the bitbay transaction page.'
                                  ' Sometimes needs some manual cleanup.')
ap.add_argument('type', help='"fees" or "transactions"')
ap.add_argument('-v', '--verbose', help='Print more messages', action='store_true')
ap.add_argument('--logfile', help='Logfile for all the messages')
args = ap.parse_args()

#
# Log
log = logging.getLogger('bitbay_history_converter')
log.setLevel(logging.DEBUG)
# Format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# Console handler
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG if args.verbose else logging.INFO)
ch.setFormatter(formatter)
log.addHandler(ch)
# Log file handler
if args.logfile:
    fh = logging.FileHandler(args.logfile)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    log.addHandler(fh)


def post_processing_transactions(data):
    # Post processing to achieve identical format as bitbay.net use in their exports

    formatted_list_of_rows = []
    for row in data:
        if row[0] == 'Rynek':
            formatted_list_of_rows.append(row)
            continue

        # Surround currency separator with spaces...
        row[0] = row[0].replace('-', ' - ')

        # Convert date and time
        old_datetime_string = row[1].replace(' ', '').replace(',', ' ')
        old_datetime_format = "%m/%d/%Y %I:%M:%S%p"
        datatime_object = datetime.strptime(old_datetime_string, old_datetime_format)
        new_datetime_format = "%d-%m-%Y %H:%M:%S"
        row[1] = datatime_object.strftime(new_datetime_format)

        # Translate BID/ASK
        if row[2] == 'BID':
            row[2] = 'Kupno'
        else:
            row[2] = 'Sprzedaż'

        # Remove currency spaces and indicators
        row[4] = row[4][:-3].replace(' ', '')  # PLN
        row[5] = row[5][:-3].replace(' ', '')  # BTC, ETH etc. (from pair)
        row[6] = row[6][:-3].replace(' ', '')  # PLN

        formatted_list_of_rows.append(row)

    return formatted_list_of_rows


def post_processing_operations(data):
    formatted_list_of_rows = []
    for row in data:
        if row[1] == 'Rodzaj':
            formatted_list_of_rows.append(row)
            continue

        # Convert date and time
        old_datetime_string = row[0].replace(' ', '').replace(',', ' ')
        old_datetime_format = "%m/%d/%Y %I:%M:%S%p"
        datatime_object = datetime.strptime(old_datetime_string, old_datetime_format)
        new_datetime_format = "%d-%m-%Y %H:%M:%S"
        row[0] = datatime_object.strftime(new_datetime_format)

        # Add currency to Rodzaj
        currency = row[2][-3:]
        row[1] = row[1] + ': ' + currency

        # Remove minus from the fee value
        row[2] = row[2][1:]

        # Remove currency spaces and indicators
        row[2] = row[2][:-3].replace(' ', '')
        row[3] = row[3][:-3].replace(' ', '')

        formatted_list_of_rows.append(row)

    return formatted_list_of_rows


def main():
    with open(args.inputfile, "r", encoding="utf-8") as tf:
        raw_content = tf.readlines()
    log.debug('Got "{}" raw lines'.format(len(raw_content)))

    # Strip newlines, unify minuses
    list_content = [x.strip().replace('−', '-') for x in raw_content]

    # Types
    if args.type == "transactions":
        headers = ['Rynek', 'Data operacji', 'Rodzaj', 'Typ', 'Kurs', 'Ilość', 'Wartość']
    elif args.type == "fees":
        headers = ['Data operacji', 'Rodzaj', 'Wartość', 'Saldo po']
    else:
        log.error('Unknown operation type')
        exit(1)

    log.debug('Type is "{}"'.format(args.type))
    log.debug('Will use headers: "{}"'.format(headers))

    entries_per_row = len(headers)
    log.debug('Check if the copy-paste file is likely valid')
    log.debug('Total number of lines "{}" should divide by number of headers "{}"'
              .format(len(list_content), entries_per_row))
    assert (len(list_content) % entries_per_row == 0)

    # Generate a proper list of rows
    data = [headers]

    # Pre processing
    counter = 0
    current_row = []
    for item in list_content:
        current_row.append(item)
        counter += 1

        if counter == entries_per_row:
            data.append(current_row)
            current_row = []
            counter = 0

    log.debug('Got "{}" lines after pre-processing'.format(len(data)))

    # Post processing
    if args.type == "transactions":
        data = post_processing_transactions(data)
    elif args.type == "fees":
        data = post_processing_operations(data)

    log.debug('Got "{}" lines after post-processing'.format(len(data)))

    # Save as CSV
    output = str(args.inputfile)[:-4] + '.csv'
    with open(output, 'w', newline='', encoding="utf-8") as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for row in data:
            csvwriter.writerow(row)

    log.info("Done. CSV saved as: {}".format(output))


if __name__ == '__main__':
    main()
