import os
import pickle


class steamID:

    def __init__(self):
        if os.path.isfile('users/steamIDs.txt'):
            self.steamIDs = pickle.load(open('users/steamIDs.txt', 'rb'))
        else:
            self.steamIDs = dict()

        if os.path.isfile('users/nameLinks.txt'):
            self.nameLinks = pickle.load(open('users/nameLinks.txt', 'rb'))
        else:
            self.nameLinks = dict()

    def storeSteamID(self, dID, newID):
        self.steamIDs[dID] = newID

        pickle.dump(self.steamIDs, open('users/steamIDs.txt', 'wb'))

    def storeDiscordID(self, name, dID):
        self.nameLinks[name] = dID

        pickle.dump(self.nameLinks, open('users/nameLinks.txt', 'wb'))

    def returnSteamID(self, dID):
        try:
            ID = self.steamIDs[dID]
        except:
            ID = -1
        return ID

    def returnDiscordID(self, name):
        try:
            ID = self.nameLinks[name]
        except:
            ID = -1
        return ID

    def noID(self, name):
        return 'No Steam ID stored for user %s. Please use steamID command with a valid Steam ID' % name
