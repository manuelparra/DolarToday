#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    @decription: using dolartoday API for show the value of dollar in
    Venezuela
    @author: Manuel Parra
    @date: 04/01/19
"""

# import the header files
from datetime import date
from urllib.request import Request, urlopen
from sys import exit
import ssl
import json
import sqlite3
import nettest

# database for storage data in the hhd
conn = sqlite3.connect('dtdb.sqlite')
cur = conn.cursor()

cur.executescript('''
    CREATE TABLE IF NOT EXISTS Label (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        label TEXT UNIQUE
    );

    CREATE TABLE IF NOT EXISTS Historical (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        id_label INTEGER,
        value FLOAT,
        rdate DATE,
        UNIQUE(id_label, value, rdate),
        FOREIGN KEY (id_label) REFERENCES Label(id)
    );
''')

# testing the Internet connections
print("Testing your Internet connection, please wait")

firsthost = '8.8.8.8'
secondhost = '8.8.4.4'

tc = nettest.chargetest([firsthost, secondhost])
if not tc.isnetup():
    print("Your Internet connection is down!. We can't continue")
    exit()

# ignorate SSL certificate
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# get the json data
url = "https://s3.amazonaws.com/dolartoday/data.json"
print("Retrieving data from", url)

try:
    html = urlopen(Request(url, headers={'User-Agent': 'Mazilla/5.0'}),
                   context=ctx).read().decode('utf-8')
except:
    print("Error to get the URL! That web isn't avalibled")
    exit()

# if don't get any error, we have data retrieved in html object
print("Retrieved", len(html), "characters")

# process html data to get json
try:
    js = json.loads(html)
except:
    js = None

if not js:
    print("****** Failure to retrieve ******")
    print(html)
    exit()

labels = [('USD', ), ('EUR', )]

value_usd = js['USD']['dolartoday']
value_eur = js['EUR']['dolartoday']

cur.executemany('''
    INSERT OR IGNORE INTO Label (label)
    VALUES (?)
''', labels)

cur.execute('''
    SELECT id
    FROM Label
    WHERE label = ?
''', ('USD', ))
id_usd = cur.fetchone()[0]

cur.execute('''
    SELECT id
    FROM Label
    WHERE label = ?
''', ('EUR', ))
id_eur = cur.fetchone()[0]

today = date.today()
dolartoday = [(id_usd, value_usd, today),
              (id_eur, value_eur, today)]

cur.executemany('''
    INSERT OR IGNORE INTO Historical (id_label,
    value, rdate)
    VALUES (?, ?, ?)
''', dolartoday)

conn.commit()
cur.close()

print(labels[0][0], dolartoday[0][1])
print(labels[1][0], dolartoday[1][1])
print("Finish!")
