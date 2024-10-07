import sqlite3
import json
import time
import urllib.request
import tkinter as tk
import shutil
from pathlib import Path
import os

class dbUpdater:

    def __init__(self, bar, dbOracle, dbCollection, jsonFile) -> None:
        self.path = Path.cwd()
        
        self.dbCollection = dbCollection
        self.dbOracle = dbOracle
        self.jsonFile = jsonFile

        self.menu = tk.Menu(bar)
        self.menu.add_command(label="Update", command=lambda: self.updateFromScryfall())
        self.menu.add_command(label="Backup", command=lambda: self.dbBackup())
        bar.add_cascade(label="Database", menu=self.menu)

        self.target = None

    ###################################
    # Sets target for refresh
    def setTarget(self, obj):
        self.target = obj

    ###################################
    # Parses JSON card typeline
    def getType(self, typeLine):
        types = ["Creature", "Artifact", "Battle", "Enchantment", "Instant", "Land", "Planeswalker", "Sorcery"]
        line = typeLine

        # Check for double sided card marked by "name // name"
        if "//" in line:
            idx = line.find("//")
            line = line[:idx]

        # Scan for types in order
        for t in types:
            if t in line:
                return t

        # Default junk type
        return "Other"
 
    ###################################
    # Main Update Process
    def updateFromScryfall(self):
        print("--- UPDATING ORACLE DATABASE ---")
        connection = sqlite3.connect(self.dbOracle)
        cursor = connection.cursor()
        
        # Scryfall Bulk Data Header
        start = time.time()
        uri = "https://api.scryfall.com/bulk-data/default-cards"
        print("Getting Default Cards from {}".format(uri))
        try:
            datapointer = urllib.request.urlopen(uri)
        except IOError as e:
            print("Failed to get Default Cards list from Scryfall")
            if hasattr(e, 'code'):
                print('Code - {}.'.format(e.code))
            return
        datapointer = json.load(datapointer)
        
        # Scryfall Bulk Data Full JSON
        uri = datapointer['download_uri']
        urllib.request.urlretrieve(uri, self.jsonFile)

        file = open(self.jsonFile, encoding='UTF8')
        data = json.load(file)
        end = time.time()
        print("Refreshed cards from scryfall ({} sec)".format(end-start))
        
        # Delete table!
        start = time.time()
        res = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
        for t in res:
            cursor.execute("DROP TABLE IF EXISTS {}".format(t[0]))
        end = time.time()
        print("Deleted existing table ({} sec)".format(end-start))

        # Create Table
        table = """ CREATE TABLE ORACLE (
                    Cardname TEXT NOT NULL,
                    Type TEXT NOT NULL,
                    Id TEXT NOT NULL,
                    Setcode TEXT NOT NULL
                ); """
        cursor.execute(table)

        counter = 0
        start = time.time()
        for card in data:

            # Scan for reversible cards
            if card['layout'] == "reversible_card":
                subCard = card['card_faces'][0]
                cardType = self.getType(subCard['type_line'])
            else:
                cardType = self.getType(card['type_line'])

            # Format name
            name = card['name']

            # Scan for arena cards
            if name[:2] == "A-":
                continue
            if 'paper' not in card['games']:
                continue

            scryId  = card['id']
            setName = card['set']

            cursor.execute("INSERT INTO ORACLE VALUES (?, ?, ?, ?)", [name, cardType, scryId, setName])
            counter += 1
        end = time.time()
        print("Imported {} cards ({} sec)".format(counter, end-start))

        # Create index on Cardname
        start = time.time()
        cursor.execute("CREATE INDEX index_Cardname ON ORACLE (Cardname);")
        end = time.time()
        print("Created cardname index ({} sec)".format(end-start))

        # Exit
        connection.commit()
        connection.close()
        file.close()

        # Refresh Target db
        if self.target is not None:
            self.target.reload()

        # Delete json file
        try:
            os.remove(self.jsonFile)
            print("Deleted JSON file {}".format(self.jsonFile))
        except OSError:
            print("Failed to remove JSON file after update")
            pass

    def dbBackup(self):

        # Backup SQL Collection Database
        currentPath = Path('{}\{}'.format(self.path, self.dbCollection))
        backupPath  = Path('{}\collectionBackup.db'.format(self.path))
        shutil.copyfile(currentPath, backupPath)

        # Backup SQL Oracle Database
        currentPath = Path('{}\{}'.format(self.path, self.dbOracle))
        backupPath  = Path('{}\oracleBackup.db'.format(self.path))
        shutil.copyfile(currentPath, backupPath)
