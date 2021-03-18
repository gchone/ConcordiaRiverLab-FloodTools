# -*- coding: utf-8 -*-

### Historique des versions ###
# v0.1 - Fev 2020 - Création


class NumpyArrayFedObject(object):

    def __init__(self, numpyarray_holder):
        self.__numpyarray_holder = numpyarray_holder

    def __getattribute__(self, name):
        try:
            # retourne la valeur lue dans la matrice Numpy
            array = self.numpyarray_holder.__numpyarray
            # champ pour l'id:
            idfield = self.numpyarray_holder.__dict_attr_fields["id"]
            # champ pour la valeur:
            valuefield = self.numpyarray_holder.__dict_attr_fields[name]

            return array[array[idfield] == self.id][valuefield][0]
        except KeyError:
            # si ce n'est pas dans la matrice numpy, on regarde dans les attributs normaux
            return super(NumpyArrayFedObject, self).__getattribute__(name)

    def __setattr__(self, name, value):
        try:
            # change la valeur dans la matrice Numpy pour
            array = self.numpyarray_holder.__numpyarray
            # champ pour l'id:
            idfield = self.numpyarray_holder.__dict_attr_fields["id"]
            # champ pour la valeur:
            valuefield = self.numpyarray_holder.__dict_attr_fields[name]
            array[array[idfield] == self.id][valuefield] = value
        except KeyError:
            # si ce n'est pas dans la matrice numpy, on modifie les attributs normaux
            super(NumpyArrayFedObject, self).__setattr__(name, value)
