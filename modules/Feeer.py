#!/usr/bin/env python3
# mk (c) 2018

from decimal import Decimal
from datetime import datetime
# https://docs.python.org/3/library/collections.html#collections.OrderedDict
from collections import OrderedDict

from modules.Taxer import Taxer

import logging
log = logging.getLogger('bitbay_tax_calculator')


class Feeer:
    """
    Class used by bitbay_tax_calculator.py
    """

    @staticmethod
    def include_fees(transactions_data, fees_data):
        """
        Obtain valid fees by combining transactions and fees data.
        Main issue here is that the fees are presented in different order than
         relevant transactions. We therefore group them by datetime, sort by value, match,
         and finally present in the natural order of transactions.

        :param transactions_data: All data from transactions CSV
        :param fees_data: All data from fees CSV
        :return: Transactions data with an additional row for fees
        """

        # Col indexes for some flexibility when CSV columns change
        tran_col_idx = Taxer.get_col_indexes(transactions_data)
        fees_col_idx = Feeer.get_col_indexes(fees_data)

        # Final container
        headers = transactions_data[0]
        headers.append('Prowizja')
        rows_with_fees = [headers]

        log.debug("==> Create a data structure good enough to combine transactions with proper fees")
        tran_groups = Feeer.group_entries_by_date(transactions_data, tran_col_idx)
        fees_groups = Feeer.group_entries_by_date(fees_data, fees_col_idx)
        Feeer.sanity_check_of_groups(tran_groups, fees_groups)

        log.debug('==> Combine groups')
        for i in range(0, len(tran_groups)):
            tran_group = tran_groups[i]
            fees_group = fees_groups[i]

            log.debug('Group: "{}"'.format(i))

            # Sort both groups by value to get mappings that we can use to connect them
            tran_order_given_to_value_map = Feeer.get_order_by_value_map(tran_group, tran_col_idx)
            fees_order_given_to_value_map = Feeer.get_order_by_value_map(fees_group, fees_col_idx)
            fees_order_value_to_given_map = {v: k for k, v in
                                             fees_order_given_to_value_map.items()}

            for tran_group_given_order_id in range(0, len(tran_group)):
                tran_row = tran_group[tran_group_given_order_id]

                tran_group_value_order_id = tran_order_given_to_value_map[tran_group_given_order_id]
                fees_group_given_order_id = fees_order_value_to_given_map[tran_group_value_order_id]

                fees_row_for_tran_row = fees_group[fees_group_given_order_id]
                log.debug('Transaction row: "{}"'.format(tran_row))
                log.debug('Corresponding fees row: "{}"'.format(fees_row_for_tran_row))

                # Finally, we can combine both rows
                combined_row = tran_row
                fee_value = fees_row_for_tran_row[fees_col_idx['Wartość']]
                if tran_row[tran_col_idx['Rodzaj']] == "Kupno":
                    cryptocur = tran_row[tran_col_idx['Rynek']][:3]
                    rate = tran_row[tran_col_idx['Kurs']]
                    fee_value_pln = Decimal(rate) * Decimal(fee_value)
                    fee_value_pln_str = str(fee_value_pln.quantize(Decimal(10) ** -2))
                    log.debug("Fee of {} in {} converted to PLN at rate {} gives {} PLN".format(fee_value, cryptocur,
                                                                                                rate, fee_value_pln_str))
                    combined_row.append(fee_value_pln_str)
                else:
                    combined_row.append(fee_value)

                log.debug('Combined row: "{}"'.format(combined_row))

                rows_with_fees.append(combined_row)

        return rows_with_fees

    @staticmethod
    def group_entries_by_date(data, col_indexes):
        """
        As we have no primary keys on transactions nor on the fees it's not so obvious how to
        connect them together. So we discover and follow some assumptions and hope they work.
        Therefore, we assume:
         * Transactions and groups of fees are sorted in the order of execution
         * For a given group of transactions or fees maximum time difference is minimal and depending on group size
         * Groups of transactions are executed in the same order as corresponding groups of fees

        Also check sanity_check_of_groups()

        :param data: List of lists - all the rows from the CSV file
        :param col_indexes: Fortunately looks like transactions and fees will both work here
        :return: List of lists of lists containing groups -> rows -> entries, keeping the order
        """

        log.debug('Grouping based on headers "header: index:" "{}"'.format(col_indexes))

        groups = []

        # Just for debugging
        overview = OrderedDict()

        # Initialise with data value from the first row (after headers)
        tmp_date = data[1][col_indexes['Data operacji']]

        tmp_group = []
        index = 0

        for row in data:
            # Ignore headers
            if row[col_indexes['Data operacji']] == 'Data operacji':
                continue

            # Dynamically adjust max time difference based on group length
            max_time_diff = (len(tmp_group) // 10) + 2

            if Feeer.is_within_time_diff(row[col_indexes['Data operacji']],
                                         tmp_date, max_time_diff):
                tmp_group.append(row)
            else:
                overview[tmp_date] = len(tmp_group)
                groups.append(tmp_group.copy())
                tmp_date = row[col_indexes['Data operacji']]
                tmp_group.clear()
                index = 0

                tmp_group.append(row)

            index += 1

        # Final group
        overview[tmp_date] = len(tmp_group)
        groups.append(tmp_group.copy())

        log.debug('Got "{}" groups: {}'.format(len(groups), overview))

        return groups

    @staticmethod
    def sanity_check_of_groups(tran_groups, fees_groups):
        """
        So we can be more certain out assumptions hold
        """

        log.debug('Sanity check of corresponding groups(of transactions and fees)')

        log.debug('Equal number of groups: "{}"'.format(len(tran_groups)))
        assert len(tran_groups) == len(fees_groups)

        log.debug("Equal number of entries in corresponding groups")
        for i in range(0, len(tran_groups)):
            assert len(tran_groups[i]) == len(fees_groups[i])

    @staticmethod
    def get_order_by_value_map(group, col_indexes):
        """
        param group: List of rows
        :return: A dict mapping given_order_id -> order_by_value_id
        """
        log.debug("Get sort by value map")

        # Target map
        given_to_value_order_map = {}

        # Convert the list into a dictionary: given_order_id -> entry
        given_order_dict = {}
        for i in range(0, len(group)):
            given_order_dict[i] = group[i]

        # .items() gives a tuple like (key, value)
        # lambda is a an anonymous function that for every item returns it's value[sort_index]
        value_based_index = 0
        sort_index = col_indexes['Wartość']
        for given_index, v in (sorted(given_order_dict.items(),
                                     key=lambda item: float(item[1][sort_index]))):
            given_to_value_order_map[given_index] = value_based_index
            value_based_index += 1

        Feeer.sanity_check_order_mapping(group, sort_index, given_to_value_order_map)

        return given_to_value_order_map

    @staticmethod
    def sanity_check_order_mapping(group, sort_index, map):
        values_by_given_order = [x[sort_index] for x in group]

        values_by_mapped_order = [None] * len(group)
        for i in range(0, len(values_by_given_order)):
            values_by_mapped_order[map[i]] = group[i][sort_index]

        log.debug('Mapping check')
        prev = values_by_mapped_order[0]
        for j in range(1, len(values_by_mapped_order)):
            assert float(prev) < float(values_by_mapped_order[j])

    @staticmethod
    def is_within_time_diff(date_a_str, date_b_str, max_time_diff):
        """
        :param date_a_str:
        :param date_b_str:
        :param max_time_diff:
        :return: True if given dates are close enough
        """
        date_format = '%d-%m-%Y %H:%M:%S'

        date_a_epoch = datetime.strptime(date_a_str, date_format).timestamp()
        date_b_epoch = datetime.strptime(date_b_str, date_format).timestamp()

        diff = abs(date_a_epoch - date_b_epoch)

        return diff < max_time_diff

    @staticmethod
    def get_col_indexes(data):
        """
        We want to be sure we are using the right columns for our calculations.
        Expecting something like this for the headers:

        #Data operacji;Rodzaj;Wartość;Saldo po

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
