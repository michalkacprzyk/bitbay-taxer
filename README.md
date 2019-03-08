# bitbay-taxer

## What is?
A set of tools to semi-automatically deal with Polish TAX calculations involved in trading
of crypto assets on bitbay.net.

## What for?
For some reason nobody made it easy for a trader to correctly calculate taxes.

### Analysis
There are multiple issues:

- Export to CSV is limited only to three months
  - Therefore, it is mostly useless, unless somebody periodically downloads it
  - Also, it is in different format than the one displayed on the webpage
- Export via API is also limited
  - Maybe it is possible to manually bootstrap the data and then create a cronjob to keep it updated?
    - Nope, operations export is limited to just 200 entries, so it's possible to have a single transaction bigger than that...
- Exported data does not contain an ID, and there are multiple transactions with the same datatime mark
  - Assume that the given order is correct (avoid resorting)
- Export of transactions does not contain fees
  - There is a separate operations page that contains fees
    - But it's not trivial to connect them with relevant transactions
      - But it is possible by grouping by date (up to few seconds) and sorting by value
  - It is possible to download some invoices regarding fees, but those are incomplete and limited only to fees in PLN
    - Some fees are taken in crypto

## How to?
All steps assume that we are in the cloned directory of this repository.


### Preparations (optional)
This step is required if we are interested in automatic creation of a Google Sheet containing calculated data.

  1. Create a new Sheet in Google Drive and copy **ID** from the **URL** (sample **ID** below)
      - **File -> Spreadsheets settings -> Locale United Kingdom** (unofficial in PL but good looking combination of date and currency formatting)
  2. Go to: https://developers.google.com/sheets/api/quickstart/python
      - Enable the Google Sheets API and download **credentials.json** file

```bash
python3 -m venv venv3
source venv3/bin/activate

pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### Execution procedure
  1. Create (or download from a safe storage) **user_data** directory, locate the last transaction
  2. Login to the web interface of (bitbay.net)
  3. Go to **history -> operations -> fees**
  4. Copy and paste all the new entries on top of: **user_data/fees_history.txt**
      - (Recommended) Make screenshots of all the pages involved in **user_data/scr/operations**
  5. Go to **history -> transactions**
  6. Copy and paste all the new entries on top of: **user_data/transactions_history.txt**
      - (Recommended) Make screenshots of all the pages involved in **user_data/scr/transactions**
  7. Execution example for **sample_data** directory

```bash
./bitbay_history_converter_txt_2_csv.py sample_data/fees_history.txt fees
./bitbay_history_converter_txt_2_csv.py sample_data/transactions_history.txt transactions
./bitbay_tax_calculator.py sample_data/transactions_history.csv sample_data/fees_history.csv --logfile update.log
./bitbay_gsheets_uploader.py sample_data/transactions_history_tax.csv sample_data/credentials.json 1KFsAUsowdp-S0iYv4nqHaj1_g68xpKwbIn6aba79tBg
```
  8. Copy **user_data** into a safe storage

## What if?
  - The code was created and tested on [Linux Mint](https://linuxmint.com/)
    - Python 3.6.7
