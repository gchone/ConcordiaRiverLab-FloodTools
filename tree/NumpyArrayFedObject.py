# -*- coding: utf-8 -*-

### Historique des versions ###
# v0.1 - Fev 2020 - Création

class NumpyArrayFedObject(object):

    def __init__(self, numpyarray_holder):
        self.__numpyarray_holder = numpyarray_holder

    def __getattribute__(self, name):
        try:
            ### retourne la valeur lue dans la matrice Numpy (self.numpyarray_holder.__numpyarray) pour:
            ### id: self.id
            ### champ pour l'id: self.numpyarray_holder.__dict_attr_fields[self.id]
            ### champ pour la valeur: self.numpyarray_holder.__dict_attr_fields[name]
            return 0
        except:
            # si ce n'est pas dans la matrice numpy, on regarde dans les attributs normaux
            return super(NumpyArrayFedObject, self).__getattribute__(name)

    def __setattr__(self, name, value):
        try:
            ### change la valeur dans la matrice Numpy pour:
            ### id: self.id
            ### champ pour l'id: self.numpyarray_holder.__dict_attr_fields[self.id]
            ### champ pour la valeur: self.numpyarray_holder.__dict_attr_fields[name]
            pass
        except:
            # si ce n'est pas dans la matrice numpy, on modifie les attributs normaux
            super(NumpyArrayFedObject, self).__setattr__(name, value)
