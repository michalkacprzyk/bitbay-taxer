#!/usr/bin/env python3
# mk (c) 2018

from decimal import Decimal
from copy import deepcopy
from datetime import datetime

import logging
log = logging.getLogger('bitbay_tax_calculator')


class Taxer:
    """
    Class used by bitbay_tax_calculator.py
    """

    @staticmethod
    def calculate_gain_fifo(data):
        """
        :param self:
        :param data: List of lists containing all the data from the input CSV
        :return: Data with additional rows: 'income', 'cost' and 'gain' - required
         by polish tax statement
        """
        col_idx = Taxer.get_col_indexes(data)

        # We don't want to mess up with the order of transactions so will assume the data is sorted.
        # If the order is opposite to what we need (younger first) we reverse it

        # Lift up the headers
        headers = data.pop(0)

        date_format = '%d-%m-%Y %H:%M:%S'
        first_date = datetime.strptime(data[0][col_idx['Data operacji']], date_format)
        last_date = datetime.strptime(data[-1][col_idx['Data operacji']], date_format)

        if first_date > last_date:
            data.reverse()

        # Headers back
        data.insert(0, headers)

        # Calculations change data in progress, so we need a deep copy here
        data_deepcopy = deepcopy(data)

        for row in data:
            kind = row[col_idx['Rodzaj']]
            if kind == 'Rodzaj':  # Headers
                row.append('Przychód')
                row.append('Koszt')
                row.append('Dochód')
                continue

            if kind == 'Sprzedaż':
                # Tax is requirement activates at the moment of 'sell'
                gains = Taxer.get_gains_for_row(row, data_deepcopy)
                row.append(gains['income'])
                row.append(gains['cost'])
                row.append(gains['gain'])
            else:
                # For 'buy' transactions we just append empty values
                row.append('')
                row.append('')
                row.append('')

        return data

    @staticmethod
    def get_gains_for_row(sell_row, data_deepcopy):
        col_idx = Taxer.get_col_indexes(data_deepcopy)

        log.debug("==> Working with SELL row: {}".format(sell_row))
        sell_crypto = sell_row[col_idx['Rynek']]
        sell_amount = Decimal(sell_row[col_idx['Ilość']])
        sell_rate = Decimal(sell_row[col_idx['Kurs']])

        # Find the first relevant buy transaction(s) that are enough for the sell amount
        income = Decimal(0)
        cost = Decimal(0)
        for buy_row in data_deepcopy:
            # Buy rows only, valid crypto currency
            if buy_row[col_idx['Rynek']] != sell_crypto:
                continue
            if buy_row[col_idx['Rodzaj']] == 'Sprzedaż':
                continue

            buy_amount = Decimal(buy_row[col_idx['Ilość']])
            buy_rate = Decimal(buy_row[col_idx['Kurs']])
            if buy_amount == 0:  # Already used BUYs
                continue
            log.debug("Working with BUY row: {}".format(buy_row))

            remainder = sell_amount - buy_amount
            if remainder > 0:
                log.debug("Larger sell ({}) than buy ({}) amount (in this row)".format(sell_amount, buy_amount))
                income += buy_amount * sell_rate
                cost += buy_amount * buy_rate
                buy_row[col_idx['Ilość']] = str(Decimal(buy_row[col_idx['Ilość']]) - buy_amount)
                sell_amount -= buy_amount
            elif remainder < 0:
                log.debug("Larger buy ({}) than sell ({}) amount (in this row)".format(buy_amount, sell_amount))
                income += sell_amount * sell_rate
                cost += sell_amount * buy_rate
                buy_row[col_idx['Ilość']] = str(Decimal(buy_row[col_idx['Ilość']]) - sell_amount)
                break
            elif remainder == 0:
                log.debug("Exact match on buy and sell amount")
                income += sell_amount * sell_rate
                cost += buy_amount * buy_rate
                break

        gain = income - cost
        results = {
            'income': str(income.quantize(Decimal(10) ** -2)),
            'cost': str(cost.quantize(Decimal(10) ** -2)),
            'gain': str(gain.quantize(Decimal(10) ** -2)),
        }

        log.debug("Row final results: {}".format(results))
        return results

    @staticmethod
    def calculate_pcc(data):
        """
        PCC tax is just 1% of the BUY value, however it is rounded like that:
        values less than 0.5 PLN are becoming 0
        values equal and over 0.5 PLN are becoming +1
        :param self:
        :param data:
        :return:
        """
        col_idx = Taxer.get_col_indexes(data)

        for row in data:
            kind = row[col_idx['Rodzaj']]
            if kind == 'Rodzaj':  # Headers
                row.append('PCC')
                continue

            value = Decimal(row[col_idx['Wartość']])

            if kind == 'Kupno':
                # PCC tax from provision...
                value += Decimal(row[col_idx['Prowizja']])

                pcc = Decimal(value) * Decimal(0.01)
                # Rounding
                zlote = int(pcc)
                grosze = pcc % 1
                if grosze >= 0.50:
                    zlote += 1

                row.append(str(zlote))
            else:
                row.append('')

        return data

    @staticmethod
    def get_col_indexes(data):
        """
        We want to be sure we are using the right columns for our calculations.
        Expecting something like this for the headers:

        # Rynek;Data operacji;Rodzaj;Typ;Kurs;Ilość;Wartość;Prowizja

        :param data: List of lists containing all the data from the input CSV
        :return: Dictionary mapping column names to column index
        """

        col_index_dic = {}
        headers = data[0]
        index = 0
        for header in headers:
            col_index_dic[header] = index
            index += 1

        return col_index_dic
