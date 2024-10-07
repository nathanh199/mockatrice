import sqlite3

###########################################################################
# Searchable list class for oracle and collection lists
class dbManager:

    categories = ["cardname", "cardtype", "id", "home", "deck", "status", "wishlist", "rowId"]

    def __init__(self, fileName, tableName) -> None:
        self.connection = sqlite3.connect(fileName)
        self.cursor = self.connection.cursor()
        self.table = tableName

        # Check for existing table
        res = self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", [self.table])
        if len(res.fetchall()) < 1:
            print("Not found. Creating table {}".format(self.table))
            cmd = """ CREATE TABLE {} (
                    Cardname TEXT NOT NULL,
                    Cardtype TEXT NOT NULL,
                    Id TEXT NOT NULL,
                    Home TEXT NOT NULL,
                    Deck TEXT NOT NULL,
                    Status TEXT NOT NULL,
                    Wishlist INT DEFAULT 0
                ); """.format(self.table)
            self.cursor.execute(cmd)

    ###################################
    # Clear all tables # DISABLED
    def clearAll(self):
         res = self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
         for t in res:
             self.cursor.execute("DROP TABLE IF EXISTS {}".format(t[0]))
             print("Deleted table {}".format(t[0]))

    ###################################
    # Convert DB result to dictionary format
    def toDict(self, entry):
        
        dictionary = {}

        for i in range(len(self.categories)):
            dictionary[self.categories[i]] = entry[i]

        return dictionary
    
    ###################################
    # Search DB by Cardname
    def searchName(self, searchStr, searchField='', searchVal = '', limit=200):
        name = searchStr
        
        if searchField != '':
            if searchField not in self.categories:
                return []

        # Check length and format to SQL
        if name == "":
            name = "%"
        if "'" in name:
            name = name.replace("'","''")

        # Search the selected table/category
        if searchField == '':
            self.results = self.cursor.execute("SELECT *, ROWID FROM {} WHERE Cardname LIKE '%{}%' ORDER BY Cardname".format(self.table, name)).fetchall()
        else:
            self.results = self.cursor.execute("SELECT *, ROWID FROM {} WHERE Cardname LIKE '%{}%' AND {}=? ORDER BY Cardname".format(self.table, name, searchField), [searchVal]).fetchall()
        
        # trim results to top X entries, format to dictionary
        res = [self.toDict(item) for item in self.results[:limit]]

        return res
    
    ###################################
    # Search DB by rowId
    def searchRowId(self, searchId):
        self.results = self.cursor.execute("SELECT *, ROWID FROM {} WHERE rowid=?".format(self.table), [searchId]).fetchall()

        res = self.toDict(self.results[0])
        return res

    ###################################
    # Search DB by deck
    def searchDeck(self, searchStr):
        name = searchStr

        # Check length and format to SQL
        if name == "":
            name = "%"
        if "'" in name:
            name = name.replace("'","''")

        # Search the selected table/category
        self.results = self.cursor.execute("SELECT *, ROWID FROM {} WHERE Deck=? ORDER BY Cardtype, Cardname".format(self.table), [name]).fetchall()
        
        # trim results to top X entries, format to dictionary
        res = [self.toDict(item) for item in self.results]
        return res

    ###################################
    # Search DB by home
    def searchHome(self, searchStr):
        name = searchStr

        # Check length and format to SQL
        if name == "":
            name = "%"
        if "'" in name:
            name = name.replace("'","''")

        # Search the selected table/category
        self.results = self.cursor.execute("SELECT *, ROWID FROM {} WHERE Home=? ORDER BY Cardname".format(self.table), [name]).fetchall()
        
        # trim results to top X entries, format to dictionary
        res = [self.toDict(item) for item in self.results[:200]]

        return res

    ###################################
    # Get unique values from a specific field
    def getUnique(self, field, searchField='', searchVal = ''):

        if field not in self.categories:
            return []
        
        if (searchField != '' and
            searchField not in self.categories):
            return []

        if searchField == '':
            res = self.cursor.execute("SELECT DISTINCT {} FROM {} ORDER BY {}".format(field, self.table, field)).fetchall()
            res = [i[0] for i in res]
            return res
        else:
            res = self.cursor.execute("SELECT DISTINCT {} FROM {} WHERE {}=? ORDER BY {}".format(field, self.table, searchField, field), [searchVal]).fetchall()
            res = [i[0] for i in res]
            return res

    ###################################
    # Edit a given field
    def editField(self, rowId, field, newVal):

        if field not in self.categories:
            return {}

        # Make sure such an item exists
        res = self.cursor.execute("SELECT *, ROWID FROM {} WHERE rowid=?".format(self.table), [rowId]).fetchall()
        if len(res) > 0:
            self.cursor.execute("UPDATE {} SET {}=? WHERE rowid=?".format(self.table, field), [newVal, rowId])
            return self.toDict(res[0])
        
        else:
            return -1
    
    ###################################
    # Add a card entry with given params
    def addCard(self, name, cardtype="", id=0, home="Unsorted", deck="", status="", wishlist=0):

        self.cursor.execute("INSERT INTO {} VALUES (?, ?, ?, ?, ?, ?, ?)".format(self.table), [name, cardtype, id, home, deck, status, wishlist])
        print("Added card '{}' to {}".format(name, home))
        return self.cursor.lastrowid
        
    ###################################
    # Remove a card by rowid, return entry
    def removeCard(self, rowId):

        card = self.searchRowId(rowId)

        self.cursor.execute("DELETE FROM {} WHERE rowid=?".format(self.table), [rowId])

        return card

    ###################################
    # Commit DB changes
    def commit(self):
        self.connection.commit()