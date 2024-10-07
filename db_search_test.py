import tkinter as tk

from dbManager import dbManager
from searchbox import SearchWindow
from searchbox import DeckWindow
from searchbox import OracleManager
from infobox import InfoBox
from logger import PrintLogger
from updater import dbUpdater

def motion(event):
    x, y = event.x, event.y
    #print('{}, {}'.format(x, y))
    dummyLabel.configure(text="Mouse : ({}, {})".format(x,y))

###############################################################################
# Begin TKinter Setup
window = tk.Tk()
window.title("Mockatrice")
window.state('zoomed')
tk.Grid.rowconfigure(window, [1], weight=1)
tk.Grid.columnconfigure(window, [0,1,3], weight=1)
window.option_add('*tearOff', tk.FALSE)

# Mouse coord indicator
window.bind('<Motion>', motion)
dummyLabel = tk.Label(window)
dummyLabel.grid(column=3, row=2)

# Menu Bar
menubar = tk.Menu(window)
window.config(menu=menubar)

###############################################################################
# LOGGER
logger = PrintLogger(window)
logger.frame.grid(columnspan=2,column=0,row=2, sticky='nswe')

###############################################################################
# DB Managers
db = dbManager('collection-cards.db', 'ORACLE')

###############################################################################
# SEARCH FRAMES

# General Collection (MY CARDS)
collectionSearch = SearchWindow(window, menubar, db)
collectionSearch.listFrame.grid(column=1, row=0, sticky='nsew')
collectionSearch.buttonFrame.grid(column=1, row=1, sticky='nsew')

# Oracle Database (ALL CARDS)
oracleSearch = OracleManager(window, 'oracle-cards.db')
oracleSearch.listFrame.grid(column=0, row=0, sticky='nsew')
oracleSearch.buttonFrame.grid(column=0, row=1, sticky='nsew')
oracleSearch.setTarget(collectionSearch)

###############################################################################
# DECK FRAME
deckManager = DeckWindow(window, menubar, db)
deckManager.treeFrame.grid(column=3, row=0, columnspan=4,rowspan=2, sticky='nsew')
deckManager.buttonFrame.grid(column=5, row=2, columnspan=2, sticky="news")
deckManager.basicsFrame.grid(column=3, row=2, columnspan=2, sticky='')
collectionSearch.setTarget(deckManager)

###############################################################################
# Image/Info FRAME
info = InfoBox(window, db)
oracleSearch.bindInfo(info)
collectionSearch.bindInfo(info)
deckManager.bindInfo(info)
info.imgFrame.grid(column=2, row=0, sticky="nsew")
info.textFrame.grid(column=2, row=1, sticky="nsew")

###############################################################################
# DB UPDATER
updater = dbUpdater(menubar, 'oracle-cards.db',
                    'collection-cards.db', 'oracle-cards.json')
updater.setTarget(oracleSearch)

###############################################################################
# END PROGRAM
window.mainloop()
db.commit()