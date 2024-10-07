import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import sqlite3
from dbManager import dbManager
from pathlib import Path
from PIL import ImageTk, Image

###########################################################################
# Searchable list class for oracle list
class OracleManager:

    def __init__(self, window, fileName) -> None:
        self.connection = sqlite3.connect(fileName)
        self.cursor = self.connection.cursor()

        # Check for existing table
        res = self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ORACLE';")
        if len(res.fetchall()) < 1:
            print("ORACLE table not found")
            print("Please update card database")
            cmd = """ CREATE TABLE ORACLE (
                    Cardname TEXT NOT NULL,
                    Type TEXT NOT NULL,
                    Id TEXT NOT NULL,
                    Setcode TEXT NOT NULL
                ); """ #EMPTY
            self.cursor.execute(cmd)

        # Results & info variables
        self.results = []
        self.idx = 0

        # Pointer to target of adding/doubleclicking
        self.target = None

        # Pointer to card info manager
        self.info = None

        # Wishlist Button & Frame
        self.wishlist = False
        self.buttonFrame = tk.Frame(master=window)
        tk.Grid.columnconfigure(self.buttonFrame, [0,1], weight=1)

        self.lbl = tk.Label(master=self.buttonFrame, text="Wishlist Mode:")
        self.lbl.grid(column=0, row=1, sticky='e')

        self.btn = tk.Button(master=self.buttonFrame, text="OFF")
        self.btn.bind("<Button-1>", lambda e: self.toggle())
        self.btn.grid(column=1, row=1, sticky='w')

        self.buttonFrame.grid(column=0, row=1, sticky='ew')

        # Search frame
        self.listFrame = tk.Frame(master=window, height=150, width=75, relief=tk.RAISED)
        tk.Grid.rowconfigure(self.listFrame, [1], weight=1)
        tk.Grid.columnconfigure(self.listFrame, [0], weight=1)
        self.listFrame.grid(column=0, row=0, sticky='nsew')

        # Search String
        self.searchStr = tk.StringVar()
        self.searchStr.trace_add("write", lambda name, index, mode: self.searchCallback())

        # Search Bar
        self.ent_search = tk.Entry(master=self.listFrame, textvariable=self.searchStr)
        self.ent_search.grid(column=0, columnspan=2, row=0, sticky=(tk.W,tk.E))

        # Results List
        choicesvar = tk.StringVar()
        self.lbx_results = tk.Listbox(master=self.listFrame, height=10, listvariable=choicesvar, selectmode='browse')
        self.lbx_results.grid(column=0, row=1, sticky=(tk.N,tk.W,tk.E,tk.S))

        # Results Scrollbar
        s = ttk.Scrollbar(self.listFrame, orient=tk.VERTICAL, command=self.lbx_results.yview)
        self.lbx_results.configure(yscrollcommand=s.set)
        s.grid(column=1, row=1, sticky=(tk.N,tk.S))

        # Initial Search
        self.searchCallback()

        self.lbx_results.bind("<<ListboxSelect>>", lambda e: self.setSelected(-1, True))
        self.lbx_results.bind("<Double-1>", self.doubleClick)
        self.lbx_results.bind("<Return>", self.doubleClick)
        self.ent_search.bind("<Return>", self.doubleClick)
        self.ent_search.bind("<KeyRelease-Up>", lambda e: self.arrowFunc(-1))
        self.ent_search.bind("<KeyRelease-Down>", lambda e: self.arrowFunc(1))

    ###################################
    # Turns wishlist mode on/off
    def toggle(self):
        
        if self.wishlist == True:
            self.wishlist = False
            self.btn.config(text = "OFF")
        
        else:
            self.wishlist = True
            self.btn.config(text = "ON")
        
        self.reload()

    ###################################
    # Double click action (add to target)
    def doubleClick(self, arg1):
        
        if self.target is not None:
            if len(self.lbx_results.curselection()) > 0:
                self.target.addTo(self.results[self.lbx_results.curselection()[0]], self.wishlist)
                self.ent_search.selection_range(0, 'end')

    ###################################
    # Set the add destination on doubleclick
    def setTarget(self, obj):
        self.target = obj

    ###################################
    # Pulls the tuple for the selected card object
    def setSelected(self, targetIdx, pullInfo):

        # Default to not change selection
        if targetIdx != -1:
            
            self.lbx_results.selection_clear(0, 'end')

            # Check bounds (<0)
            if targetIdx < 0:
                self.lbx_results.selection_set(0, 0)
                self.lbx_results.see(0)

            # Check bounds (>max)
            elif targetIdx >= len(self.results):
                self.lbx_results.selection_set(len(self.results)-1, len(self.results)-1)
                self.lbx_results.see(len(self.results)-1)

            # Valid index
            else:
                self.lbx_results.selection_set(targetIdx, targetIdx)
                self.lbx_results.see(targetIdx)

        # Get 
        sel = self.lbx_results.curselection()

        if len(sel) > 0:

            if (pullInfo) and (self.info is not None):
                self.info.set(self.results[sel[0]])

    ###################################
    # function for when arrowkeys are pressed
    def arrowFunc(self, dir):

        idx = self.getIdx()
        self.setSelected(idx+dir, True)

    ###################################
    # gets the index of the selected list item
    def getIdx(self):
        sel = self.lbx_results.curselection()
        if len(sel) > 0:
            return sel[0]
        else:
            return -1

    ###################################
    # Handler for typing in the searchbar
    def searchCallback(self):

        # Get current search string
        strVar = self.ent_search.get()
        setName = ''

        if len(strVar) == 36:
            self.results = self.cursor.execute("SELECT * FROM ORACLE WHERE Id='{}' ORDER BY Cardname".format(strVar)).fetchall()

        else:

            # Check for SET search with @
            if '@' in strVar:
                strList = strVar.split('@')
                strVar = strList[0].strip()
                setName = strList[1].strip()

                #return if waiting for valid setname
                if len(setName) < 3:
                    return

            # Check length and format to SQL
            if strVar == "":
                strVar = "%"
            if "'" in strVar:
                strVar = strVar.replace("'","''")

            # Search the selected table/field
            self.results = self.cursor.execute("SELECT * FROM ORACLE WHERE Cardname LIKE '%{}%' ORDER BY Cardname".format(strVar)).fetchall()
        
        # Handle setname filtering if desired
        if setName != '':
            tempRes = []
            for r in self.results:
                if setName == r[3]:
                    tempRes.append(r)

            self.results = tempRes

        
        self.reload()

        # Autoselect top result, set as selected result
        self.lbx_results.selection_set(0)
        self.lbx_results.see(0)
        self.setSelected(0, True)

    ###################################
    # Refresh Listbox using current results
    def reload(self):
        
        # trim results to top X entries
        strRes = [item for item in self.results[:200]]

        # Repopulate the listbox
        self.lbx_results.delete(0, tk.END)
        for card in strRes:
            self.lbx_results.insert(tk.END, card[0])
            if self.wishlist:
                self.lbx_results.itemconfig(self.lbx_results.index("end")-1, {'bg':'#E1ABF1'})
            else:
                self.lbx_results.itemconfig(self.lbx_results.index("end")-1, {'bg':'white'})
        
    ###################################
    # Bind an info panel
    def bindInfo(self, info):
        self.info = info

###########################################################################
# Searchable list class for collection list
class SearchWindow:

    def __init__(self, masterWindow, bar, manager: dbManager):
        self.master = masterWindow
        self.db = manager
        self.listFrame = tk.Frame(master=masterWindow, height=150, width=75)
        tk.Grid.rowconfigure(self.listFrame, [1], weight=1)
        tk.Grid.columnconfigure(self.listFrame, [0], weight=1)

        self.info = None

        # Buttons
        w = 15
        h = 2
        self.buttonFrame = tk.Frame(master=masterWindow)
        #tk.Grid.rowconfigure(self.buttonFrame, [0,1], weight=1)
        tk.Grid.columnconfigure(self.buttonFrame, [0,1,2], weight=1)
        self.btn_delete = tk.Button(self.buttonFrame, text='Delete', bg='red', width=w, height=h, command=self.removeCard)
        self.btn_add = tk.Button(self.buttonFrame, text='>>', bg='green', width=w, height=h, command=lambda: self.doubleClick(None))
        self.btn_move = tk.Button(self.buttonFrame, text="Move", bg='blue', width=w, height=h, command=self.sendToLocation)
        self.btn_delete.grid(column=0,row=0)
        self.btn_add.grid(column=2,row=0)
        self.btn_move.grid(column=1, row=0)

        # Get all collections
        self.collections = self.db.getUnique('home')
        if 'Unsorted' not in self.collections:
            self.collections.insert(0, 'Unsorted')
        if 'Unowned' not in self.collections:
            self.collections.insert(0, 'Unowned')
        self.activeCollection = None

        # Combobox
        self.dropdown = ttk.Combobox(self.buttonFrame, state='readonly', values=self.collections)
        self.dropdown.grid(column=1, row=1)

        # Menu
        self.homeMenu = tk.Menu(bar)
        self.homeMenu.add_command(label="Add New", command=self.namePopup)
        self.homeMenu.add_separator()
        self.homeMenu.add_command(label='All', command=lambda: self.activateCollection(None))
        for c in self.collections:
            if len(c) > 0:
                self.homeMenu.add_command(label=c, command=lambda val=c: self.activateCollection(val))

        bar.add_cascade(label="Storage", menu=self.homeMenu)

        # Search String
        self.searchStr = tk.StringVar()
        self.searchStr.trace_add("write", lambda name, index,mode, var=self.searchStr: self.searchCallback(var))

        # Search Bar
        self.ent_search = tk.Entry(master=self.listFrame, textvariable=self.searchStr)
        self.ent_search.grid(column=0, columnspan=2, row=0, sticky=(tk.W,tk.E))

        # Results List
        choicesvar = tk.StringVar()
        self.lbx_results = tk.Listbox(master=self.listFrame, height=10, listvariable=choicesvar, exportselection=False)
        self.lbx_results.grid(column=0, row=1, sticky=(tk.N,tk.W,tk.E,tk.S))

        # Results Scrollbar
        s = ttk.Scrollbar(self.listFrame, orient=tk.VERTICAL, command=self.lbx_results.yview)
        self.lbx_results.configure(yscrollcommand=s.set)
        s.grid(column=1, row=1, sticky=(tk.N,tk.S))

        # Results print
        self.result_lbl = tk.Label(master=self.listFrame, text="")
        self.result_lbl.grid(column=0, row=2, columnspan=2, stick='we')

        # Initial Search
        self.reload("%")

        self.lbx_results.bind("<<ListboxSelect>>", lambda e: self.setSelected(-1, True))
        self.lbx_results.bind("<Double-1>", self.doubleClick)
        #self.ent_search.bind("<Return>", self.doubleClick)
        self.ent_search.bind("<KeyRelease-Up>", lambda e: self.arrowFunc(-1))
        self.ent_search.bind("<KeyRelease-Down>", lambda e: self.arrowFunc(1))

    ###################################
    # Display a popup for a new deck
    def namePopup(self):
        self.popup= tk.Toplevel(self.master)
        self.popup.geometry("250x150")
        self.popup.title("New Collection Name")
        tk.Label(self.popup, text= "Input new collection name:").pack()
        self.persistentString = tk.StringVar()
        tk.Entry(self.popup, textvariable=self.persistentString).pack()
        tk.Button(self.popup, text="CREATE", command=self.newCollection).pack()

    ###################################
    # Create a new deck
    def newCollection(self):

        # Check that the string has text
        if self.persistentString.get() == "":
            return
        
        # Check that the deck name does already exist
        for c in self.collections:
            if c == self.persistentString.get():
                return

        self.popup.destroy()

        newName = self.persistentString.get()

        # Create new DeckWindow
        self.collections.append(newName)
        self.dropdown.config(values=self.collections)
        self.homeMenu.add_command(label=newName, command=lambda name=newName: self.activateCollection(name))
        self.dropdown.configure(values=self.collections)
        self.dropdown.set(self.collections[len(self.collections)-1])
        self.activateCollection(newName)

    ###################################
    # Activate a collection
    def activateCollection(self, collection):
        self.activeCollection = collection
        self.searchStr.set('')
        self.reload(self.ent_search.get())

    ###################################
    # Doubleclick function (move to a deck)
    def doubleClick(self, obj):
        if self.target is not None:
            if len(self.lbx_results.curselection()) > 0:
                self.target.addTo(self.results[self.lbx_results.curselection()[0]])

    ###################################
    # Add to associated DB
    def addTo(self, entry, wish):
        if int(wish) == 1:
            newRow = self.db.addCard(entry[0], cardtype=entry[1], id=entry[2], wishlist=int(wish), home='Unowned')
        elif self.activeCollection is None:
            newRow = self.db.addCard(entry[0], cardtype=entry[1], id=entry[2], wishlist=int(wish), home='Unsorted')
        else:
            newRow = self.db.addCard(entry[0], cardtype=entry[1], id=entry[2], wishlist=int(wish), home=self.activeCollection)
        self.reload(self.ent_search.get(), newRow)

    ###################################
    # Pulls the tuple for the selected card object
    def setSelected(self, targetIdx, pullInfo):
        
        # Default to not change selection
        if targetIdx != -1:
            
            self.lbx_results.selection_clear(0, 'end')
            
            # Check bounds (<0)
            if targetIdx < 0:
                print("Uh-Oh, targetIdx= {}".format(targetIdx))
                # self.lbx_results.select_set(0)
                # self.lbx_results.activate(0)
                # self.lbx_results.see(0)

            # Check bounds (>max)
            elif targetIdx >= len(self.results):
                print("Uh-Oh, targetIdx= {}".format(targetIdx))
                # self.lbx_results.select_set(len(self.results)-1)
                # self.lbx_results.activate(len(self.results)-1)
                # self.lbx_results.see(len(self.results)-1)

            # Valid index
            else:

                self.lbx_results.select_set(targetIdx)
                self.lbx_results.activate(targetIdx)
                self.lbx_results.see(targetIdx)

        # Get 
        sel = self.lbx_results.curselection()

        if len(sel) > 0:

            if (pullInfo) and (self.info is not None):
                self.info.set(self.results[sel[0]])

    ###################################
    # function for when arrowkeys are pressed
    def arrowFunc(self, dir):

        idx = self.getIdx()
        self.setSelected(idx+dir, True)

    ###################################
    # gets the index of the selected list item
    def getIdx(self):
        sel = self.lbx_results.curselection()
        if len(sel) > 0:
            return sel[0]
        else:
            return -1

    ###################################
    # Handler for typing in the searchbar
    def searchCallback(self, var):

        # Reload with current string
        self.reload(var.get())

        # Set selection to top item
        self.setSelected(0, True)

    ###################################
    # Refresh selected
    def reload(self, searchStr, selectRow=-1):
        
        # Query DB
        if self.activeCollection is None:
            self.results = self.db.searchName(searchStr, limit=1000)
        else:
            self.results = self.db.searchName(searchStr, 'home', self.activeCollection, limit=1000)

        # Repopulate the listbox
        idxCount = 0
        idxTarget = -1
        self.lbx_results.delete(0, tk.END)
        for card in self.results:
            self.lbx_results.insert(tk.END, card['cardname'])
            if card['wishlist'] == 1:
                self.lbx_results.itemconfig(self.lbx_results.index("end")-1, {'bg':'#E1ABF1'})
            else:
                self.lbx_results.itemconfig(self.lbx_results.index("end")-1, {'bg':'white'})

            if card['rowId'] == selectRow:
                idxTarget = idxCount
            idxCount += 1
        self.result_lbl.configure(text="{} results for search '{}'".format(len(self.results), searchStr.replace('%', '')))

        if selectRow != -1:
            self.setSelected(idxTarget, True)
        
    ###################################
    # Edit CURRENT table
    def sendToLocation(self):
         
         # Check that there is a curerntly selected item
         if len(self.lbx_results.curselection()) > 0:

            # Check that the dropdown has a valid selection
            curIdx = self.dropdown.current()
            if curIdx >= 0:
                
                # Check that target & current are different
                card = self.results[self.lbx_results.curselection()[0]]
                if card['home'] != self.collections[curIdx]:

                    # Check whether the target is Unowned
                    if self.collections[curIdx] == 'Unowned':
                        self.db.editField(card['rowId'], 'wishlist', 1)

                    # Check whether the source is u
                    if card['home'] == 'Unowned':
                        self.db.editField(card['rowId'], 'wishlist', 0)

                    self.db.editField(card['rowId'], 'home', self.collections[curIdx])
                    print("Moved {} to {}".format(card['cardname'], self.collections[curIdx]))
                    self.reload(self.ent_search.get())
                    self.target.reload()

    ###################################
    # Remove from entire selection
    def removeCard(self):

        if len(self.lbx_results.curselection()) > 0:
            card = self.results[self.lbx_results.curselection()[0]]
            card = self.db.removeCard(card['rowId'])

            print("Removed {} from collection".format(card['cardname']))
            self.reload(self.ent_search.get())
            self.info.reload([card['cardname']])
            self.target.reload()

    ###################################
    # Set the add destination on doubleclick
    def setTarget(self, obj):
        self.target = obj

    ###################################
    # Bind an info panel
    def bindInfo(self, info):
        self.info = info

###########################################################################
# Organized List class for decks
class DeckWindow:

    headers = ["Commander", "Mainboard", "Sideboard"]
    basics = ["Plains", "Island", "Swamp", "Mountain", "Forest", "Wastes"]

    def __init__(self, masterWindow, bar, manager: dbManager):
        self.db = manager
        self.deckName = ""
        self.info = None
        self.menuBar = bar
        self.master = masterWindow
        self.treeFrame = tk.Frame(master=masterWindow, height=100, relief=tk.RAISED)
        tk.Grid.rowconfigure(self.treeFrame, [1], weight=1)
        tk.Grid.columnconfigure(self.treeFrame, [0], weight=1)

        # Control Frame
        self.buttonFrame = tk.Frame(master=masterWindow)
        self.btn_commander = tk.Button(self.buttonFrame, text="Set as Commander", command=lambda newTag="Commander": self.changeStatus(newTag))
        self.btn_mainboard = tk.Button(self.buttonFrame, text="Move to Mainboard", command=lambda newTag="Mainboard": self.changeStatus(newTag))
        self.btn_sideboard = tk.Button(self.buttonFrame, text="Move to Sideboard", command=lambda newTag="Sideboard": self.changeStatus(newTag))
        self.btn_delete = tk.Button(self.buttonFrame, text="Remove from Deck", background='red', command=lambda newTag="Delete": self.changeStatus(newTag))
        self.btn_commander.pack()
        self.btn_mainboard.pack()
        self.btn_sideboard.pack()
        self.btn_delete.pack()

        # Basics
        self.basicsFrame = tk.Frame(master=masterWindow, borderwidth=4, relief='raised')
        basicLabel = tk.Label(self.basicsFrame, text="Basic Lands")
        imageDir = Path("{}\icons".format(Path.cwd()))
        for idx in range(0,len(self.basics)):
            path = "{}\{}.webp".format(imageDir, self.basics[idx])
            image = Image.open(path)
            image = image.resize([20,20])
            image = ImageTk.PhotoImage(image)
            icon  = tk.Button(self.basicsFrame, image=image,height=30, width=30, command=lambda type=self.basics[idx]: self.createBasic(type))
            icon.image = image            
            icon.grid(column=int(idx%3), row=1+int(idx/3))
        basicLabel.grid(column=0,row=0,columnspan=3)
        
        # Decks
        self.decks = self.db.getUnique("deck")
        self.activeDeck = None

        self.deckMenu = tk.Menu(self.menuBar)
        self.deckMenu.add_command(label="Add New", command=self.namePopup)
        self.deckMenu.add_command(label="Save", command=lambda format="cod": self.saveToTxt(format))
        self.deckMenu.add_separator()
        for d in self.decks:
            if len(d) > 0:
                self.deckMenu.add_command(label=d, command=lambda name=d:self.openDeck(name))
        self.menuBar.add_cascade(label="Decks", menu=self.deckMenu)

        # Tree
        self.tree = ttk.Treeview(self.treeFrame, columns=('#', 'Name', 'entry'), selectmode='browse', show='headings', displaycolumns=['#', 'Name'])
        self.tree.grid(column=0, row=1,sticky=(tk.N,tk.W,tk.E,tk.S))
        self.tree.heading('#', text='#')
        self.tree.heading('Name', text='Card')
        self.tree.column(0, anchor=tk.CENTER, minwidth=20, width=20, stretch=False)

        self.tree.bind("<<TreeviewSelect>>", lambda e: self.setSelected())

        # Scrollbar
        s = ttk.Scrollbar(self.treeFrame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=s.set)
        s.grid(column=1, row=1, sticky=(tk.N,tk.S))

    ###################################
    # select a deck
    def openDeck(self, name):
        self.activeDeck = name
        self.reload()

    ###################################
    # (re)load the deck tree interface
    def reload(self):

        if self.activeDeck == None:
            return

        # clear current tree
        self.tree.delete(*self.tree.get_children())

        # Search for all cards in deck
        cards = self.db.searchDeck(self.activeDeck)

        # Print all 3 headers
        for header in self.headers:
            self.tree.insert('', 'end', header, text=0, open=True, values=[0,header, ''], tags=['header'])

        # Now add cards under headers as appropriate
        for card in cards:
            parent = card['status']+card['cardtype']
            
            if card['status'] == "Commander":
                parent = card['status']

            else:
                # Check for relevant type header
                if not self.tree.exists(parent):
                    self.tree.insert(card['status'], 'end', card['status']+card['cardtype'], text = 0, open=True, values=[0, card['cardtype'], ''], tags=['type'])

            # Even or Odd insertion
            colorTag = 'even'
            if len(self.tree.get_children(parent)) %2 == 1:
                colorTag = 'odd'
            if card['wishlist']:
                colorTag = 'wishlist'
                
            # Insert card
            self.tree.insert(parent, 'end', card['rowId'], text=1, values=[1, card['cardname'], card['rowId']], tags=[colorTag])

        # Set count values for headers & types
        for header in self.tree.get_children(''):
            headCount = 0

            if header == "Commander":
                headCount = len(self.tree.get_children(header))
                self.tree.item(header, values=[headCount, header, ''])

            else:
                for t in self.tree.get_children(header):
                    numChildren = len(self.tree.get_children(t))
                    label = self.tree.item(t, 'values')[1]
                    self.tree.item(t, values=[numChildren, label, ''])
                    headCount = headCount + numChildren

                self.tree.item(header, values=[headCount, header, ''])

        self.tree.tag_configure('header', background='#7F9CDF')
        self.tree.tag_configure('type', background='#90B1FF')
        self.tree.tag_configure('odd', background='#f0f0f0')
        self.tree.tag_configure('wishlist', background='#E1ABF1')
        self.tree.column(0, anchor=tk.CENTER, minwidth=20, width=20, stretch=False)

    ###################################
    # Change the number of generic basics
    def createBasic(self, type):

        if self.activeDeck == None:
            return

        cardName = "{} (Generic)".format(type)
        match type:
            case "Plains":
                id = '1d7dba1c-a702-43c0-8fca-e47bbad4a00f'
            case "Island":
                id = '0c4eaecf-dd4c-45ab-9b50-2abe987d35d4'
            case "Swamp":
                id = '8365ab45-6d78-47ad-a6ed-282069b0fabc'
            case "Mountain":
                id = '42232ea6-e31d-46a6-9f94-b2ad2416d79b'
            case "Forest":
                id = '19e71532-3f79-4fec-974f-b0e85c7fe701'
            case "Wastes":
                id = '7019912c-bd9b-4b96-9388-400794909aa1'
            case _:
                id =  -1

        self.db.addCard(name=cardName, cardtype='Land', id=id, home='Basic Lands',
                        deck=self.activeDeck, status='Mainboard')
        self.reload()

    ###################################
    # Add to current deck
    def addTo(self, entry):
        
        if self.activeDeck is not None:

            card = self.db.searchRowId(entry['rowId'])
            if card['deck'] == self.activeDeck:
                print("{} is already in deck \'{}\'".format(entry['cardname'], self.activeDeck))

            else:
                self.db.editField(entry['rowId'], 'deck', self.activeDeck)
                self.db.editField(entry['rowId'], 'status', 'Mainboard')
                print("Added {} to deck \'{}\'".format(entry['cardname'], self.activeDeck))
                self.reload()
                self.info.reload(entry)

    ###################################
    # Remove from current deck
    def deleteFrom(self, rowId):
        entry = self.db.editField(rowId, 'deck', '')
        entry = self.db.editField(rowId, 'status', '')
        print("Removed {} from deck \'{}\'".format(entry['cardname'], self.activeDeck))
        self.info.reload(entry)

    ###################################
    # Change card status
    def changeStatus(self, newTag):

        # Get currently selected item
        curItem = self.tree.focus()
        curItem = self.tree.item(curItem)
        rowId = curItem['values'][2]

        # Check that it isn't a category item or a basic land
        if ('header' not in curItem['tags']) and ('type' not in curItem['tags']):

            # Update status and reload
            if newTag == 'Delete':
                self.deleteFrom(rowId)
            else:                  
                card = self.db.editField(rowId, 'status', newTag)
                self.info.reload(card)
            self.reload()
    
    ###################################
    # Display a popup for a new deck
    def namePopup(self):
        self.popup= tk.Toplevel(self.master)
        self.popup.geometry("250x150")
        self.popup.title("New Deck Name")
        tk.Label(self.popup, text= "Input new deck name:").pack()
        self.persistentString = tk.StringVar()
        tk.Entry(self.popup, textvariable=self.persistentString).pack()
        tk.Button(self.popup, text="CREATE", command=self.newDeck).pack()

    ###################################
    # Create a new deck
    def newDeck(self):

        # Check that the string has text
        if self.persistentString.get() == "":
            return
        
        # Check that the deck name does already exist
        for d in self.decks:
            if d == self.persistentString.get():
                return

        self.popup.destroy()

        newName = self.persistentString.get()

        # Create new DeckWindow
        self.decks.append(newName)
        self.deckMenu.add_command(label=newName, command=lambda name=newName:self.openDeck(name))
        self.openDeck(newName)

    ###################################
    # Bind an info panel
    def bindInfo(self, info):
        self.info = info

    ###################################
    # Find the selected item
    def setSelected(self):
        if self.info is not None:
            curItem = self.tree.focus()
            curItem = self.tree.item(curItem)
            if ('header' not in curItem['tags']) and ('type' not in curItem['tags']):
                card = self.db.searchRowId(curItem['values'][2])
                self.info.set(card)

    ###################################
    # Save as a file
    def saveToTxt(self, format="raw"):

        if (self.activeDeck == None):
            return

        # Select file to save
        cockatrice = "C:\\Users\\Nathan\\AppData\\Local\\Cockatrice\\Cockatrice\\decks"
        f = filedialog.asksaveasfile(initialdir=cockatrice)

        # Search for all cards in deck
        cards = self.db.searchDeck(self.activeDeck)

        # Header for cockatrice .cod
        if format == "cod":
            f.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
            f.write("<cockatrice_deck version=\"1\">\n")
            f.write("\t<deckname>{}</deckname>\n".format(self.activeDeck))
            f.write("\t<comments></comments>\n")
            f.write("\t<zone name=\"main\">\n")


        # for each card in the deck,
        for card in cards:
            print(card)

            # make sure it is either commander or mainboard (do not export sideboard)
            if (card['status'] == "Commander") or (card['status'] == "Mainboard"):
                
                name = card['cardname']

                # Format generic basic correctly
                if ("(Generic)" in name):
                    print(card)
                    idx = name.find(' ')
                    name = name[:idx]
                    
                # Write to COD file
                f.write("\t\t<card number=\"1\" name=\"{}\"/>\n".format(name))
        
        # Closer for COD file
        if format == "cod":
            f.write("\t</zone>\n")
            f.write("</cockatrice_deck>\n")

        f.close()