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
$ python3.6 replace_simple_answers.py

Required: config file that specify where the data are: replace_simple_answers_config.json
Expected output: replace_simple_answers_data.json in the current working directory, or output
JSON file specified in the config file, with all simple answers specified in the config file replaced.

"""

from excel_reader import load_xl
import re
import json
import datetime
import csv
import sys
import ingestion
import csv, xlwt
import wcs_workspace




# Main Method
if __name__ == "__main__":

    sys.setrecursionlimit(5000)

    # Loading config from file stitching_config.json
    myWorkSpace = wcs_workspace.wcs_workspace('replace_simple_answers_config.json')

    outputFileName = 'replaced_simple_answers_data.json'

    if 'Output File' in myWorkSpace.config:
        outputFileName = myWorkSpace.config['Output File']

    if 'Workspace Name' in myWorkSpace.config:
        print ('Updating workplace name to ' + myWorkSpace.config['Workspace Name'])
        myWorkSpace.set_workspace_name(myWorkSpace.config['Workspace Name'])

    # Replace the simple dialogs as specified above
    assert("Stitching Nodes" in myWorkSpace.config)
    for item in myWorkSpace.config['Stitching Nodes']:
        assert('prune_topic' in item)
        assert('prune_node' in item)
        topic_item = item['prune_topic']
        prune_node = item['prune_node']
        print ('Pruning child node of "'+ prune_node + '" with contents of "' + topic_item + '"')
        myWorkSpace.replace_dialogs(topic_item, prune_node)

    if myWorkSpace.verifyDialogs():
        print("New dialog nodes verified. Now writing to file " + outputFileName)
        # Write to file
        myWorkSpace.write_to_file(outputFileName)

