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
    ('WAT', 'Water', 1000000, 18.01, 'water.pdb'),
    ('TFE', '2,2,2-Trifluoroethanol', 1393000, 100.04, 'tfe.pdb'),
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
    def __init__(self, name, longname, density, molecular_weight, pdb):
        self.name = name
        self.longname = longname
        self.density = Decimal(str(density))                    # g/m^3
        self.molecular_weight = Decimal(str(molecular_weight))  # g/mol
        self.pdb = pdb

    @property
    def coefficient(self):
        return self.density / self.molecular_weight

    @classmethod
    def find(cls, name):
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

    def create_substance(name, data):
        return Substance(
                name=name,
                longname=data['longname'],
                density=data['density'],
                molecular_weight=data['molecular_weight'],
                pdb=data['pdb'],
            )
    subs = yaml.load(open(filename, 'rb').read().decode(encoding))
    substances = []
    for key, value in subs.iteritems():
        sub = create_substance(key, value)
        if register:
            Substance.register(sub)
        substances.append(sub)
    return substances


def blend(a, b, percentage):
    # determine lhs, rhs
    if a.coefficient > b.coefficient:
        lhs = a
        rhs = b
        percentage = Decimal(percentage)
        reverse = False
    else:
        lhs = b
        rhs = a
        percentage = Decimal(100 - percentage)
        reverse = True
    # find minimum numbers required
    k = percentage / (100 - percentage)
    m = lhs.coefficient / rhs.coefficient
    diff = lambda x: abs(round(x) - float(x))
    lhs_n = 1
    rhs_n = 0
    while True:
        rhs_n = k * m * lhs_n
        if rhs_n > 1 and diff(rhs_n) < 0.1:
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
            print "'%s' config file is loaded" % DEFAULT_CONFIGFILE
    # Load custom substances
    if os.path.exists(opts.config):
        load_substances(opts.config)
        if opts.verbose:
            print "'%s' config file is loaded" % opts.config
    if opts.verbose:
        print
        print "The following substances are registered"
        print "----------------------------------------------------------------"
        print "Name", "Long-name", "Density", "Molecular weight", "PDB"
        print "----------------------------------------------------------------"
        for s in Substance._substances.values():
            print s.name, s.longname, s.density, s.molecular_weight, s.pdb

    # Find substance
    lhs = Substance.find(lhs)
    rhs = Substance.find(rhs)

    # Calculate the required number of molecules
    lhs_n, rhs_n = blend(lhs, rhs, percentage)
    # Estimate required volume (Angstrom)
    lhs_v = Decimal(str(lhs_n)) / lhs.coefficient / Na * 10**30
    rhs_v = Decimal(str(rhs_n)) / rhs.coefficient / Na * 10**30
    sidel = math.pow(lhs_v + rhs_v, 1.0/3.0)

    if opts.verbose:
        print
        print "===================================================================="
        print "To create %s%% (v/v) of %s with %s," % (
                percentage, rhs.longname, lhs.longname)
        print "you need following each molecules"
        print
        print "%s:" % lhs.name, int(lhs_n), "molecules", "(%s)" % lhs.longname
        print "%s:" % rhs.name, int(rhs_n), "molecules", "(%s)" % rhs.longname
        print
        print "The estimated minimum bounding box of the mixture is"
        print
        print "BOX:", "%f A^3" % sidel
        print
        print "===================================================================="

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

    if opts.verbose:
        print
        print "===================================================================="
        print "The following content is passed to packmol"
        print
        print packmol
        print
        print "===================================================================="


    # Execute packmol to create PDB file
    if not opts.dry:
        p = subprocess.Popen('packmol',
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT)
        p.communicate(packmol)
        p.stdin.close()
        if opts.verbose:
            print "'%s' is created." % opts.output

if __name__ == '__main__':
    main()
