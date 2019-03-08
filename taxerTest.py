#!/usr/bin/env python3
# mk (C) 2018
# Tests for the most important calculations

import unittest
from unittest import TestCase

from modules.Taxer import Taxer


class TaxerTest(TestCase):

    def test_get_gains_for_row_match_no_gain(self):
        data_lol = [
            ['Rynek', 'Data operacji', 'Rodzaj', 'Typ', 'Kurs', 'Ilość', 'Wartość'],
            ['BTC-PLN', 'some date', 'Kupno', 'some type', '1000', '1', '1000'],
            ['BTC-PLN', 'some date', 'Sprzedaż', 'some type', '1000', '1', '1000'],
        ]
        sell_row = data_lol[2]

        gains = Taxer.get_gains_for_row(sell_row, data_lol)
        self.assertEqual(gains, {'cost': '1000.00', 'gain': '0.00', 'income': '1000.00'})

    def test_get_gains_for_row_match_gain(self):
        data_lol = [
            ['Rynek', 'Data operacji', 'Rodzaj', 'Typ', 'Kurs', 'Ilość', 'Wartość'],
            ['BTC-PLN', 'some date', 'Kupno', 'some type', '1000', '1', '1000'],
            ['BTC-PLN', 'some date', 'Sprzedaż', 'some type', '2000', '1', '2000'],
        ]
        sell_row = data_lol[2]
        taxer = Taxer()
        gains = taxer.get_gains_for_row(sell_row, data_lol)
        self.assertEqual(gains, {'cost': '1000.00', 'gain': '1000.00', 'income': '2000.00'})

    def test_get_gains_for_row_match_loss(self):
        data_lol = [
            ['Rynek', 'Data operacji', 'Rodzaj', 'Typ', 'Kurs', 'Ilość', 'Wartość'],
            ['BTC-PLN', 'some date', 'Kupno', 'some type', '1000', '1', '1000'],
            ['BTC-PLN', 'some date', 'Sprzedaż', 'some type', '500', '1', '500'],
        ]
        sell_row = data_lol[2]
        taxer = Taxer()
        gains = taxer.get_gains_for_row(sell_row, data_lol)
        self.assertEqual(gains, {'cost': '1000.00', 'gain': '-500.00', 'income': '500.00'})

    def test_get_gains_for_row_larger_buy_no_gain(self):
        data_lol = [
            ['Rynek', 'Data operacji', 'Rodzaj', 'Typ', 'Kurs', 'Ilość', 'Wartość'],
            ['BTC-PLN', 'some date', 'Kupno', 'some type', '1000', '1', '1000'],
            ['BTC-PLN', 'some date', 'Sprzedaż', 'some type', '1000', '0.5', '500'],
            ['BTC-PLN', 'some date', 'Sprzedaż', 'some type', '1000', '0.5', '500'],
        ]
        sell_row = data_lol[2]
        taxer = Taxer()
        gains = taxer.get_gains_for_row(sell_row, data_lol)
        self.assertEqual(gains, {'gain': '0.00', 'income': '500.00', 'cost': '500.00'})

    def test_get_gains_for_row_larger_buy_some_gain(self):
        data_lol = [
            ['Rynek', 'Data operacji', 'Rodzaj', 'Typ', 'Kurs', 'Ilość', 'Wartość'],
            ['BTC-PLN', 'some date', 'Kupno', 'some type', '1000', '1', '1000'],
            ['BTC-PLN', 'some date', 'Sprzedaż', 'some type', '2000', '0.5', '1000'],
            ['BTC-PLN', 'some date', 'Sprzedaż', 'some type', '2000', '0.5', '1000'],
        ]
        sell_row = data_lol[2]
        taxer = Taxer()
        gains = taxer.get_gains_for_row(sell_row, data_lol)
        self.assertEqual(gains, {'gain': '500.00', 'income': '1000.00', 'cost': '500.00'})

    def test_get_gains_for_row_larger_sell_no_gain(self):
        data_lol = [
            ['Rynek', 'Data operacji', 'Rodzaj', 'Typ', 'Kurs', 'Ilość', 'Wartość'],
            ['BTC-PLN', 'some date', 'Kupno', 'some type', '1000', '0.5', '500'],
            ['BTC-PLN', 'some date', 'Kupno', 'some type', '1000', '0.5', '500'],
            ['BTC-PLN', 'some date', 'Sprzedaż', 'some type', '1000', '1', '1000'],
        ]
        sell_row = data_lol[3]
        taxer = Taxer()
        gains = taxer.get_gains_for_row(sell_row, data_lol)
        self.assertEqual(gains, {'income': '1000.00', 'cost': '1000.00', 'gain': '0.00'})

    def test_get_gains_for_row_larger_sell_some_gain(self):
        data_lol = [
            ['Rynek', 'Data operacji', 'Rodzaj', 'Typ', 'Kurs', 'Ilość', 'Wartość'],
            ['BTC-PLN', 'some date', 'Kupno', 'some type', '1000', '0.5', '500'],
            ['BTC-PLN', 'some date', 'Kupno', 'some type', '1000', '0.5', '500'],
            ['BTC-PLN', 'some date', 'Sprzedaż', 'some type', '2000', '1', '2000'],
        ]
        sell_row = data_lol[3]
        taxer = Taxer()
        gains = taxer.get_gains_for_row(sell_row, data_lol)
        self.assertEqual(gains, {'income': '2000.00', 'cost': '1000.00', 'gain': '1000.00'})


if __name__ == '__main__':
    unittest.main()
