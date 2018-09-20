#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 14 11:00:35 2016
@author: Jason Jingshi Li, George Yiapanis
File: ingestion.py
Ingesting content from MS Excel to JSON format for the Watson Conversation Service

 ***************************************************************************
  * IBM Source Material
  * (C) COPYRIGHT International Business Machines Corp., 2016.
  *
  * The source code for this program is not published or otherwise divested
  * of its trade secrets, irrespective of what has been deposited with the
  * U. S. Copyright Office.
  ***************************************************************************

"""

from excel_reader import load_xl
import re, io, sys
import json
import datetime
import csv

def loadjson(filename):
    """Loads a json file into a python dictionary
    Positional arguments
    --------------------
    filename : str
        the filename of the the file to be read
    Returns
    --------------------
    a python dictionary
    note: This function can only read a json file with a single dictionary
    """
    with io.open(filename, 'r', encoding='utf8') as file:
        return json.load(file)

def writejson(dict_, filename):
    """Dump dictionary as a json file.
    Positional arguments
    --------------------
    dict_ : dictionary
        a python dictionary
    filename : str
        the filename of the output
    Returns
    --------------------
    no return
    """
    with io.open(filename, 'w', encoding='utf8') as outfile:
        json.dump(dict_, outfile)
        return

def list_2_dict(value, keys):
    """
    maps each item in list_ to a specific classes_
    """
    dict_ = {}
    for i, key in enumerate(keys):
        if key in dict_:
            if value[i] in dict_[key]:
                pass
            else:
                dict_[key].append(value[i])
        else:
            dict_[key] = [value[i],]
    return dict_

def __combine_lists__(intents):
    """
    returns dictionay in the form {key : value}
    """
    dict_={}
    for intent in intents:
        dict_[intent] = string2condition(intent)
    return dict_


def string2condition(string):
    """
    Format a string so it can be used as a condition
    replace spaces and punctuations with underscores
    """
    # First, we chop off trailing whitespace
    string = string.rstrip()

    string  = re.sub(r"\u2019", '_', string)
    string  = re.sub(r'\'', '_', string)
    string  = re.sub(r'\?', '', string)
    string =  re.sub(r',', '', string)
    string  = re.sub(r' ', '_', string)
    return string


def dict_2_json(dictionary, filenametosavejson):
    """
    Dumps dictionary to JSON
    """
    with io.open(filenametosavejson, 'w', encoding='utf8') as f:
        json.dump(dictionary, f, indent=4, sort_keys=True)
    return

def get_reduced_indices(list_, regex = '.*Draft'):
    """
    Reduce indices for a given regex
    Used for parsing excel files
    """
    reduced_indices = []
    for i, item in enumerate(list_):
        if re.search(regex, item, re.IGNORECASE):
            reduced_indices.append(i)
    return reduced_indices

def reduce_data(sheet, indices):
    """
    Reduce data for a given list of indices
    Used for parsing excel files
    """
    for key in sheet.data:
        sheet.data[key] = [sheet.data[key][i] for i in indices]
    return sheet

class load_intents(object):
    """
    A class for loading intents for use in watson conversational service
    """
    def __init__(self, sheet, intents_config):
        """
        Load intents for a given excel sheet and config parameters
        """
        self.config = intents_config

        assert 'question header' in intents_config and 'intent header' in intents_config
        self.examples = sheet.data[intents_config['question header']]
        self.intents = sheet.data[intents_config['intent header']]

        self.intent_names = load_intents.__get_intent_names__(self)
        self.csv = load_intents.__get_csv__(self)
        self.date_created = str(datetime.datetime.now()).split('.')[0]
        self.date_updated = str(datetime.datetime.now()).split('.')[0]
        self.json = load_intents.__get_json__(self)

    def __get_intent_names__(self):
        """
        Get intent names from ingested data, adding prefix to them
        """
        # First we get a draft of names by simply formatting the intent name
        intent_names = __combine_lists__(self.intents)

        # We then add the intent prefix to the intent names
        if 'intent prefix' in self.config:
            intent_names = {k: self.config['intent prefix'] + v for k, v in intent_names.items()}
        return intent_names

    def __get_csv__(self):
        """
        Store ingested data ready for writing to a csv file
        """
        return [[self.examples[index], self.intent_names[intent]]  for index, intent in enumerate(self.intents)]

    def __get_json__(self):
        """
        Creates a conversation tree in the form a  python dictionary
        Arguments
        ----------
        None
        Return
        ------
        a list of dictionary, each dictionary represents a node in the conversation tree
        [dict1, dict2 ....]
        An example format show below
        {
            "created": "2016-12-23 12:12:15",
            "description": "description",
            "examples": [
                {
                    "created": "2016-12-23 12:12:15",
                    "text": "Goodbye",
                    "updated": "2016-12-23 12:12:15.373088"
                },
                {
                    "created": "2016-12-23 12:12:15",
                    "text": "hasta la vista",
                    "updated": "2016-12-23 12:12:15.373088"
                },
                {
                    "created": "2016-12-23 12:12:15",
                    "text": "so long",
                    "updated": "2016-12-23 12:12:15.373088"
                },
                {
                    "created": "2016-12-23 12:12:15",
                    "text": "farewell for now",
                    "updated": "2016-12-23 12:12:15.373088"
                },
                {
                    "created": "2016-12-23 12:12:15",
                    "text": "cheerio then",
                    "updated": "2016-12-23 12:12:15.373088"
                }
            ],
            "intent": "C.Goodbye"
        }
        """
        dict_intent = {}
        self.date_updated = str(datetime.datetime.now())
        for index, intent in enumerate(self.intents):
            if (intent == ""):
                continue;
            fmtd_intent = self.intent_names[intent]

            exampleString = formatExampleString(self.examples[index])
            nesteddict = {'text': exampleString, 'created' : self.date_created, 'updated' : self.date_updated}
            nesteddict2 = {'text': self.examples[index].capitalize(), 'created' : self.date_created, 'updated' : self.date_updated}
            if fmtd_intent in dict_intent:
                if nesteddict in dict_intent[fmtd_intent]['examples'] or nesteddict2 in dict_intent[fmtd_intent]['examples']:
                    pass
                else:
                    dict_intent[fmtd_intent]['examples'].append(nesteddict)
            else:
                dict_intent[fmtd_intent] = {}
                dict_intent[fmtd_intent]['intent'] = fmtd_intent
                dict_intent[fmtd_intent]['examples'] = [nesteddict,]
                dict_intent[fmtd_intent]['created'] = self.date_created
                dict_intent[fmtd_intent]['description'] = fmtd_intent
        return [dict_intent[key] for key in dict_intent]

    def write_to_csv(self, filename):
        """
        write intents to a csv file
        Positional Arguments
        ---------------------
        filename : (str)
            the name of the csv :q!file
        """
        with io.open(filename, 'w', encoding='utf8') as f:
            intentwriter = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
            for row in self.csv:
                intentwriter.writerow(row)
        return

def formatExampleString(example):
    """
    Format example string for the classifier
    substitute newline characters as spaces
    chop off trailing newline and whitespaces
    """
    return re.sub(r"\n", " ", example).rstrip()

class entities(object):
    """
    A class for loading entities for use in WCS
    """
    def __init__(self, e_name, e_value, e_synonym, fuzzy_match):
        """
        Store ingested entity data
        """
        self.e_name = e_name
        self.e_value = e_value
        self.e_synonym = e_synonym
        self.fuzzy_match = fuzzy_match

        # Replace spaces with underscores
        self.e_all_names = __combine_lists__(e_name)

        self.date_created = str(datetime.datetime.now()).split('.')[0]
        self.json = entities.__get__json__(self)

    def __check_ingestion__(self):
        """
        Checking ingestion is done correctly
        """
        assert len(self.e_name) == len(self.e_value)
        assert len(self.e_name) == len(self.e_synonym)

    def __get__json__(self):
        """
        Create a list of entity dictionaries based on ingested entity data
        This dictionary can be later written directly to JSON file.
        """
        self.__check_ingestion__()
        entitiesList = []

        for index, name in enumerate(self.e_name):


            # get all the entries of the row from Excel
            fmt_name = self.e_all_names[name]
            if fmt_name == "":
                continue

            value = self.e_value[index]
            synonym = self.e_synonym[index]

            isNewEntity = True

            # We loop through the existing list of entities to see if this is a new
            # entity that we have not seen before
            for e_item in entitiesList:
                assert 'entity' in e_item
                if e_item['entity'] == fmt_name:
                    # This is an entity that we have already seen before
                    isNewEntity = False
                    # We'll loop through the values to see if this is just a synonym entry, or a new value
                    assert 'values' in e_item
                    isNewValue = True
                    for v_item in e_item['values']:
                        assert 'value' in v_item
                        if v_item['value'] == value:
                            # Adding synonym
                            isNewValue = False
                            assert 'synonyms' in v_item

                            if (len(synonym) == 0 or len(synonym) > 64):
                                print('WARNING: synonym ' + synonym + ' of entity ' + fmt_name + ':(' + value + ') is too short or too long, and will be ignored!');
                                continue;
                            if v_item['synonyms'] == None:
                                v_item['synonyms'] = [synonym]
                            elif synonym not in v_item['synonyms']:
                                v_item['synonyms'].append(synonym)
                    # loop values complete, confirm it is a new value
                    if isNewValue:
                        e_item['values'].append(self.new_value_entry(value, synonym))
            # loop entities complete, confirm it is a new entity
            if isNewEntity:
                #if (synonym != None):
                    #if (len(synonym) == 0 or len(synonym) > 64):
                        #print('WARNING: synonym ' + synonym + ' of entity ' + fmt_name + ':(' + value + ') is too short or too long, and will be ignored!');
                        #synonym = None;
                entitiesList.append(self.new_entity_entry(fmt_name, value, synonym))

        return entitiesList

    def new_entity_entry(self, fmt_name, value, synonym):
        """
        New entity data entry
        """
        newEntity= {}
        newEntity['created'] = self.date_created
        newEntity['description'] = None
        newEntity['entity'] = fmt_name
        newEntity['open_list'] = False
        newEntity['source'] = None
        newEntity['type'] = None
        newEntity['updated'] = self.date_created
        newEntity['values'] = [self.new_value_entry(value, synonym)]
        newEntity['fuzzy_match'] = self.fuzzy_match
        return newEntity

    def new_value_entry(self, value, synonym):
        """
        New entity value entry
        One entity may have many values
        """
        new_entry = {}
        new_entry['created'] = self.date_created
        new_entry['metadata'] = None
        if synonym == "":
            new_entry['synonyms'] = None
        elif len(synonym) > 64:
            print('WARNING - synonym ' + synonym + ' of entity value (' + value + ') is too long, and will be ignored!');
            new_entry['synonyms'] = None
        else:
            new_entry['synonyms'] = [synonym]
        new_entry['updated'] = self.date_created
        new_entry['value'] = formatEntityValue(value)
        return new_entry

def formatEntityValue(valueString):
    returnString = valueString.replace("'", "")
    return returnString

class dialog(object):
    """
    Loads a conversation tree for use in watson's conversational service
    Positional arguments
    --------------------
    conditions: list
        list of conditions or intents
    values: list
        list of answers
    len(conditions) = len(values)
    Attributes
    -----------
    conv_start
    """

    def __init__(self, conditions, values, parameters=None):
        """
        Store the ingested dialog(answer) data
        """
        self.conv_start = dialog.__conversation_start__(self)

        self.conditional_node = None
        self.conditions = conditions
        if parameters == None:
            self.parameters = {}
        else:
            self.parameters = parameters

        formatHTML = True
        if 'formatHTML' in parameters:
            formatHTML = parameters['formatHTML']

        self.values = [formatAnswer(value, formatHTML) for value in values]

        if len(conditions) == 0:
            print('ERROR - No condition for dialog nodes found!')
            print('ERROR - Answers not ingested! Stopping now!')
            sys.exit()

        if isinstance(conditions[0], tuple) and len(conditions[0]) == 3:
            self.intents = [str(i[0]) for i in conditions]
            self.entityTypes = [str(i[1]) for i in conditions]
            self.entityValues = [str(i[2]) for i in conditions]
            self.intent_names = __combine_lists__(self.intents)
        else:
            self.intents = conditions
            self.entityTypes = []
            self.entityValues = []
            self.intent_names = __combine_lists__(self.intents)
        self.date_created = str(datetime.datetime.now()).split('.')[0]
        self.date_updated = str(datetime.datetime.now()).split('.')[0]
        self.nodes={}
        self.reducedIndexMapping = {}
        self.json = dialog.__get__json__(self)


    def __get__json__(self):
        """
        Creates a conversation tree in the form a  python dictionary
        Arguments
        ----------
        None
        Return
        ------
        a list of dictionary, each diction represents a node in the conversation tree
        [dict1, dict2 ....]
        An example format show below
        {
            "conditions": "#O.What_are_goals",
            "context": null,
            "description": null,
            "dialog_node": "node_315_7",
            "go-to": null,
            "metadata": null,
            "output": {
                "text": {
                    "append": null,
                    "selection_policy": "random",
                    "values": [
                        "A goal is something that you want to do or achieve. Goals can be short term, like something that you want to do in the next three months. Or they can be long term, so something that will take a long time to achieve, maybe 5 to 10 years.\n\nAt your planning meeting your planner will help you make a list of your goals and work out what supports you need to make your goals happen."
                    ]
                }
            },
            "parent": "node_315_0",
            "previous_sibling": "node_315_6"
        }
        """
        id_ = 0
        dict_dialogue ={}
        sorted_dict ={}
        indices = {}
        dict_values = list_2_dict(self.values, self.conditions)

        for index, condition in enumerate(self.conditions):

            # Extract intent as formatted condition
            fmt_condition = self.intent_names[self.intents[index]]

            # if entity is specified, append to formatted condition
            if len(self.entityTypes) == len(self.intents):
                fmt_condition = fmt_condition + getMultipleEntityString(self.entityTypes[index], self.entityValues[index])

            nesteddict = {'text' : {'append': None, 'selection_policy': 'sequential', 'values': dict_values[condition] }}

            # print(fmt_condition + ": " + str(nesteddict))

            if fmt_condition in dict_dialogue:
                pass
            else:
                dict_dialogue[fmt_condition] = {}
                dict_dialogue[fmt_condition]["conditions"] = '#'+ fmt_condition
                dict_dialogue[fmt_condition]["context"] = None
                dict_dialogue[fmt_condition]["description"] = None
                dict_dialogue[fmt_condition]["dialog_node"] = 'node_'+str(id_+1)
                self.nodes[fmt_condition] = 'node_'+str(id_+1)
                dict_dialogue[fmt_condition]["go-to"] = None
                dict_dialogue[fmt_condition]["metadata"] = None
                dict_dialogue[fmt_condition]["output"] = nesteddict
                dict_dialogue[fmt_condition]["previous_sibling"] = 'node_'+str(id_)
                dict_dialogue[fmt_condition]["parent"] = None
                sorted_dict[id_]=fmt_condition
                indices[fmt_condition] = id_
                self.reducedIndexMapping[index] = id_
                id_ += 1
        self.dict_= dict_dialogue
        self.sorted_dict = sorted_dict
        self.indices = indices

        returnList = [dict_dialogue[sorted_dict[key]] for key in sorted_dict]

        return returnList


    def __get_last_child__(self, rootName):
        """
        Get last child of this group of dialogs
        """
        for node in self.json:
            if node['parent'] != rootName:
                continue
            nodeName = node['dialog_node']
            lastChild = True
            for otherNode in self.json:
                if otherNode['previous_sibling'] == nodeName:
                    lastChild = False
                    break
            if lastChild:
                return nodeName
        print ('ERROR: last child not found! ' + rootName)
        return None

    def __get_first_child__(self, rootName):
        """
        Get first child of this group of dialogs
        """
        for node in self.json:
            if node['parent'] != rootName:
                continue
            if node['previous_sibling'] == None:
                return node['dialog_node']
        print ('ERROR: first child not found! ' + rootName)
        return None

    def __update_root_name__(self, newRootName):
        """
        Update the root name of this group of dialogs
        """
        newJSON = []
        for node in self.json:
            isEndingZero = re.compile(".*_0$")
            if isEndingZero.match(str(node['parent'])):
                node['parent'] = newRootName
            newJSON.append(node)
        self.json = newJSON

    def __handle_check__(self, intent, intentPrefix, nodeCode, index):
        """
        Update the node with the appropriate intent prefix and node code.
        """
        fmt_cndt = intentPrefix+intent
        self.intent_names[intent] = fmt_cndt
        self.dict_[intent]['conditions'] = '#'+fmt_cndt
        self.dict_[intent]['parent'] = 'node_'+nodeCode+'_0'
        self.dict_[intent]['dialog_node'] = 'node_'+nodeCode + '_' + str(index+1)
        self.dict_[intent]['previous_sibling'] = 'node_'+nodeCode + '_' + str(index)
        self.nodes[intent] = 'node_'+nodeCode + '_' + str(index+1)
        self.json = [self.dict_[self.sorted_dict[key]] for key in self.sorted_dict]
        return self

    def long_answers(self, long_answers, long_answer_indices, nodeCode):
        """
        Extends conversation tree to account for long answers.
        Positional Arguments
        ---------------------
        self: dialog instance
        long_answers: list of long answer text (alternative to the standard answers)
        long_answer_indices: list of indices for long answer text
        nodeCode: the string denote the number in the middle of the node name
        Return
        -------
        self: an updated version of the dialog instance
        """
        i=len(self.json)

        breakTag = ""
        longAnswerQuestion = ""
        yesNoTag = ""
        yesCondition = "#C.Yes"
        noCondition = "#C.No"
        if "breakTag" in self.parameters:
            breakTag = self.parameters["breakTag"]
        if "long answer question" in self.parameters:
            longAnswerQuestion = self.parameters["long answer question"]
        if "yesNoTag" in self.parameters:
            yesNoTag = self.parameters["yesNoTag"]
        if "yesCondition" in self.parameters:
            yesCondition = self.parameters["yesCondition"]
        if "noCondition" in self.parameters:
            noCondition = self.parameters["noCondition"]


        for counter, index in enumerate(long_answer_indices):
            assert index in self.reducedIndexMapping
            jsonIndex = self.reducedIndexMapping[index]

            for responseID, response in enumerate(self.json[jsonIndex]['output']['text']['values']):
                self.json[jsonIndex]['output']['text']['values'][responseID] = response + longAnswerQuestion + yesNoTag

            parent_id_follow_ons = self.json[jsonIndex]['dialog_node']
            i += 1
            yes_node = dialog.__get_simple_conditional_node__(self, condition_name = yesCondition, node_name = 'node_' + nodeCode + '_'+str(i), \
                                                           previous_sibling = None, parent=parent_id_follow_ons, \
                                                           value = long_answers[counter])
            self.json.append(yes_node)
            i +=1
            no_node = dialog.__get_simple_conditional_node__(self, condition_name=noCondition, node_name='node_' + nodeCode + '_' + str(i), \
                                                         previous_sibling = 'node_' + nodeCode + '_' + str(i-1), parent=parent_id_follow_ons, value = "Sure. Let’s talk about something else.")
            self.json.append(no_node)

            # Add long answer also as a second sequential response, if there is only one response
            # This is implemented as requested in issue #2 of the repo
            if len(self.json[jsonIndex]['output']['text']['values']) == 1:
                print("adding long answers to: " + str(self.json[jsonIndex]['output']['text']['values']))
                self.json[jsonIndex]['output']['text']['values'].append(long_answers[counter])

        return self

    def follow_on_questions(self, follow_on_intents, follow_on_wordings, follow_on_indices, nodeCode):
        """
        Estends conversation tree to account for follow on questions
        Positional Arguments
        --------------------
        self: dialog instance
        follow_on_intents: list of intent that the follow on question jump to
        follow_on_wording: list of wording of the follow on question
        nodeCode: the string denote the number in the middle of the node name
        Return
        -------
        self: an updated version of the dialog instance
        """
        i=len(self.json)

        breakTag = ""
        yesNoTag = ""
        yesCondition = "#C.Yes"
        noCondition = "#C.No"
        if "breakTag" in self.parameters:
            breakTag = self.parameters["breakTag"]
        if "yesNoTag" in self.parameters:
            yesNoTag = self.parameters["yesNoTag"]
        if "yesCondition" in self.parameters:
            yesCondition = self.parameters["yesCondition"]
        if "noCondition" in self.parameters:
            noCondition = self.parameters["noCondition"]


        for counter, index in enumerate(sorted(follow_on_indices)):
            assert index in self.reducedIndexMapping
            jsonIndex = self.reducedIndexMapping[index]

            self.json[jsonIndex]['output']['text']['values'] = [self.json[jsonIndex]['output']['text']['values'][0]+ breakTag + follow_on_wordings[counter] + yesNoTag]
            parent_id_follow_ons = self.json[jsonIndex]['dialog_node']
            i += 1
            yes_node = dialog.__get_simple_conditional_node__(self, condition_name = yesCondition, node_name = 'node_' + nodeCode + '_'+str(i), \
                                                        previous_sibling = None, parent=parent_id_follow_ons, \
                                                        value = 'Okay. Let me look that up.')

            yes_node["context"] = {"user_meant": follow_on_intents[counter]}
            yes_node["output"].update({"action": "follow-on"})

            self.json.append(yes_node)
            i += 1
            no_node = dialog.__get_simple_conditional_node__(self, condition_name=noCondition, node_name='node_' + nodeCode + '_' + str(i), \
                                                        previous_sibling = 'node_' + nodeCode + '_' + str(i-1), parent=parent_id_follow_ons, value = "Okay. Let’s talk about something else.")
            self.json.append(no_node)

        return self



    def __get_simple_conditional_node__(self, condition_name = "#C.Yes", node_name = 'node_C.0', previous_sibling = None, parent = None, value=None):
        """
        return a customizable conversational node
        Keyword Arguments
        ----------------
        condition_name: (str)
            the name of the condition
        node_name: (str)
            the dialog id e.g. node_4 or node_C.4
        previous_sibling: (str)
            the dialog id of the previous sibling e.g. node_3 or node_C.3
            default = None
        parent: (str)
            the dialog id of the parent node e.g. node_C.0
            default = None
        value: (str)
            the answer response
        """
        dict_  = {"conditions": condition_name,
                     "context": None,\
                     "created": self.date_created,\
                     "description": None,\
                     "dialog_node": node_name,\
                     "next_step": None, \
                     "metadata": None, \
                     "parent" : parent, \
                     "previous_sibling": previous_sibling, \
                     "updated" : self.date_updated, \
                     "output": {"text": value}}
        return dict_

    def set_conditional_node(self, intentPrefix, nodeCode):
        """
        # Set conditional node for this group of dialog nodes
        """
        dict_  = {"conditions": "\""+intentPrefix+"\""" == intent[0].intent.substring(0,2)",\
                "context": None,\
                "created": self.date_created,\
                "description": None,\
                "dialog_node": "node_" + nodeCode + "_0",\
                "next_step": {"dialog_node": "node_" + nodeCode + "_1",\
                "behavior": "jump_to",\
                "selector": "condition"},\
                "metadata": None,\
                "output": {},\
                "parent": None,\
                "previous_sibling": None,\
                "updated": self.date_updated}
        self.conditional_node =  dict_
        return self

    def __prepend_handle__(self, intentlist, intentPrefix, nodeCode):
        """
        Alters the name of each condition and conversation (dialog) node (originally in the form node_#) by including the class of each command:
        Example
        ---------
        Condition:
            "What is the NDIS?"
        Old Condition Names:
            "#What_is_the_NDIS"
        New Condition Names:
            "#O.What_is_the_NDIS"
        Old Node Names
            node_1, node_2, node_3 .. (All command)
        New Node Names
            node_314_1, node_314_2.. (Critical Commands)
            node_315_1, node_315_2.. (On-topic Commands)
            node_316_1, node_316_2.. (System tCommands)
            node_317_1, node_317_2.. (Chit-chat Commands)
        Positional arguments
        --------------------
        intentlist: list
            list of intents or conditions
        handlelist: list
            list containing the class of each command, either 'Critical', 'On-topic', 'System' or 'Chit-chat'
        """
        processedCondition = []
        for i, condition in enumerate(intentlist):
            condition = intentlist[i]
            if condition in processedCondition:
                continue
            processedCondition.append(condition)
            if not isinstance(condition, tuple):
                condition_name = string2condition(condition)
            else:
                intent = condition[0]
                entityType = condition[1]
                entityValue = condition[2]
                condition_name = self.intent_names[intent] + getMultipleEntityString(entityType, entityValue)
            # print('condition name: ' + condition_name)
            if condition_name not in self.indices:
                print('ERROR - condition ' + condition_name + ' not in index\nIndices: ' + str(self.indices))
                print (str(intentlist))
                print('This happens typically when you have a more general condition ahead of a more specific condition in the spreadsheet!')
                print('Stopping now. Please check your spreadsheet');
                sys.exit()
            index = self.indices[condition_name]
            dialog.__handle_check__(self, condition_name, intentPrefix, nodeCode, index)
        self.json[0]['previous_sibling'] = None
        return self

    def __conversation_start__(self):
        """
        Returns a converstion_start node:
            Example,
        {
            "conditions": "conversation_start",
            "context": null,
            "description": null,
            "dialog_node": "node_0",
            "go-to": null,
            "metadata": null,
            "output": {
                "text": "Hello"
            },
            "parent": null,
            "previous_sibling": null
        }
        No arguments
        """
        dict_ = {"conditions" : "conversation_start", \
                                                "context" : None, \
                                                "description" : None, \
                                                "dialog_node" : 'node_0', \
                                                "go-to" : None, \
                                                "metadata" : None, \
                                                "output" : {"text" : 'Hello'}, \
                                                "parent" : None, \
                                                "previous_sibling" : None}

        return [dict_]

def config_load_name(config):
    """
    Load workspace name from config
    """
    if 'Workspace Name' not in config:
        now = str(datetime.datetime.now()).split('.')[0]
        return 'DefaultName ' + now
    else:
        return str(config['Workspace Name'])


def config_load_sheet(config, item_topic):
    """
    Load excel spreadsheet from config file
    """
    if 'filename' not in config[item_topic] or 'sheet' not in config[item_topic]:
        print('ERROR: filename or sheet not found in config of ' + item_topic)
        sys.exit()
    sheet = load_xl(config[item_topic]['filename'], config[item_topic]['sheet'])
    assert 'filter header' in config[item_topic]
    assert 'filter by regex' in config[item_topic]
    indices_list = get_reduced_indices(sheet.data[config[item_topic]['filter header']], \
                regex=config[item_topic]['filter by regex'])
    return reduce_data(sheet, indices_list)

def config_load_intents(config, item_topic):
    """
    # Loading intents as specified in the config file
    """
    sheet = config_load_sheet(config, item_topic)
    intents_config = config[item_topic]
    intents_data = load_intents(sheet, intents_config)
    print ('ADDING INTENTS: ' + str(len(intents_data.json)) + ' intents added for "' + item_topic + '"')
    return intents_data


# Loading entities as specified in the config file
def config_load_entities(config, item_topic):
    """
    # Loading entities as specified in the config file
    """
    sheet = config_load_sheet(config, item_topic)
    e_names = sheet.data[config[item_topic]['entity header']]
    e_values = sheet.data[config[item_topic]['value header']]
    e_synonyms = sheet.data[config[item_topic]['synonym header']]

    fuzzyMatch = True
    if 'fuzzy match' in config[item_topic]:
        fuzzyMatch = config[item_topic]['fuzzy match']

    final_entities = entities(e_names, e_values, e_synonyms, fuzzyMatch)
    print ('ADDING ENTITIES: ' + str(len(final_entities.json)) + ' entities added for "' + item_topic + '"')
    return final_entities

def getEntityString(entityType, entityValue):
    """
    # return entity string formatted
    e.g. @fruit:apple
    """
    if entityType == '':
        return ''
    e_type = ' && @' + string2condition(entityType.strip())
    if entityValue == '':
        return e_type
    e_value = entityValue.strip()

    # If the entity value has non-alphanumeric characters
    # we put it between a bracket
    if not e_value.isalnum():
        e_value = '(' + e_value + ')'

    return e_type + ':' + formatEntityValue(e_value)


def getMultipleEntityString(entityTypes, entityValues):

    entityConditionString = ''

    if entityTypes == '':
        return ''

    entityTypeList = entityTypes.split('\n');
    entityValueList = entityValues.split('\n');

    if (len(entityTypeList) != len(entityValueList)):
        print('ERROR: Number of Entity Classes and Entity Values differ in Condition!')
        print('Entity Classes: ' + entityTypes)
        print('Entity Values: ' + entityValues)
        sys.exit()

    for i in range(len(entityTypeList)):
        entityConditionString = entityConditionString + getEntityString(entityTypeList[i], entityValueList[i])

    return entityConditionString

def config_load_dialogs(config, item_topic):
    """
    # Loading dialogs as specified in the config file
    """
    # Load the excel spreadsheet
    sheet = config_load_sheet(config, item_topic)

    # Obtain the conditions and answers
    values = sheet.data[config[item_topic]['answers']]

    # Get emotion parameters
    if 'emotion header' in config[item_topic]:
        emotions = sheet.data[config[item_topic]['emotion header']]
        assert(len(emotions) == len(values))
        for i in range(len(emotions)):
            if (emotions[i] != ""):
                emotionTag = '<mct:gesture context="' + emotions[i]  + '"/>'
                values[i] = emotionTag + values[i]

    parameters = {}
    parameters["breakTag"] = ""
    parameters["yesNoTag"] = ""
    parameters["long answer question"] = "Would you like to know more?"

    if "breakTag" in config:
        parameters["breakTag"] = config["breakTag"]
    if "yesNoTag" in config:
        parameters["yesNoTag"] = config["yesNoTag"]
    if "long answer question" in config:
        parameters["long answer question"] = config["long answer question"]
    if "yesCondition" in config:
        parameters["yesCondition"] = config["yesCondition"]
    if "noCondition" in config:
        parameters["noCondition"] = config["noCondition"]

    if "formatHTML" in config:
        parameters["formatHTML"] = config["formatHTML"]

    # Setting node prefix from config, default 'Z.'.
    intentPrefix = 'Z.'
    if 'intent prefix' in config[item_topic]:
        intentPrefix = config[item_topic]['intent prefix']
        parameters['intent prefix'] = intentPrefix

    # Setting node code from config, default '300', used for node naming
    nodeCode = '300'
    if 'node code' in config[item_topic]:
        nodeCode = config[item_topic]['node code']

    # Generating dialog node
    if 'entity type' in config[item_topic] and 'entity value' in config[item_topic] and 'intent' in config[item_topic]:
        # the node has #Intent + @Entity:entity_value
        entityValue = sheet.data[config[item_topic]['entity value']]
        entityType = sheet.data[config[item_topic]['entity type']]
        intent = sheet.data[config[item_topic]['intent']]
        conditions = list(zip(intent, entityType, entityValue))
        # print(str(conditions))
    elif 'intent' in config[item_topic]:
        conditions = sheet.data[config[item_topic]['intent']]
    elif 'conditions' in config[item_topic]:
        # the node only has #Intent
        conditions = sheet.data[config[item_topic]['conditions']]
    else:
        print('ERROR: No condition specified! Expecting \'conditions\' or \'entity type\'')
        sys.exit()

    # Create dialog nodes
    final_dialog = dialog(conditions, values, parameters).__prepend_handle__(conditions, intentPrefix, nodeCode)
    # Set conditional node
    final_dialog = final_dialog.set_conditional_node(intentPrefix, nodeCode)

    # Obtain long answers and their indices
    long_answer_indices = []
    if 'long answer' in config[item_topic]:
        long_answer_indices = get_reduced_indices(sheet.data[config[item_topic]['long answer']], \
                                    regex = config[item_topic]['long answer filter by regex'])
        long_answers = [formatAnswer(sheet.data[config[item_topic]['long answer']][long_answer_index]) for long_answer_index in long_answer_indices]

    # Obtain follow on questions and their indices
    if 'follow on intent' in config[item_topic] and 'follow on wording' in config[item_topic]:
        follow_on_indices = get_reduced_indices(sheet.data[config[item_topic]['follow on intent']], \
                                    regex = config[item_topic]['follow on filter by regex'])

        # If we already have long answer, we don't include the follow on question
        follow_on_indices = sorted(set(follow_on_indices) - set(long_answer_indices))

        follow_on_intents = [sheet.data[config[item_topic]['follow on intent']][follow_on_index] for follow_on_index in follow_on_indices]
        follow_on_wordings = [sheet.data[config[item_topic]['follow on wording']][follow_on_index] for follow_on_index in follow_on_indices]

    # Add long answers to dialog nodes
    if 'long answer' in config[item_topic] and len(long_answer_indices) != 0:
        final_dialog = dialog.long_answers(final_dialog, long_answers, long_answer_indices, nodeCode)

    # Add follow on questions to dialog nodes
    if 'follow on intent' in config[item_topic] and len(follow_on_indices) != 0:
        final_dialog = dialog.follow_on_questions(final_dialog, follow_on_intents, follow_on_wordings, follow_on_indices, nodeCode)

    # Reporting to STDOUT
    print ('ADDING DIALOGS: ' + str(len(final_dialog.json)) + ' dialog nodes added for "' + item_topic + '"')

    return final_dialog


def mergeDialogs(dialogList):
    """
    # Finally merge all dialogs into a list of JSON/dictionaries
    """
    # We assume the input list is not empty.
    assert (len(dialogList)>0)

    JSONList = dialogList[0].conv_start

    previousSibling = 'node_0'
    # First we add the conditional nodes, and make sure they line up
    # This way we can inspect the conditional nodes at the beginning of
    # the JSON file.
    for myDialog in dialogList:
        conditional_node = myDialog.conditional_node
        conditional_node['previous_sibling'] = previousSibling
        previousSibling = conditional_node['dialog_node']
        JSONList = JSONList + [conditional_node]

    # Then we add the actual nodes.
    for myDialog in dialogList:
        JSONList = JSONList + myDialog.json

    return JSONList

def formatURL(text):
    """
    Take text with eg 'NDIS [URL Info] (www.url.com) works by...'
    to '<mct:link><mct:url>www.url.com</mct:url><mct:label>URL Info</mct:label></mct:link> works by...'
    """
    return re.sub(r'\[(.*?)\]\s+\((.*?)\)', r'<mct:link><mct:url>\2</mct:url><mct:label>\1</mct:label></mct:link>', text)

def formatList(text):
    """
    Take text with eg 'NDIS is \n- a\n- b\n- c\nD'
    to 'NDIS is <ul><li> a</li><li> b</li><li> c</li><ul>D'
    """

    textList = re.split('\n *- *', text)

    returnText = textList[0]

    if len(textList) > 1:
        returnText = returnText + '\n'

    for i in range(1,len(textList)):
        if i == 1:
            returnText = returnText + '<ul>'
        if i<len(textList)-1:
            if '\n\n' in textList[i]:
                lineSplit = textList[i].split('\n\n', 1)
                returnText = returnText + '<li>' + lineSplit[0] + '</li></ul>\n\n' + lineSplit[1] + '\n<ul>'
            else:
                returnText = returnText + '<li>' + textList[i] + '</li>'
        else:
            newLineList = textList[i].split('\n', 1)
            tail = ""
            if len(newLineList) == 2:
                tail = newLineList[1]
            returnText = returnText + '<li>' + newLineList[0] + '</li></ul>' + tail

    return returnText

def formatDefinitions(text):
    """
    Take text with eg 'The ~Access Request Form~ is...'
    to 'The <em>Access Request Form</em> is...'
    """
    return re.sub(r'~(.*?)~', r'<em>\1</em>', text)

def formatStrongText(text):
    """
    Take text with eg 'The *Strong Tab* is...'
    to 'The <strong>Strong Tab</strong> is...'
    """
    return re.sub(r'\*(.*?)\*', r'<strong>\1</strong>', text)

def formatBreakTags(text):
    """
    Take text with eg 'A\nB'
    to 'A<br/>B'
    """
    return re.sub(r'\n', r'<br/>', text)

def formatEmail(text):
    """
    Take text with email addresses like 'abc@d.com'
    to 'abc\@d.com'
    This is to escape the entity reference in Watson Assistant
    """
    return re.sub(r'(.*?)@(.*\..*)', r'\1\@\2', text)


def formatAnswer(text, formatHTML=True):
    """
    Take in answer text, format the appropriate:
    - Lists
    - Definitions
    - URLs
    """
    newText = formatEmail(text)

    if not formatHTML:
        return newText

    # Formatting for HTML
    newText = formatList(newText)
    newText = formatDefinitions(newText)
    newText = formatStrongText(newText)
    newText = formatBreakTags(newText)
    return formatURL(newText)


if __name__ == "__main__":
    """
    # Main method
    """

    message = "We no longer handle ingestion directly this way, please use the new methods with \'updateEverything.sh\'."

    print(message)


