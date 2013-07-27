#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
#
# Author:   Alisue (lambdalisue@hashnote.net)
# URL:      http://hashnote.net/
# Date:     2013-07-27
#
# (C) 2013 hashnote.net, Alisue
#
from decimal import Decimal


def insert_ter(iterator, residues=None):
    """
    Insert 'TER' after each residue specified

    Arguments:
        iterator -- a target iterator
        residues -- a list of residues or None (for all residues)

    Returns:
        iterator
    """
    prev_resinum = None
    for row in iterator:
        rowtype = row[0:4]
        residue = row[17:20]
        resinum = row[23:26]
        if rowtype in ['ATOM', 'HETATM']:
            if residues is None or residue in residues:
                if prev_resinum is not None and prev_resinum != resinum:
                    yield "TER\n"
                prev_resinum = resinum
        yield row


def blend_substances(a, b, percentage, min_total=500):
    """
    Blend two substance (A and B) in percentage (v/v)

    Arguments:
        a -- substance A
        b -- substance B
        percentage -- a percentage of substance B
        min_total -- minimum number of total molecules

    Returns:
        [Na, Nb] - a list of number of each substance molecules required
    """
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
