#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
#
# Author:   lambdalisue (lambdalisue@hashnote.net)
# URL:      http://hashnote.net/
# License:  MIT license
# Created:  2013-05-07
#
import os
import math
import subprocess
from decimal import Decimal
from optparse import OptionParser

DEFAULT_CONFIGFILE = '~/.blendrc'
DEFAULT_SUBSTANCES = (
    ('WAT', 'Water', 1.0, 18.01, 'water.pdb'),
    ('TFE', '2,2,2-Trifluoroethanol', 1.393, 100.04, 'tfe.pdb'),
)

PACKMOL_TEMPLATE = """
#######################################################################

%(percentage)s%% (v/v) of %(rhs_longname)s with %(lhs_longname)s

#######################################################################

tolerance 2.0
output %(output)s

structure %(lhs_pdb)s
    number %(lhs_n)s
    inside cube -%(sideh)0.3f -%(sideh)0.3f -%(sideh)0.3f %(sidel)0.3f
end structure

structure %(rhs_pdb)s
    number %(rhs_n)s
    inside cube -%(sideh)0.3f -%(sideh)0.3f -%(sideh)0.3f %(sidel)0.3f
end structure
"""

# Avogadro constant (mol^-1)
Na = Decimal('6.02e+23')

class Substance(object):
    """Substance class

    Property:
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
        if isinstance(name, cls):
            substance = name
        else:
            substance = cls(name, longname, density, molecular_weight, pdb)
        # Register the substance to cls list
        if not hasattr(cls, '_substances'):
            cls._substances = {}
        cls._substances[substance.name] = substance

    @classmethod
    def unregister(cls, name):
        if isinstance(name, cls):
            name = name.name
        # Unregister the substance to cls list
        if hasattr(cls, '_substances'):
            del cls._substances[substance.name]


def load_substances(filename, encoding='utf-8', register=True):
    try:
        import yaml
    except:
        raise Warning("To enable loading configure file, install PyYAML")

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
            Substance.register(sub)
        substances.append(sub)
    return substances


def blend(a, b, percentage, min_total=500):
    # determine lhs, rhs
    if a.coefficient > b.coefficient:
        lhs = a
        rhs = b
        percentage = Decimal(percentage)
        reverse = False
    else:
        lhs = b
        rhs = a
        percentage = Decimal(100) - Decimal(percentage)
        reverse = True
    # find minimum numbers required
    k = (100 - percentage) / percentage
    m = rhs.coefficient / lhs.coefficient
    diff = lambda x: abs(round(x) - float(x))
    lhs_n = 1
    rhs_n = 0
    while True:
        rhs_n = k * m * lhs_n
        if diff(rhs_n) < 0.1 and rhs_n+lhs_n > min_total:
            break
        lhs_n += 1
    rhs_n = round(rhs_n)
    if not reverse:
        return lhs_n, rhs_n
    else:
        return rhs_n, lhs_n


def main():
    usage = """%prog SUB_A SUB_B PERCENTAGE [options]

Blend PERCENTAGE (v/v) of SUB_B with SUB_A"""
    parser = OptionParser(usage)
    parser.add_option('-c', '--config', metavar='FILE', default='blendrc',
            help="load configure from FILE (Default 'blendrc')")
    parser.add_option('-v', '--verbose', action='store_true', default=False,
            help="print informations")
    parser.add_option('-n', '--dry', action='store_true', default=False,
            help="do not create blended PDB ('-v' will automatically be set)")
    parser.add_option('-m', '--min-total', metavar='TOTAL', default=500,
            type='int',
            help="minimum total number of molecules (Default 500)")
    parser.add_option('-o', '--output', metavar='FILE',
            help="output blended PDB into FILE (Default "
                 "<PERCENTAGE>p_<SUB_B>.pdb)")
    opts, args = parser.parse_args()

    # Parse non ordeded arguments
    if len(args) != 3:
        raise Exception("Not enough arguments are gived. See help with '-h'")
    lhs = args[0]
    rhs = args[1]
    percentage = args[2]

    # Set default options if it's not specified
    if not opts.output:
        opts.output = percentage + "p_" + rhs.lower() + ".pdb"
    if opts.dry:
        # force to set -v
        opts.verbose = True

    # Add default substances
    for substance in DEFAULT_SUBSTANCES:
        Substance.register(*substance)
    # Load default config file
    if os.path.exists(DEFAULT_CONFIGFILE):
        load_substance(DEFAULT_CONFIGFILE)
        if opts.verbose:
            print "+ Loaded: '%s'" % DEFAULT_CONFIGFILE
    # Load custom substances
    if os.path.exists(opts.config):
        load_substances(opts.config)
        if opts.verbose:
            print "+ Loaded: '%s'" % opts.config
    if opts.verbose:
        bar_length = 80
        try:
            from tabulate import tabulate
            substance_table = []
            for s in Substance._substances.values():
                substance_table.append((
                    s.name, s.longname, s.density,
                    s.molecular_weight, s.pdb))
            substance_headers = (
                    'Name', 'Long-name', 'Density (g/cm^3)',
                    'Molecular Weight (g/mol)', 'PDB File')
            table = tabulate(substance_table, headers=substance_headers)
            bar_length = len(table.split("\n")[1])
            print
            print "=" * bar_length
            print "Available substance list".center(bar_length)
            print "=" * bar_length
            print table
        except ImportError:
            raise Warning("`tabulate` is required to be installed")

    # Find substance
    lhs = Substance.find(lhs)
    rhs = Substance.find(rhs)

    # Calculate the required number of molecules
    lhs_n, rhs_n = blend(lhs, rhs, percentage, opts.min_total)
    # Estimate required volume (meter -> Angstrom)
    lhs_v = Decimal(str(lhs_n)) / lhs.coefficient / Na * 10**30
    rhs_v = Decimal(str(rhs_n)) / rhs.coefficient / Na * 10**30
    sidel = math.pow(lhs_v + rhs_v, 1.0/3.0)

    if opts.verbose:
        print
        print "=" * bar_length
        print ("%s%% (v/v) of %s with %s," % (percentage, rhs.longname,
            lhs.longname)).center(bar_length)
        print "=" * bar_length
        print "%s:" % lhs.name, int(lhs_n), "molecules", "(%s)" % lhs.longname
        print "%s:" % rhs.name, int(rhs_n), "molecules", "(%s)" % rhs.longname
        print "BOX:", "%f A^3" % sidel, "(Estimated minimum bounding box)"

    # Create packmol input file
    kwargs = {
        'percentage': percentage,
        'output': opts.output,
        'lhs_name': lhs.name,
        'lhs_longname': lhs.longname,
        'lhs_pdb': lhs.pdb,
        'lhs_n': int(lhs_n),
        'rhs_name': rhs.name,
        'rhs_longname': rhs.longname,
        'rhs_pdb': rhs.pdb,
        'rhs_n': int(rhs_n),
        'sideh': sidel / 2,
        'sidel': sidel
    }
    packmol = PACKMOL_TEMPLATE % kwargs

    #if opts.verbose:
    #    print
    #    print "===================================================================="
    #    print "The following content is passed to packmol"
    #    print packmol
    #    print "===================================================================="


    # Execute packmol to create PDB file
    if not opts.dry:
        p = subprocess.Popen('packmol',
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE)
                #stderr=subprocess.STDOUT)
        p.communicate(packmol)
        p.stdin.close()
        if opts.verbose:
            print
            print "+ Created: '%s'" % opts.output

if __name__ == '__main__':
    main()
