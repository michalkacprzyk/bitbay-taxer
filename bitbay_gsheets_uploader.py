#!/usr/bin/env python3
# mk (c) 2018

from modules.GSheetsUploaderHelper import GSheetsUploaderHelper
import csv
import argparse


# Command line call

ap = argparse.ArgumentParser(description='Program uploads a CSV file into Google Sheets. '
                                         'Also, does some formatting')

ap.add_argument('csvfile', help='A CSV file. Likely full output of bitbay_tax_calculator ')
ap.add_argument('clientsecret', help='A service account JSON file, its email is added to'
                                     ' shared in the sheets we access')
ap.add_argument('sheet_id', help='Obtained from the sheet URL. Sheet needs to be set to'
                                 ' locale: UK, to have some sensible data formating.')

args = ap.parse_args()

# Action

print("[i] Load data form CSV")
data = []
with open(args.csvfile, newline='') as csvfile:
    cr = csv.reader(csvfile, delimiter=';')
    for row in cr:
        data.append(row)

print("[i] Open a sheet and get properties")
g_sheet = GSheetsUploaderHelper(args.clientsecret, args.sheet_id)
print(g_sheet.get_sheet_properties())

print("[i] Update document title")
g_sheet.update_document_title("bitbay.net Podatek (auto)")

print("[i] Update sheet title")
g_sheet.update_sheet_title(0, "Transakcje (auto)")

g_sheet.format_header()

print("[i] Upload data")
sheet_cols_names = list('A B C D E F G H I J K L M N O P Q R S T U V'.split())
rows_nr = len(data)
cols_nr = len(data[0])

my_range = 'A1:{}{}'.format(sheet_cols_names[cols_nr], rows_nr)
g_sheet.write_data(data, my_range, 'USER_ENTERED')

print("[i] Format values")
g_sheet.format_values(rows_nr)

print("[i] Done")
