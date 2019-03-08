#!/usr/bin/env python3
# mk (c) 2018

import argparse

# https://docs.python.org/3/howto/logging-cookbook.html
import logging

# https://docs.python.org/3/library/csv.html
import csv

from modules.Taxer import Taxer
from modules.Feeer import Feeer

#
# Command line call
ap = argparse.ArgumentParser(description='Program calculates PL TAX on bitbay.net transactions '
                                         '+ gains in a FIFO way '
                                         '+ PCC '
                                         '+ FEEs in PLN')
ap.add_argument('transactions', help='A CSV file containing transactions in bitbay export format. '
                                     'Preferably it contains all relevant transactions for a given year.')
ap.add_argument('fees', help='A CSV file containing fees in a tweaked bitbay export format. '
                             'Should correspond to the transactions file above.')
ap.add_argument('-v', '--verbose', help='Print more messages', action='store_true')
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
    fh = logging.FileHandler(args.logfile, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    log.addHandler(fh)


def main():

    log.info('Read the transactions data from: "{}"'.format(args.transactions))
    transactions_data = []
    with open(args.transactions, newline='', encoding="utf-8") as csvtransactions:
        cr = csv.reader(csvtransactions, delimiter=';')
        for row in cr:
            transactions_data.append(row)
    log.debug('Number of rows read: "{}"'.format(len(transactions_data)))

    log.info('Read the fees data from: "{}"'.format(args.fees))
    fees_data = []
    with open(args.fees, newline='', encoding="utf-8") as csvfees:
        cr = csv.reader(csvfees, delimiter=';')
        for row in cr:
            fees_data.append(row)
    log.debug('Number of rows read: "{}"'.format(len(fees_data)))

    # We should have the same number of transactions and fees
    assert len(transactions_data) == len(fees_data)

    log.info('Include fees in transaction data')
    transactions_data = Feeer.include_fees(transactions_data, fees_data)

    log.info('Include the gain tax FIFO calculations')
    transactions_data = Taxer.calculate_gain_fifo(transactions_data)

    log.info('Include the PCC tax calculations')
    transactions_data = Taxer.calculate_pcc(transactions_data)

    # Save as CSV
    output = args.transactions[:-4] + '_tax.csv'
    with open(output, 'w', newline='', encoding="utf-8") as csvoutput:
        csvwriter = csv.writer(csvoutput, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for row in transactions_data:
            csvwriter.writerow(row)
        csvwriter.writerow([])
        csvwriter.writerow(['* Prowizje od kupna kryptowaluty pobierane są w danej w kryptowalucie. '
                            'Przeliczanie na PLN odbywa się po kursie odpowiadającym transakcji '
                            'której prowizja dotyczy. Oznacza to natychmiastowe kupno i sprzedaż kryptowaluty '
                            'czyli brak dochodu do opodatkowania podatkiem dochodowym. '
                            'Podatek PCC zawiera prowizje dla trasakcji kupna.'])

    log.info('Done. CSV saved as: "{}"'.format(output))


if __name__ == '__main__':
    main()
