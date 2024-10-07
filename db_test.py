import sqlite3
import json
import time
import urllib.request

def getType(typeLine):
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
 
# Open (or create) database
connection = sqlite3.connect('oracle-cards.db')
cursor = connection.cursor()

# Scryfall Bulk Data Header
start = time.time()
try:
    datapointer = urllib.request.urlopen("https://api.scryfall.com/bulk-data/default-cards")
except IOError as e:
    print("Failed to get Default Cards list from Scryfall")
    if hasattr(e, 'code'):
        print('Code - {}.'.format(e.code))
    exit()
datapointer = json.load(datapointer)

# Scryfall Bulk Data Full JSON
uri = datapointer['download_uri']
filename = 'oracle-cards.json'
urllib.request.urlretrieve(uri, filename)

file = open('oracle-cards.json', encoding='UTF8')
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
            Img BLOB DEFAULT 0
        ); """
cursor.execute(table)

counter = 0
start = time.time()
for card in data:

    # Scan for reversible cards
    if card['layout'] == "reversible_card":
        subCard = card['card_faces'][0]
        cardType = getType(subCard['type_line'])
    else:
        cardType = getType(card['type_line'])

    # Format name (//)
    name = card['name']
    if "//" in name:
        idx = name.find("//")
        name = name[:idx]

    # Scan for arena cards
    if name[:2] == "A-":
        continue
    if 'paper' not in card['games']:
        continue


    cursor.execute("INSERT INTO ORACLE VALUES (?, ?, ?, ?)", [name, cardType, card['id'], 0])
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
