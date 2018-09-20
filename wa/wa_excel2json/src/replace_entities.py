#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 16 10:26:36 2017

@author: Jason Jingshi Li

 ***************************************************************************
  * IBM Source Material
  * (C) COPYRIGHT International Business Machines Corp., 2017.
  *
  * The source code for this program is not published or otherwise divested
  * of its trade secrets, irrespective of what has been deposited with the
  * U. S. Copyright Office.
  ***************************************************************************

To run:
$ python3.6 replace_entities.py

Required: config file that specify where the data are: replace_entities_config.json
Expected output: replaced_entities_data.json or specified output file in config, with entities replaced

"""

import json
import wcs_workspace




# Main Method
if __name__ == "__main__":

    # Loading config from file stitching_config.json
    myWorkSpace = wcs_workspace.wcs_workspace('replace_entities_config.json')
    print ('Workspace loaded')

    outputFileName = 'replaced_entities_data.json'

    if 'Output File' in myWorkSpace.config:
        outputFileName = myWorkSpace.config['Output File']

    if 'Workspace Name' in myWorkSpace.config:
        print ('Updating workplace name to ' + myWorkSpace.config['Workspace Name'])
        myWorkSpace.set_workspace_name(myWorkSpace.config['Workspace Name'])

    # Replace the simple dialogs as specified above
    assert("New Entities" in myWorkSpace.config)

    myWorkSpace.config_add_entities(myWorkSpace.config['New Entities'])

    # Write to file
    print ('Writing to file ' + outputFileName)
    myWorkSpace.write_to_file(outputFileName)

