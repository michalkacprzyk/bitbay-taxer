#!/usr/bin/env python3
# mk (c) 2018

# The idea here was to use bitbay API as a source of data, and then automate the entire process.
# Unfortunately, the transaction limits imposed by them make this unreliable as it's possible to have
# more than 200 transactions between updates, therefore this tool will miss some and the user will still have to
# manually copy and paste full history from the web interface...

# Yet it is still a valid example of using the API


import argparse
# https://docs.python.org/3/howto/logging-cookbook.html
import logging

from time import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from time import sleep
import hmac
import hashlib
import json
import pandas
import csv

#
# Command line call
ap = argparse.ArgumentParser(description='')
ap.add_argument('-v', '--verbose', help='print more messages', action='store_true')
ap.add_argument('--logfile', help='Logfile for all the messages')
args = ap.parse_args()

#
# Log
log = logging.getLogger('bitbay_tax_calculator')
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


def bitbay_api_call(method, params={}):
    url = 'https://bitbay.net/API/Trading/tradingApi.php'

    key = b''
    secret = b''

    params['method'] = method
    params['moment'] = int(time())

    post = urlencode(params).encode('utf8')
    sign = hmac.new(secret, post, hashlib.sha512).hexdigest()

    headers = {'API-Key': key,
               'API-Hash': sign
               }

    request = Request(url, post, headers)
    ret = urlopen(request).read().decode()

    return ret


def get_operations_history_data_via_api(currs):
    """
    :param currs: A list containing interesting currencies
    :return:
    """

    all_data = []

    # Unless we set our limit high, we will get max. only 10 rows, hard limit seems to be 200
    limit = 1000

    for cur in currs:
        log.debug('Making the API call for: "{}"'.format(cur))

        json_str = bitbay_api_call('history', {'currency': cur, 'limit': limit})
        json_obj = json.loads(json_str)
        all_data = all_data + json_obj

        log.debug('Got "{}" rows, going to sleep.'.format(len(json_obj)))
        sleep(1)  # Max one call per second

    log.debug('In total got "{}" rows'.format(len(all_data)))

    return all_data


def operations_data_dict_to_lol(data_dict):

    headers_order = ['time', 'operation_type', 'amount', 'balance_after']
    headers_map = {
        "time": "Data operacji",
        "operation_type": "Rodzaj",
        "amount": "Wartość",
        "balance_after": "Saldo po",
        # "comment": "",
        # "id": "",
        #"currency": "btc",
    }

    data_lol = []

    for row_d in data_dict:
        row_l = []
        for col in headers_order:
            row_l.append(row_d[col])
        data_lol.append(row_l)

    return data_lol


def main():

    currs = 'PLN BTC BCC ETH XRP'.split()
    log.debug('We are interested in: {}'.format(currs))

    log.debug('Getting the operations history data via API')
    operations_data_api = get_operations_history_data_via_api(currs)

    # Fee data only
    fee_data = [row for row in operations_data_api if row ['operation_type'] == '-fee']
    fee_data_sorted = sorted(fee_data, key=lambda o: o['id'])

    fee_data_lol = operations_data_dict_to_lol(fee_data_sorted)

    with open('/home/k4m1/test.csv', 'w', newline='') as csvoutput:
        csvwriter = csv.writer(csvoutput, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for row in fee_data_lol:
            csvwriter.writerow(row)


if __name__ == '__main__':
    main()
