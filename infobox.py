import tkinter as tk
from tkinter import ttk
from PIL import ImageTk, Image
import urllib.request
import io
from pathlib import Path
import json

###########################################################################
# Class for getting the info for a given card
class InfoBox:

    cardSizeName = 'normal'
    cardSize = (488, 680) # scryfall image size

    def __init__(self, masterWindow, manager) -> None:
        self.db = manager

        self.selected = None
        self.json = None
        self.img = None

        # Image frame
        self.imgFrame = tk.Frame(master=masterWindow, highlightthickness=1, highlightbackground='black', width=self.cardSize[0], height=self.cardSize[1])
        self.imgFrame.grid_propagate(False)
        tk.Grid.rowconfigure(self.imgFrame, [0], weight=1)
        tk.Grid.columnconfigure(self.imgFrame, [0], weight=1)

        self.imgLabel = tk.Label(self.imgFrame, image=None)
        self.imgLabel.grid(column=0,row=0, sticky="nsew")

        # Info Text Frame
        self.textFrame = tk.Frame(master=masterWindow)
        self.textBox = tk.Text(self.textFrame, font=("consolas", "8", "normal"))
        self.textBox.grid(column=0,row=0,sticky='nsew')
        self.textBox.config(state='disabled')

        # Check for image storage
        self.imgDir = Path("{}\images".format(Path.cwd()))
        if not self.imgDir.exists():
            print("Created image directory at {}".format(self.imgDir))
            self.imgDir.mkdir(parents=True)
        else:
            print("Found img directory at {}".format(self.imgDir))

    ###################################
    # Sets a new card to be displayed
    def set(self, entry):
        

        if len(entry) == 4:
            scryId = entry[2]
        else:
            scryId = entry['id']

        try:
            data = urllib.request.urlopen("https://api.scryfall.com/cards/{}".format(scryId))
        except IOError as e:
            print("Could not find card with scryfall ID {}".format(scryId))
            if hasattr(e, 'code'):
                print('Code - {}.'.format(e.code))
            return
        
        self.card = entry
        self.json = json.load(data)
        self.updateText()
        
        if self.json['image_status'] == 'missing':
            print("Missing image")

        else:
            self.updateImg()

    ###################################
    # Updates the active image
    def updateImg(self):

        # Check for valid card JSON
        if self.json is None:
            return
        
        # Check to see whether the file is saved locally
        photo = self.getImageFromFile()
        if photo is None:
            photo = self.getImageFromScryfall()

        self.imgLabel.configure(image=photo)
        self.imgLabel.image=photo

    ###################################
    # Checks filesystem for image
    def getImageFromFile(self):
        path = "{}\{}.jpg".format(self.imgDir, self.json['id'])
        if not Path(path).exists():
            return None
        else:
            image = Image.open(path)
            image = image.resize(self.cardSize)
            return ImageTk.PhotoImage(image)

    ###################################
    # Gets an image from scryfall
    def getImageFromScryfall(self):

        # Check that the json has uris
        if 'image_uris' not in self.json:
            url = self.json['card_faces'][0]['image_uris'][self.cardSizeName]
        else:
            url = self.json['image_uris'][self.cardSizeName]

        # Get the image
        with urllib.request.urlopen(url) as u:
            raw_data = u.read()
        image = Image.open(io.BytesIO(raw_data))
        image = image.resize(self.cardSize)

        # Save permanently and return
        image.save("{}\{}.jpg".format(self.imgDir,self.json['id']))
        return ImageTk.PhotoImage(image)
        
    ###################################
    # Update the text in the text box
    def updateText(self):
        self.textBox.config(state='normal')
        self.textBox.delete('1.0', 'end')

        # Informational Text
        if len(self.card) > 4:
            self.textBox.insert('end', "{}\n".format(self.card['cardname']))
        else:
            self.textBox.insert('end', "{}\n".format(self.card[0]))
        self.textBox.insert('end', "Set: {} ({})\n".format(self.json['set_name'], self.json['set'].upper()))

        if len(self.card) > 4:
            self.textBox.insert('end', "-- Locations --\n")
            self.textBox.insert('end', "Found in {}\n".format(self.card['home']))

            if self.card['status'] == 'Sideboard':
                self.textBox.insert('end', "Sideboard for: {}\n".format(self.card['deck']))
            elif self.card['status'] == 'Commander':
                self.textBox.insert('end', "Commander for: {}\n".format(self.card['deck']))
            elif self.card['status'] == 'Mainboard':
                self.textBox.insert('end', "Mainboard for: {}\n".format(self.card['deck']))
            else:
                self.textBox.insert('end', "")

            self.textBox.insert('end', "-- Prices --\n")
            if self.json['prices']['usd'] != None:
                self.textBox.insert('end', "Regular: ${}\n".format(self.json['prices']['usd']))
            if self.json['prices']['usd_foil'] != None:
                self.textBox.insert('end', "Foil: ${}\n".format(self.json['prices']['usd_foil']))
            if self.json['prices']['usd_etched']  != None:
                self.textBox.insert('end', "Etched: ${}\n".format(self.json['prices']['usd_etched']))

            self.textBox.insert('end', "-- RAW --\n")
            self.textBox.insert('end', "{}\n".format(self.card))
            
        self.textBox.config(state='disabled')

    ###################################
    # Refresh info
    def reload(self, entry):
        self.card = entry
        self.updateText()
        