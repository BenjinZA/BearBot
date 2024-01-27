import os
import pickle
import random


class truth:

    def __init__(self):
        if os.path.isfile('users/truths.txt'):
            self.truths = pickle.load(open('users/truths.txt', 'rb'))
        else:
            self.truths = []
            self.truths.append('%s se uncle vat aan hom')
            self.truths.append('%s het \'n klein tollie')
            self.truths.append('%s geniet \'n lekker boud kap')
            self.truths.append('%s vat aan klein kinders')
            self.truths.append('%s loer vir jou van die bosse')
            self.truths.append('%s was deur die kakgat gebore')
            self.truths.append('%s het lekker man titties')
            self.truths.append('%s pis nog in sy broek')
            self.truths.append('%s is maar bloot eenvoudig, net \'n poes')
            self.truths.append('%s gorrel graag spytkak')

    def storeTruth(self, newTruth):
        self.truths.append('%s ' + newTruth)

        pickle.dump(self.truths, open('users/truths.txt', 'wb'))

    def returnTruth(self, user):
        r = random.randint(0, len(self.truths)-1)

        return self.truths[r] % user

    def deleteTruth(self, truth_number):
        del self.truths[truth_number]

        pickle.dump(self.truths, open('users/truths.txt', 'wb'))
