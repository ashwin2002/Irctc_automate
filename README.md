# Irctc_automate
Irctc site automation using Python Selenium
This code supports CITIBANK payment gateway

Pre requisites:
  1. Python 2.7
  2. Selenium
  3. SendKeys

Installing Required packages:
  1. Install selenium using 'pip install selenium'
  2. Install SendKeys using 'pip install sendkeys'


Usage: python irctc_automate.py irctcUserId profileFile book|cancel|status [options]
Options:
  -h, --help            show this help message and exit
  -d DATE, --date=DATE  Use this DATE for ticket booking
  --pnr=PNR_NUMBER      User this PNR_NUMBER for cancel or status enquiry  

Fill the required data in the default_profile.ini files with required data and run the code.

Below are the help regarding the profile.ini file sections:

[JOURNEY] section, valid 'class' format:
  # SL/1A/2A/3A/CC

[JOURNEY] section, 'phoneNumForSMS' dafault value will book with pre-defined phone number

[PASSENGERS] section format:
  # name;age;gender;berth_preference;senior_citizen;nationality;id_card_number
    name;age;male/female;middle/upper/lower/side lower/side upper;yes/no;Indian;1234567890

[CHILDREN] section format:
  # name;age;gender
    name;age;male/female

[PAYMENT] section, valid 'mode' values:
  # preferred/aggregator/debit_card/netbanking/scan_and_pay/cash_card/irctc_prepaid/e_wallet/cod/credit_card
