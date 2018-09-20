#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 16 10:26:36 2017

wcs_workspace.py
@author: Jason Jingshi Li

 ***************************************************************************
  * IBM Source Material
  * (C) COPYRIGHT International Business Machines Corp., 2017.
  *
  * The source code for this program is not published or otherwise divested
  * of its trade secrets, irrespective of what has been deposited with the
  * U. S. Copyright Office.
  ***************************************************************************

File: wcs_workspace.py
A class representing a workspace in the Watson Conversation Service (WCS)

"""

import re, io
import json
import datetime
import random
import csv
import sys
import ingestion
import csv, xlwt, xlrd
import copy
from excel_reader import load_xl


class wcs_workspace(object):

    """
    # We define a class to represent a WCS workspace.
    # We load the existing JSON data exported from WCS into it
    # It also handle manipulation of data inside a WCS workspace
    """

    def __init__(self,  configFile):
        """
        Constructor
        Populate data given a configuration file or a workspace JSON file
        """
        self.config = ingestion.loadjson(configFile)
        if 'Old Workspace' in self.config:
            # We've loaded a config file
            print('Config loaded from ' + configFile)
            self.data = self.load_datafile(self.config['Old Workspace']['filename'])
        elif 'dialog_nodes' in self.config:
            # We've actually loaded a data file
            print('Data loaded from ' + configFile)
            self.data = self.load_datafile(configFile)
            self.config = {}
        else:
            print('ERROR: failed to load ' + configFile)
            sys.exit()

    def replace_irrevelant(self):
        if 'intents' not in self.data:
            print('ERROR: intents not found in file')
            sys.ext()
        for intentElem in self.data['intents']:
            if "irrevelant" not in intentElem['intent']:
                continue
            if 'counterexamples' not in self.data:
                self.data['counterexamples'] = []
            counterExampleList = [e['text']
                    for e in self.data['counterexamples'] if 'text' in e]

            for example in intentElem['examples']:
                if example['text'] not in counterExampleList:
                    self.data['counterexamples'].append(example)

            #self.data['counterexamples'] += intentElem['examples']
            self.data['intents'].remove(intentElem)

    def load_datafile(self, inputFileName):
        """
        # load the JSON data from file
        """
        with io.open(inputFileName, 'r', encoding='utf8') as file:
            filedata = file.read()
            return json.loads(filedata)

    def getDialogNodes(self):
        """
        Return list of dialog nodes in the workspace
        """
        if 'dialog_nodes' in self.data:
            return self.data['dialog_nodes']
        return []

    def write_to_file(self, outputFileName):
        """
        # Write the JSON data to file
        """
        ingestion.dict_2_json(self.data, outputFileName)

    def summariseDialogNode(self, node):
        """
        Provide a full summary of a given dialog node.
        """
        (intent, entities, answers) = self.getIntentEntitiesAnswer(node)
        fullSummary = []
        for answer in answers:
            summaryList = [intent, entities, answer]
            nodeFeatures = ['conditions','context','created','description','dialog_node','next_step',\
                            'metadata','output','parent','previous_sibling','updated']
            for feature in nodeFeatures:
                if feature not in node:
                    print('ERROR: ' + feature + ' not in node')
                    print(str(node))
                    sys.exit()
                summaryList += [str(node[feature])]
            fullSummary += [summaryList]
        return fullSummary

    def summariseDialogs(self):
        """
        # summarise all dialogs to a list of human readable format
        """
        allDialogs = []
        for node in self.getDialogNodes():
            nodeSummary = self.summariseDialogNode(node)
            if nodeSummary != []:
                allDialogs += nodeSummary
        return allDialogs

    def summariseIntents(self):
        """
        Summarise all intents to a list of intent and examples
        """
        intentSummary = []
        for intent in self.data['intents']:
            intentName = intent['intent']
            for example in intent['examples']:
                intentSummary.append([intentName, example['text']])
        return intentSummary

    def addDialogsFromExcel(self):
        """
        DEPRECATED
        Add dialog nodes from Excel file, assume there are emotion tags
        """
        assert 'EmoTags' in self.config
        assert 'filename' in self.config['EmoTags']
        assert 'sheet' in self.config['EmoTags']
        filename = self.config['EmoTags']['filename']
        sheetName = self.config['EmoTags']['sheet']
        xl_workbook = xlrd.open_workbook(filename)
        sheet = xl_workbook.sheet_by_name(sheetName)

        # Obtain all column headers:
        colHeaders = {};
        for col_index in range(sheet.ncols):
            colHeaders[sheet.cell(0,col_index).value] = col_index

        expectedHeaders = ['conditions','context','created','description','dialog_node','next_step',\
                                            'metadata','output','parent','previous_sibling','updated']

        for header in expectedHeaders:
            assert header in colHeaders
        assert 'answer' in colHeaders

        self.write_to_file('before.json')

        # Loop through every row to clear existing data
        doneNodes = []
        for row_index in range(1, sheet.nrows):
            node_id = sheet.cell(row_index, colHeaders['dialog_node']).value
            if node_id in doneNodes:
                continue
            for dNode in self.data['dialog_nodes']:
                if dNode['dialog_node'] == node_id:
                    if 'values' in dNode['output']['text']:
                        del dNode['output']['text']['values']
                        doneNodes += [node_id]
                    else:
                        dNode['output']['text'] = ""
                    break

        myWorkSpace.write_to_file('after.json')


        # Loop through every row to add the new data
        for row_index in range(1, sheet.nrows):
            node_id = sheet.cell(row_index, colHeaders['dialog_node']).value
            answer = sheet.cell(row_index, colHeaders['answer']).value

            # If there is emotion header, prefix emotion to the answer.
            if 'Emotion' in colHeaders:
                emotion =  sheet.cell(row_index, colHeaders['Emotion']).value
                answer = "<mct:gesture context=\"" + emotion + "\"/>" + answer

            # If node is already in dialogs, update the answer
            nodeAdded = False
            for dNode in self.data['dialog_nodes']:
                if dNode['dialog_node'] == node_id:
                    self.addAnswer2Node(dNode, answer)
                    nodeAdded = True
                    break

            # If the node is not in dialogs, we create a new one
            if not nodeAdded:
                newNode = {}
                for header in expectedHeaders:
                    cellValue = sheet.cell(row_index, colHeaders[header]).value
                    if header == 'output':
                        newNode[header] = dict()
                        newNode[header]['text'] = ""
                    else:
                        newNode[header] = cellValue
                self.replaceNodeAnswer(newNode, answer)
                self.data['dialog_nodes'] += [newNode]

        if self.verifyDialogs():
            print ("Dialog imported and verified")

    def addAnswer2Node(self, node, answer):
        """
        Add a given answer to a given node
        """
        assert 'output' in node
        assert 'text' in node['output']
        if 'values' in node['output']['text']:
            node['output']['text']['values'] += [answer]
        elif isinstance(node['output']['text'], dict):
            node['output']['text']['values'] = [answer]
        elif node['output']['text'] == "":
            node['output']['text'] = answer
        else:
            firstAnswer = node['output']['text']
            node['output']['text'] = dict()
            node['output']['text']['values'] = [firstAnswer, answer]

    def replaceNodeAnswer(self, node, answer):
        """
        Replace existing answer in node with new answer
        """
        assert 'output' in node
        assert 'text' in node['output']
        del node['output']['text']
        node['output']['text'] = dict()
        node['output']['text']['values']=[answer]

    def printDialog2CSV(self, filename):
        """
        Print dialog nodes as comma-separated values
        """
        # column header: the first three are for the benefit of the reader
        # the others are actual data from dialog
        columnHeaders = ['intent','entities','answer',\
                         'conditions','context','created','description','dialog_node','next_step',\
                         'metadata','output','parent','previous_sibling','updated']
        allDialogs = [columnHeaders] + self.summariseDialogs()
        with io.open(filename, "w", encoding='utf8') as f:
            writer = csv.writer(f)
            writer.writerows(allDialogs)
            print('Data written to ' + filename)

    def writeDialogs2Excel(self, filename):
        """
        Write dialog data as an Excel file
        """
        columnHeaders = ['intent','entities','answer',\
                'conditions','context','created','description','dialog_node','next_step',\
                'metadata','output','parent','previous_sibling','updated']
        allDialogs = [columnHeaders] + self.summariseDialogs()
        workbook = xlwt.Workbook(encoding="utf-8")
        sheet = workbook.add_sheet("Answer Content")
        for i, l in enumerate(allDialogs):
            for j, col in enumerate(l):
                sheet.write(i, j, col)
        workbook.save(filename)
        print('Data written to spreadsheet ' + filename)

    def writeIntents2Excel(self, filename):
        """
        Write intent data as Excel file
        """
        columnHeaders = ['intent', 'example']
        allIntents = [columnHeaders] + self.summariseIntents()
        workbook = xlwt.Workbook(encoding="utf-8")
        sheet = workbook.add_sheet("Question Intents")
        for i, l in enumerate(allIntents):
            for j, col in enumerate(l):
                sheet.write(i, j, col)
        workbook.save(filename)
        print('Intents written to spreadsheet ' + filename)

    def getIntentEntitiesAnswer(self, node):
        """
        # given a dialog node, return the intent, entities, and list of answers relevant to the node
        """
        conditions = self.extractConditions(node)
        intent = self.extractIntent(conditions)
        entities = self.extractEntities(conditions)
        answer = self.getAnswer(node)
        return (intent, entities, answer)

    def getAnswer(self, node):
        """
        Return the answer text for a given dialog node
        """
        answer = ""
        if node['output'] != None:
            if 'text' in node['output']:
                if 'values' in node['output']['text']:
                    answer = node['output']['text']['values']
                else:
                    answer = [node['output']['text']]
        return answer

    def setAnswer(self, node, answer):
        """
        Set the answer text for a given dialog node
        """
        assert 'output' in node
        assert 'text' in node['output']
        if 'values' in node['output']['text']:
            node['output']['text']['values'] = answer
        else:
            node['output']['text'] = answer

    def printAnswers(self):
        """
        Print all dialog node answers to STDOUT
        """
        for node in self.data['dialog_nodes']:
            (intent, entities, answerList) = self.getIntentEntitiesAnswer(node)
            for answer in answerList:
                answer = self.extractAnswerText(answer)
                print (intent + ',' + entities + ',' + answer)

    def extractAnswerText(self, answer):
        """
        # putting quotes around answers for the benefit of Excel CSV parser...
        """
        return '"' + str(answer) + '"'

    def extractConditions(self, node):
        """
        Extract conditions of a given dialog node
        """
        returnText = ''
        if node['conditions'] != None:
            returnText = str(node['conditions'])
        if node['parent'] != None:
            parent = node['parent']
            for otherNode in self.data['dialog_nodes']:
                if otherNode['dialog_node'] == parent:
                    returnText = returnText + '|' + self.extractConditions(otherNode)
        return returnText

    def extractIntent(self, conditionString):
        """
        Extract intent from the condition of a given dialog node
        """
        returnText = ''
        m = re.search('(?<=#)\w+', conditionString)
        if m!=None:
            returnText = m.group(0)
        return returnText

    def extractEntities(self, conditionString):
        """
        Extract entities from the condition of a given dialog node
        """
        items = conditionString.split('|')
        returnString = ''
        for item in items:
            m = re.search('(?<=)@.+', item)
            if m != None:
                returnString = returnString + m.group(0) + ' '
        return returnString

    # Verify dialog nodes are consistent
    def verifyDialogs(self):
        """
        Test to verify certain assumptions we have for dialog nodes
        in a WCS workspace
        """
        verified = True;
        for node in self.data['dialog_nodes']:
            parent = node['parent']
            prev = node['previous_sibling']
            name = node['dialog_node']

            parentFound = (str(parent) == 'None')
            prevFound = (str(prev) == 'None')
            for othernode in self.data['dialog_nodes']:
                if othernode['dialog_node'] == parent:
                    parentFound = True
                if othernode['dialog_node'] == prev:
                    prevFound = True
            if prevFound == False:
                print('ERROR: ' + str(name) + ' did not find prev sibling ' + str(prev))
                verified = False
            if parentFound == False:
                print('ERROR: ' + str(name) + ' did not find parent ' + str(parent))
                verified = False
        return verified


    # Given a list of dialog nodes, we remove all the children of them
    # except the one where the condition is true (for stiching purposes)

    def prune_dialog_childnodes(self, parents_to_prune):
        """
        Given a workspace and a list of names of a dialog nodes,
        we remove all the decendant nodes of those nodes
        in the workspace, except the the node with
        condition 'true'.
        """
        print("Pruning child nodes of " + str(parents_to_prune))

        check_for_more = True

        nodes_to_prune = []

        for node in self.data['dialog_nodes']:
            if 'title' in node and node['title'] in parents_to_prune:
                parents_to_prune.append(node['dialog_node'])

        # Establish all parents to prune in the dialog nodes
        while (check_for_more):
            check_for_more = False
            for node in self.data['dialog_nodes']:

                # if node has no parent value set to null
                if not 'parent' in node:
                    node['parent'] = None
                if not 'previous_sibling' in node:
                    node['previous_sibling'] = None

                # if the node's parent is in the  original parents_to_prune and the condition is true
                # we avoid removing it, as it is the default node by convention
                if node['parent'] in parents_to_prune and node['conditions'] == 'true':
                    continue
                # otherwise, if its parent is in the nodes_to_prune, we'll also remove this node
                if (node['parent'] in parents_to_prune or node['parent'] in nodes_to_prune) and \
                        node['dialog_node'] not in nodes_to_prune:
                    print('Pruning node ' + node['dialog_node'])
                    nodes_to_prune.append(node['dialog_node'])
                    check_for_more = True

        print(str(nodes_to_prune))

        newDialogNodes = []
        for node in self.data['dialog_nodes']:
            if node['dialog_node'] not in nodes_to_prune:
                newDialogNodes.append(node)
                #print('Removing node ' + node['dialog_node'])
                #self.data['dialog_nodes'].remove(node)
        self.data['dialog_nodes'] = newDialogNodes


    def add_dialog_childnodes_after_deletion(self, topic_item, topic_simple_name):
        """
        # Doing the stitching
        After the childnodes of a topic are deleted, now we add in the new data to the topic
        """

        # load new dialog nodes, and update their root name to topic_simple_name
        dialogs_to_add = ingestion.config_load_dialogs(self.config, topic_item)
        dialogs_to_add.__update_root_name__(topic_simple_name)

        # Get the first and last child of dialogs_to_add
        last_child = dialogs_to_add.__get_last_child__(topic_simple_name)
        first_child = dialogs_to_add.__get_first_child__(topic_simple_name)


        # making sure the first and last child is properly stitched in
        for node in self.data['dialog_nodes']:

            # First child
            if node['dialog_node'] == topic_simple_name:

                # If it is a folder, we don't have to handle jump_to's
                if node['type'] == 'folder':
                    continue

                # If it is a standard node, we have to handle jump_to's
                if 'go_to' in node:
                    node['next_step'] = None
                    del node['go_to']

                if 'next_step' in node:
                    if node['next_step'] == None:
                        node['next_step'] = {}
                        node['next_step']['behavior'] = 'jump_to'
                        node['next_step']['selector'] = 'condition'
                    node['next_step']['dialog_node'] = first_child

            # Last child - we add it as previous sibling to condition:true
            # the only remaining child of topic_simple_name after deletion
            if node['parent'] == topic_simple_name:
                node['previous_sibling'] = last_child

        newNodesToAdd = dialogs_to_add.json

        self.data['dialog_nodes'] = self.data['dialog_nodes'] + dialogs_to_add.json

        # We collapse the simple answers into Multiple condition response by default.
        # Otherwise, we collapse it if it specified in the config file.
        if 'collapseDialogByIntent' not in self.config or self.config['collapseDialogByIntent'] == True:
            self.collapseDialogByIntent(newNodesToAdd)

    def replace_dialogs(self, topic_item, topic_simple_name):
        """
        # Given a workspace, it prunes the child nodes of topic_simple_name
        # and loads data from topic_item specified in
        """
        parentNodeToPrune = topic_simple_name
        parentFound = False
        for node in self.data['dialog_nodes']:
            if parentNodeToPrune == node['dialog_node']:
                parentFound = True
                break

        if not parentFound:
            for node in self.data['dialog_nodes']:
                if 'title' in node:
                    if parentNodeToPrune == node['title']:
                        parentNodeToPrune = node['dialog_node']
                        parentFound = True
                        break

        if not parentFound:
            print('ERROR - Dialog Node not found in workspace: ' + topic_simple_name)
            print('ERROR - Update workspace failed! Stopping now!')
            sys.exit(0)

        print('pruning ' + topic_simple_name + ', dialog_node:' + parentNodeToPrune)

        self.prune_dialog_childnodes([parentNodeToPrune])
        self.add_dialog_childnodes_after_deletion(topic_item, parentNodeToPrune)


    def set_workspace_name(self, newWorkSpaceName):
        """
        # Set workspace name
        """
        self.data['name'] = newWorkSpaceName

    def remove_workspace_id(self):
        """
        # Remove existing workspace id
        """
        del self.data['workspace_id']

    def getLastChildName(self, rootName):
        """
        # Return the name of the dialog node that is the last child of the
        # input node
        """
        assert 'dialog_nodes' in self.data
        for node in self.data['dialog_nodes']:
            if node['parent'] != rootName:
                continue
            nodeName = node['dialog_node']
            lastChild = True
            for otherNode in self.data['dialog_nodes']:
                if otherNode['previous_sibling'] == nodeName:
                    lastChild = False
                    break
                if lastChild:
                   return nodeName
        print ('ERROR: last child not found! ' + rootName)
        return None

    def add_dialogs(self, newDialogs):
        """
        # Adding dialogs from a different workspace to this workspace
        """
        addNewDialogHead = True

        assert 'dialog_nodes' in self.data

        # get the root node name of the other workspace
        otherRootName = getRootName(newDialogs)

        # get the last child of root node from this workspace
        lastRootSibling = self.getLastChildName(None)
        # print(lastRootSibling + ' last root sibling')

        # collect all the names of the existing dialog nodes
        oldNodeNames = []
        for node in self.data['dialog_nodes']:
            oldNodeNames.append(node['dialog_node'])

        # Loop through the new dialog nodes, if there is a conflict with the name of a node
        # we find a new name for it
        newNodeNames = {}
        for node in newDialogs:

            if not addNewDialogHead:
                # If it is the root node, we don't add it
                if node['parent'] == None and node['previous_sibling'] == None:
                    continue
            # If there is a conflict of node name, we come up with a new node name
            if node['dialog_node'] in oldNodeNames:
                counter = 0
                while True:
                    newNodeName = 'node_888_' + str(counter)
                    if newNodeName not in oldNodeNames and newNodeName not in newNodeNames.values():
                        newNodeNames[node['dialog_node']] = newNodeName
                        break

        # Now we loop through the new dialog nodes, and append them to the existing nodes
        nodesAppended = 0
        for node in newDialogs:

            if not addNewDialogHead and node['previous_sibling'] == otherRootName:
                node['previous_sibling'] = lastRootSibling
            elif node['previous_sibling'] in newNodeNames:
                node['previous_sibling'] = newNodeNames[node['previous_sibling']]

            # If it is the root node
            if node['parent'] == None and node['previous_sibling'] == None:
                if addNewDialogHead:
                    node['previous_sibling'] = lastRootSibling
                else:
                    continue

            # Modify node names to avoid conflicts
            if node['dialog_node'] in newNodeNames:
                node['dialog_node'] = newNodeNames[node['dialog_node']]
            if node['parent']  in newNodeNames:
                node['parent'] = newNodeNames[node['parent']]


            if node['next_step'] != None:
                if 'dialog_node' in node['next_step']:
                    if node['next_step']['dialog_node'] in newNodeNames:
                        node['next_step']['dialog_node'] = newNodeNames[node['next_step']['dialog_node']]
            # append the node to existing nodes
            self.data['dialog_nodes'].append(node)
            nodesAppended+=1
        print (str(nodesAppended) + ' nodes added to workspace.' )

    def config_add_entities(self, entitiesList):
        """
        # Adding entities to JSON
        # By default it will replace all existing entities, unless told otherwise
        """
        newEntities = []
        for item in entitiesList:
            newEntities += ingestion.config_load_entities(self.config, item).json
        self.add_entities(newEntities)

    def add_entities(self, newEntities):
        replaceEntities = True
        if 'Keep Previous Entities' in self.config:
            replaceEntities = not self.config['Keep Previous Entities']

        # If we don't have entities in the workspace, we just add it
        if 'entities' not in self.data or replaceEntities:
            self.data['entities'] = newEntities
            return

        # If we already do have entities, we only replace the existing ones.
        for newEntity in newEntities:
            for existingEntity in self.data['entities']:
                if existingEntity['entity'] == newEntity['entity']:
                    self.data['entities'].remove(existingEntity)
                    newEntity = updateEntity(existingEntity, newEntity)
                    break
            self.data['entities'].append(newEntity)

    def config_add_intents(self, intentList):
        """
        # Add new intents to workspace
        # By default it will replace all existing intents, unless told otherwise
        """
        newIntents = []
        for item in intentList:
            newIntents += ingestion.config_load_intents(self.config, item).json
        self.add_intents(newIntents)

    def add_intents(self, newIntents):
        keepPreviousIntents = False
        if 'Keep Previous Intents' in self.config:
            keepPreviousIntents = self.config['Keep Previous Intents']

        if 'intents' not in self.data or keepPreviousIntents == False:
            self.data['intents'] = newIntents
            return

        for newIntent in newIntents:
            for existingIntent in self.data['intents']:
                if existingIntent['intent'] == newIntent['intent']:
                    self.data['intents'].remove(existingIntent)
                    newIntent = updateIntent(existingIntent, newIntent)
                    break
            self.data['intents'].append(newIntent)

    def add_workspace(self, newWorkspace):
            self.config['Keep Previous Entities'] = True
            self.config['Keep Previous Intents'] = True

            self.add_intents(newWorkspace.data['intents'])
            self.add_entities(newWorkspace.data['entities'])
            self.add_dialogs(newWorkspace.data['dialog_nodes'])

            if self.verifyDialogs():
                print('Workspace added and verified')

    def collapseAllDialogByIntent(self):
        """
        # organize dialog nodes by intent
        #
        """
        nodesToCollapse = [];
        for node in self.data['dialog_nodes']:
            if node['previous_sibling'] == None:
                allSiblings = self.getAllSiblings(node, [node])
                self.collapseSiblingsByIntent(allSiblings)
        return;

    def collapseDialogByIntent(self, nodesToExamine):

        for node in nodesToExamine:
            if node['previous_sibling'] == None:
                allSiblings = self.getAllSiblings(node, [node])
                self.collapseSiblingsByIntent(allSiblings)
        return;

    def collapseSiblingsByIntent(self, siblingNodes):
        """
        # Given an ordered list of sibling nodes from eldest to youngest
        # collect the consecutive siblings of the same intent
        # 'collapse' them by creating a new node with that intent
        # and make those nodes children of that new node
        # this way all those nodes are 'collapsed' inside one node in the UI
        """
        prevIntent = None
        nodesToCollapse = []

        # loop though the sibling of nodes
        for node in siblingNodes:
            addLongAnswer = ''

            if node['conditions'] == None or node['conditions'] == "":
                continue
            nodeConditions = node['conditions'].split(' && ')
            # look for the new intent in the list of conditions
            newIntent = ""
            # print('looking: ' + node['dialog_node'] + str(nodeConditions))
            for condition in nodeConditions:
                if condition[0] == '#':
                    newIntent = condition
                    break

            # if the new intent is different to the previous one
            # collapse the previous set of nodes if applicable, and
            # add them
            if newIntent != prevIntent:
                if len(nodesToCollapse) > 1:
                    self.collapseNodes(nodesToCollapse);
                prevIntent = newIntent
                # print('Adding to nodesToCollapse: ' + node['conditions'])
                nodesToCollapse = []
            elif newIntent == "" or newIntent == None:
                continue

            # if this node has a child, check if it can still be a response node
            # if it has only yes/no childs, then it can be a response node
            # otherwise we need to start over.
            if self.hasChild(node):

                # collect child nodes of this node and check if we have to start over
                startOver = True
                if 'yesCondition' in self.config and 'noCondition' in self.config:
                    childNodes = [childNode for childNode in self.data['dialog_nodes'] if childNode['parent'] == node['dialog_node']]
                    for childNode in childNodes:
                        if childNode['conditions'] != self.config['yesCondition'] and childNode['conditions'] != self.config['noCondition']:
                            startOver = True
                            break
                        # If child is a yes node, then may be we can use it as a response node
                        if childNode['conditions'] == self.config['yesCondition']:
                            startOver = False
                if startOver:
                    if len(nodesToCollapse) > 1:
                        self.collapseNodes(nodesToCollapse);
                    prevIntent = None
                    nodesToCollapse = []
                    continue
                else:
                    if newIntent == "" or newIntent == None:
                        continue

            nodesToCollapse.append(node)
        # got to the end
        if len(nodesToCollapse) > 1:
            self.collapseNodes(nodesToCollapse)

    def collapseNodes(self, nodesToCollapse):
        #print('collapsing nodes ')
        #print(str(nodesToCollapse))

        commonIntent = ""
        commonParent = nodesToCollapse[0]['parent']

        # Create the new node that acts as their new parent
        newParent = dict(nodesToCollapse[0])
        newParent['dialog_node'] = self.createNewNodeName()

        # Stitch in newParent
        newParent['previous_sibling'] = nodesToCollapse[0]['previous_sibling']
        nodesToCollapse[0]['previous_sibling'] = None

        for node in self.data['dialog_nodes']:
            if node['previous_sibling'] == nodesToCollapse[-1]['dialog_node']:
                # print('replacing previous sibling for ' + node['dialog_node'])
                node['previous_sibling'] = newParent['dialog_node']
            if 'next_step' in node:
                if node['next_step'] == None:
                    continue
                if 'dialog_node' in node['next_step']:
                    if node['next_step']['dialog_node'] == nodesToCollapse[0]['dialog_node']:
                        # print('replacing next tep for ' + node['dialog_node'])
                        node['next_step']['dialog_node'] = newParent['dialog_node']

        newParent['output'] = dict()


        entitiesToAdd = set()

        # Add the new node as parent to these nodes
        # Remove the intent in the condition
        for node in nodesToCollapse:
            #print(node['dialog_node'] + ' ' + node['conditions'])
            nodeConditions = node['conditions'].split(' && ')

            # Update the condition
            if (commonIntent == ""):
                for condition in nodeConditions:
                    if condition[0] == '#':
                        commonIntent = condition
                        break
            nodeConditions.remove(commonIntent)


            nodeConditionEntityPairs = getEntityPairs(nodeConditions)

            nodeEntityConditions = []
            for (entity, value) in nodeConditionEntityPairs:
                # print('nodeEntityConditions: ' + str(entity) + ' ' + str(value))
                node['context'] = dict()
                node['context'][entity] = '@' + entity
                if value != None:
                    nodeEntityConditions.append("$" + entity + " == \"" + value + "\"")
                else:
                    nodeEntityConditions.append('$' + entity)

            entityContexts = " && ".join(nodeEntityConditions)
            if len(nodeEntityConditions) > 1:
                entityContexts = "( " + entityContexts + " )"
            entityConditions =  " && ".join(nodeConditions)
            if len(nodeConditions) > 1:
                entityConditions = "( " + entityConditions + " )"

            newNodeCondition = entityConditions
            if entityConditions != '' and entityContexts != '':
                newNodeCondition = entityConditions + " || " + entityContexts

            node['conditions'] = newNodeCondition
            node['type'] = 'response_condition'
            # Update the parent
            node['parent'] = newParent['dialog_node']

            entityTypes = re.findall('@\w+', newNodeCondition)
            entitiesToAdd.update(entityTypes)

            # If the node has yes/no childnodes for long answer,
            # remove the childnodes and add the long answer as additional output
            if self.hasChild(node):
                addLongAnswer = ""
                if 'yesCondition' not in self.config:
                    continue;
                childNodes = [childNode for childNode in self.data['dialog_nodes'] if childNode['parent'] == node['dialog_node']]
                for childNode in childNodes:
                    # If child is a yes node, get the long answer from it
                    if childNode['conditions'] == self.config['yesCondition']:
                        if 'text' in childNode['output']:
                            if isinstance(childNode['output']['text'], str):
                                addLongAnswer = childNode['output']['text']
                            elif isinstance(childNode['output']['text'], dict) and 'values' in childNode['output']['text']:
                                addLongAnswer = childNode['output']['text']['values'][0];
                            else:
                                addLongAnswer = str(childNode['output'])
                        else:
                            addLongAnswer = str(childNode['output'])

                        if isinstance(node['output']['text'], str):
                            originalAnswer = node['output']['text']
                            node['output']['text'] = dict()
                            node['output']['text']['values'] = [originalAnswer, addLongAnswer]
                            node['output']['text']['selection_policy'] = 'sequential'
                            node['output']['text']['append'] = None
                        elif isinstance(node['output']['text'], dict) and 'values' in node['output']['text'] and addLongAnswer not in node['output']['text']['values']:
                            node['output']['text']['values'].append(addLongAnswer)
                    self.data['dialog_nodes'].remove(childNode)


        # Identify Common Intent

        entitiesToClear = getEntityNames(entitiesToAdd)
        newChildContext = dict();
        for entity in entitiesToClear:
            newChildContext[entity] = None

        newParent['conditions'] = commonIntent

        self.data['dialog_nodes'].append(newParent)

        # Every MCR node is followed by the following child nodes:
        # 1. a child node that sets the default intent for the following dialog
        # 2. OPTIONAL: a child node that follows yesCondition, for long answers
        # 3. OPTIONAL: a child node that follows noCondition, for long answers
        # 4. a child node that unsets the context variables and starts over the conversation

        # Create a new child that set the default intent for the following dialog
        # It clears the context variable for the saved entities
        newChild = copy.deepcopy(newParent)
        newChild['context'] = newChildContext
        newChild['dialog_node'] = self.createNewNodeName()
        newChild['parent'] = newParent['dialog_node']
        newChild['previous_sibling'] = None
        newChild['output'] = {}
        newChild['next_step'] = {"dialog_node": newParent['dialog_node'],"behavior": "jump_to","selector": "body"}

        newChildEntityCondition =  ' || '.join(entitiesToAdd)
        if len(entitiesToAdd) > 1:
            newChildEntityCondition = '(' + newChildEntityCondition + ')'
        sameIntentCondition = 'irrelevant'
        if 'sameIntentCondition' in self.config:
            sameIntentCondition = self.config['sameIntentCondition']
        newChild['conditions'] = sameIntentCondition + ' && ' + newChildEntityCondition
        self.data['dialog_nodes'].append(newChild)

        lastAddedDialogNode = newChild['dialog_node']

        # If there is a long question prompt, add it as a child node
        if self.config:
            if 'yesCondition' in self.config:
                longQuestionPromptChild = copy.deepcopy(newChild)
                longQuestionPromptChild['conditions'] = self.config['yesCondition']
                del longQuestionPromptChild['context']
                longQuestionPromptChild['dialog_node'] = self.createNewNodeName()
                longQuestionPromptChild['previous_sibling'] = lastAddedDialogNode
                lastAddedDialogNode = longQuestionPromptChild['dialog_node']
                self.data['dialog_nodes'].append(longQuestionPromptChild)
                if 'noCondition' in self.config:
                    noChild = copy.deepcopy(newChild)
                    noChild['dialog_node'] = self.createNewNodeName()
                    noChild['conditions'] = self.config['noCondition']
                    noChild['previous_sibling'] = lastAddedDialogNode
                    del noChild['next_step']
                    noChild['output']['text'] = {}
                    noChild['output']['text']['values'] = ['What else would you like to know?']
                    if 'responseToNo' in self.config:
                        noChild['output']['text']['values'] = [self.config['responseToNo']]
                    noChild['output']['text']['selection_policy'] = 'sequential'
                    lastAddedDialogNode = noChild['dialog_node']
                    self.data['dialog_nodes'].append(noChild)

        #  a child node that unsets the context variables and starts over the conversation
        lastChild = copy.deepcopy(newChild)
        lastChild['dialog_node'] = self.createNewNodeName()
        lastChild['conditions'] = 'true'
        lastChild['previous_sibling'] = lastAddedDialogNode
        lastAddedDialogNode = lastChild['dialog_node']
        lastChild['next_step']['dialog_node'] = getRootName(self.data['dialog_nodes'])
        lastChild['next_step']['selector'] = 'condition'
        self.data['dialog_nodes'].append(lastChild)

        nodesToCollapse[0]['previous_sibling'] = lastAddedDialogNode

        return

    def createNewNodeName(self):
        # Randomly pick the middle number between 1 and 10000
        mid_fix = random.randrange(10000)
        suffix = 0
        while self.nodeNameUsed('node_' + str(mid_fix) + '_' + str(suffix)):
            suffix+=1
        #print('created new node name ' + 'node_' + str(mid_fix) + '_' + str(suffix))
        return 'node_' + str(mid_fix) + '_' + str(suffix)

    def getAllSiblings(self, prevSibling, siblingsSoFar):
        nextSibling = None;
        for node in self.data['dialog_nodes']:
            if node['previous_sibling'] == prevSibling['dialog_node']:
                nextSibling = node;
                break;
        if nextSibling == None:
            return siblingsSoFar;
        else:
            siblingsSoFar.append(nextSibling);
            return self.getAllSiblings(nextSibling, siblingsSoFar);

    def nodeNameUsed(self, newNodeName):
        for node in self.data['dialog_nodes']:
            if newNodeName == node['dialog_node']:
                return True
        return False

    def hasChild(self, mynode):
        for node in self.data['dialog_nodes']:
            if mynode['dialog_node'] == node['parent']:
                return True
        return False

    # Adding node title when it is missing
    def addNodeTitle(self):
        for node in self.data['dialog_nodes']:
            if not node['dialog_node'].startswith('node_'):
                if 'title' not in node:
                    node['title'] = node['dialog_node']

def getRootName(dialogList):
    """
    Return the name of the root node of a given dialog list
    """
    for node in dialogList:
        if node['previous_sibling'] == None and node['parent'] == None:
            return node['dialog_node']
    print('ERROR: root node not found!')
    return None

def updateIntent(oldIntent, newIntent):
    """
    # Update examples in the oldIntent with added examples of the newIntent,
    # if they are the same intent
    """
    if oldIntent['intent'] != newIntent['intent']:
        print('ERROR: Intent do not match!\nOld:' + str(oldIntent) + '\nNew:' + str(newIntent))
        return oldIntent
    for example in newIntent['examples']:
        exampleFound = False
        for oldExample in oldIntent['examples']:
            if example['text'].lower() == oldExample['text'].lower():
                exampleFound = True
                break
        if not exampleFound:
            oldIntent['examples'].append(example)
    return oldIntent

def updateEntity(oldEntity, newEntity):
    if oldEntity['entity'] != newEntity['entity']:
        print('ERROR: Entities do not match!\nOld:' + str(oldEntity) + '\nNew:' + str(newEntity))
        return oldEntity
    for newValue in newEntity['values']:
        sameValueFound = False
        for oldValue in oldEntity['values']:
            if oldValue['value'] == newValue['value']:
                oldEntity['values'].remove(oldValue)

                # update entity value, append synonyms
                if newValue['synonyms'] != None:
                    for newSynonym in newValue['synonyms']:
                        if oldValue['synonyms'] == None:
                            oldValue['synonyms'] = []
                        if newSynonym not in oldValue['synonyms']:
                            oldValue['synonyms'].append(newSynonym)

                oldEntity['values'].append(oldValue)
                sameValueFound = True
                break
        if not sameValueFound:
            oldEntity['values'].append(newValue)
    return oldEntity

def printNodeNames(nodes):
    toPrint = "siblings: ";
    for node in nodes:
        toPrint += node['dialog_node'] + ' '
    print(toPrint);

"""
getEntityNames
- given a list of entities from conditions, i.e. ['@fruit:apple', '@vegetable', '@fruit:banana']
- return a list of entity names, i.e. ['fruit', 'vegetable']
"""
def getEntityNames(EntityList):
    entityNames = []
    for entity in EntityList:
        regexmatch = re.search('@(.*):', entity);
        if regexmatch == None:
            regexmatch = re.search('@(.*)', entity);
        if regexmatch == None:
            continue;
        entityName = regexmatch.group(1)
        if entityName not in entityNames:
            entityNames.append(entityName)
    return entityNames;

def getEntityPairs(EntityList):
    entityPairs = []
    for entity in EntityList:
        regexmatch = re.search('@(.*):(.*)', entity)
        if regexmatch != None:
            entityPairs.append((regexmatch.group(1), regexmatch.group(2).strip('()')))
        else:
            regexmatch = re.search('@(.*)', entity)
            if regexmatch != None:
                entityPairs.append((regexmatch.group(1), None))
    return entityPairs


# Main Method
if __name__ == "__main__":
    """
    Main method. Not doing anything useful so far.
    """
    print('loading new_workspace')
    myWorkSpace = wcs_workspace('../data/new_workspace.json')

    # Check if the workspace dialog is valid
    if myWorkSpace.verifyDialogs():
        myWorkSpace.write_to_file('../output/new_workspace_formatted.json')

