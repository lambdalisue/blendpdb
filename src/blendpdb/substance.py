#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
#
# Author:   Alisue (lambdalisue@hashnote.net)
# URL:      http://hashnote.net/
# Date:     2013-07-27
#
# (C) 2013 hashnote.net, Alisue
#
import os
import yaml
from decimal import Decimal


class Substance(object):
    """
    Substance

    Property:
        name -- a name of the substance
        longname -- full name of the substance
        density -- density of the substance (g/cm^3)
        molecular_weight -- molecular_weight of the substance (g/mol)
        pdb -- relative or absolute path of pdb
        coefficient -- density / molecular_weight

    Class method:
        find -- find the substance class registered by name
        register -- register new substance
        unregister -- remove the substance from the registration
    """
    def __init__(self, name, longname, density, molecular_weight, pdb):
        """Constructor

        Argument:
            name -- name of the substance
            longname -- full name of the substance
            density -- density of the substance (g/cm^3)
            molecular_weight -- molecular_weight of the substance (g/mol)
            pdb -- relative or absolute path of pdb
        """
        self.name = name
        self.longname = longname
        self.density = Decimal(str(density))                    # g/cm^3
        self.molecular_weight = Decimal(str(molecular_weight))  # g/mol
        self.pdb = pdb

    @property
    def coefficient(self):
        """coefficient [mol/m^3]"""
        if not hasattr(self, '_coefficient'):
            # [g/cm^3] * 10^6 / [g/mol] = [mol/m^3]
            self._coefficient = self.density * 10**6 / self.molecular_weight
        return self._coefficient

    @classmethod
    def find(cls, name):
        """find the instance of substance from name"""
        if hasattr(cls, '_substances') and name in cls._substances:
            return cls._substances[name]
        raise Exception("Substance name '%s' is not registered. Use '.blendrc'"
                        " to register the substance")

    @classmethod
    def register(cls, name, longname=None, density=None,
                molecular_weight=None, pdb=None):
        """
        Register new substance

        Argument:
            name -- name of the substance
            longname -- full name of the substance
            density -- density of the substance (g/cm^3)
            molecular_weight -- molecular_weight of the substance (g/mol)
            pdb -- relative or absolute path of pdb

        Returns:
            substance instance
        """
        if isinstance(name, cls):
            substance = name
        else:
            substance = cls(name, longname, density, molecular_weight, pdb)
        # Register the substance to cls list
        if not hasattr(cls, '_substances'):
            cls._substances = {}
        cls._substances[substance.name] = substance
        return substance

    @classmethod
    def unregister(cls, name):
        """
        Remove the substance from registration

        Argument:
            name -- name of the substance
        """
        if isinstance(name, cls):
            name = name.name
        # Unregister the substance to cls list
        if hasattr(cls, '_substances'):
            del cls._substances[name]


    @classmethod
    def load(cls, filename, encoding='utf-8', register=True):
        """
        Load substance configuration file

        Argument:
            filename -- a filename of the substance configuration file
            encoding -- encoding of the file
            register -- if True, register loaded substances

        Returns
            loaded substance instances
        """
        dirname = os.path.dirname(filename)

        def create_substance(name, data):
            pdb = data['pdb']
            if not os.path.isabs(pdb):
                # convert to absolute path
                pdb = os.path.normpath(os.path.join(dirname, pdb))
            return Substance(
                    name=name,
                    longname=data['longname'],
                    density=data['density'],
                    molecular_weight=data['molecular_weight'],
                    pdb=pdb
                )
        subs = yaml.load(open(filename, 'rb').read().decode(encoding))
        substances = []
        for key, value in subs.iteritems():
            sub = create_substance(key, value)
            if register:
                cls.register(sub)
            substances.append(sub)
        return substances

