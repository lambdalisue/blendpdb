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
import math
import tempfile
import subprocess
from decimal import Decimal
from optparse import OptionParser

from substance import Substance
from utils import insert_ter
from utils import blend_substances

DEFAULT_CONFIGFILE = '~/.blendrc'
DEFAULT_SUBSTANCES = (
    ('WAT', 'Water', 1.0, 18.01, 'water.pdb'),
    ('TFE', '2,2,2-Trifluoroethanol', 1.393, 100.04, 'tfe.pdb'),
)
# Avogadro constant (mol^-1)
Na = Decimal('6.02e+23')

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


def blendpdb():
    usage = """
    %prog SUB_A SUB_B PERCENTAGE [options]

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
        Substance.load(DEFAULT_CONFIGFILE)
        if opts.verbose:
            print "+ Loaded: '%s'" % DEFAULT_CONFIGFILE
    # Load custom substances
    if os.path.exists(opts.config):
        Substance.load(opts.config)
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
    lhs_n, rhs_n = blend_substances(lhs, rhs, percentage, opts.min_total)
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
    tmpfile = tempfile.mkstemp()[1]
    kwargs = {
        'percentage': percentage,
        'output': tmpfile,
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
        # insert TER in each
        with open(tmpfile, 'r') as fi, open(opts.output, 'w') as fo:
            for row in insert_ter(fi, residues=None):
                fo.write(row)
        if opts.verbose:
            print
            print "+ Created: '%s'" % opts.output

if __name__ == '__main__':
    blendpdb()

