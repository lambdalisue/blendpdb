blendpdb
===============================================================================

blendpdb is a tool for mixing two different substance to make solvate such as 50%
Ethanol.

Install
-------------------------------------------------------------------------------
Use pip or easy_install like

  pip install blendpdb

Usage
-------------------------------------------------------------------------------

    Usage: blendpdb SUB_A SUB_B PERCENTAGE [options]

    Blend PERCENTAGE (v/v) of SUB_B with SUB_A

    Options:
    -h, --help            show this help message and exit
    -c FILE, --config=FILE
                            load configure from FILE (Default '.blendrc')
    -v, --verbose         print informations
    -n, --dry             do not create blended PDB ('-v' will automatically be
                            set)
    -o FILE, --output=FILE
                            output blended PDB into FILE (Default
                            <PERCENTAGE>p_<SUB_B>.pdb)

`blendrc`
-------------------------------------------------------------------------------
To add different substance, create `blendrc` file in the working directory like

    WAT:                                # Name
      longname: Water                   # Long name
      density: 1                        # Density (g/cm^3)
      molecular_weight: 18.01           # Molecular Weight (g/mol)
      pdb: water.pdb                    # PDB file indicate the substance
    TFE:                                # Name
      longname: 2,2,2-Trifluoroethanol  # Long name
      density: 1.393                    # Density (g/cm^3)
      molecular_weight: 100.04          # Molecular Weight (g/mol)
      pdb: tfe.pdb                      # PDB file indicate the substance

blendpdb also try to load `.blendrc` file in your Home directory.
