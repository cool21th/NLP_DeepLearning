# WCS-Excel2JSON

Python programs that automatically update content from Spreadsheets to a Watson Conversation Service (WCS) Workspace

## Benefits

- Content writers don't need to learn a new tool, they already know spreadsheets.
- Keeping source data in spreadsheets means they can be managed in a document tracking repository.
- Collect up content but mark it for exclusion if it's not ready yet.
- Include review comments and other information on the same row.
- Search, filter and make pivot reports in your spreadsheet.
- Automatic handling for several nifty conversation features (see below).

## Supported Conversation Features

**Simple Answers**
For if the answer is stright-forward.
```
User: Why is the sky blue?
Watson: It's blue because air is blue.
```

**Simple Answer Variants**
For variety, give more than one answer to common questions.
```
User: Hello
Watson: Hello there.
User: Hello
Watson: Hi, how can I help?
```

**Long Answers**
For if you want to give the bare bones reply first and offer a prompt for more information if they want to know the details.
```
User: Am I eligible to apply?
Watson: All people are eligible to apply.  Do you want to know more?
User: Yes
Watson: Here is the application process, etc...
```
The long answers functionality also works if the user repeats themselves, because if they are asking the same question they probably _do_ want to know more.
```
User: Am I eligible to apply?
Watson: All people are eligible to apply.  Do you want to know more?
User: But I want to know if I am eligible to apply!  (<-- same intent)
Watson: Here is the application process, etc...
```

**Broad Intents**
Where the answer depends on an entity.
```
User: What does sinecure mean?
Watson: Sinecure is a profitable job requiring hardly any work.
User: What does antinome mean?
Watson: Antinome is a contradiction.
```

**Retaining Context**
To answer the last intent if just an entity is mentioned.
```
User: What does sinecure mean?
Watson: Sinecure is a profitable job requiring hardly any work.
User: antinome?
Watson: Antinome is a contradiction.
```

## Source Data Spreadsheets

Data for intents, entities and answers is authored in spreadsheets.  You can use many individual files or combine them all into one file. The format of the spreadsheets is very flexible.  The columns can be in any order and you can add as many columns as you like.  For large files, you may find that autofilters in the spreadsheets are useful.

Having multiple sheets can be useful for dividing content up into topics and allowing different people to work separately on content.

There are examples of the spreadsheets in the ./data folder.

### Intents Spreadsheets

An Intents sheet needs to have, at a minimum, three columns.  These specify the __intent__ names, the __example__ training data and the __status__ of that row.  The headings of these columns need to match with the column headings in the replace_intents_config.json file.

Each row of the sheet defines a piece of training data for training an intent, so the intent name will be repeated across multiple rows.  Whitespace and punctuation in the intent name will be automatically removed when the intent is added into the Conversation Workspace.

![Example intents spreadsheet](https://media.github.ibm.com/user/17877/files/841ff5ca-9c8e-11e7-8176-062334164ec8)

Suggested other columns that may help the person doing question curation are: Date Added, Source, Last Modified, Editor Name, Reviewer Name, Original Source Text, and Comment.  These columns have no effect on the functionality of the WCS-Excel2JSON scripts.

### Entities Spreadsheets

An Entities sheet needs to have, at a minimum, 4 columns.  These specify the entity type, entity value, synonym and status of the row.

To specify multiple synonyms, repeat the entity row and put the new synonym on the new row.

![Example entities spreadsheet](https://media.github.ibm.com/user/17877/files/a0f28f58-9c95-11e7-81f9-dbb598c09f9b)

Suggested other columns that may help with entity curation are: date added, date modified, editor name and comment.

### Answers Spreadsheets

An Answers sheet needs to have, at a minimum, 3 columns.  These specify the __intent__, the __answer__ to give for that intent and the __status__ of the row.

To add __simple answer variants__, add extra rows, repeating the same intent for each variant answer.

Optional extra columns that have an impact of the WCS-Excel2JSON scripts:
- __Entity Type__: If the intent is a broad intent, this is the entity type that the answer applies to.  You can have one answer apply for an entire type of entities.
- __Entity Value__: For if you wish to talor the answer to just one value within an entity.
- __Long Answer__: If you want to break an answer into two parts, the normal Answer column is provided first along with a prompt "do you want to know more?"  The Long Answer part is given if the user says "yes" or asks the same intent again.  You may wish to do this for readability (if the chat window is small or the full answer is particularly long) or brevity (especially useful for chat bots that use speech).  Warning: For any intent that uses the long answer feature, do not add simple answer variant rows as these both use the same functionaility within the Conversation Service workspace.

![Example answers spreadsheet](https://media.github.ibm.com/user/17877/files/4e3b2932-9ede-11e7-9507-e97c35e66d4c)

Note, in the above picture:
- Rows 2 to 4 are for a __Broad Intent__ with diferent answers based on the entity.  Note that row 2 is for anything matching the entity type, and row 3 is only for when the specific entity value is matched.
- Row 3 shows a __Long Answer__, where the Answer column is the initial response, which is accompanied by the question "Do you want to know more?".  The Long Answer column is returned if the user says "yes".
- Rows 5 and 6 are __Simple Answer Variants__.  One of these answers will be randomly selected when the intent is matched.
- Row 7 is a __Simple Answer__.  In this case it is marked draft, so whether it will be added into the WCS workspace will depend on the *filter by regex* specified in replace_simple_answers_config.json
- Row 8 notes a __Complex Answer__ which would be excluded then the script is run as it will be implemented directly in the WCS Tool (under a different node).  This answer is included in the answer spreadsheet for completeness.

You may add other columns to the answer spreadsheet.  Suggested other columns that have no impact on the WCS-Excel2JSON scripts: Date added, reference to source, subject matter expert name, editor, reviewer, last modified.

## Watson Conversation Workspace

The Watson Conversation Workspace to add all these intents, entities and answers to needs to have been set up with nodes that can accept the answers.  If you have two answer spreadsheets you will need two nodes for those answers to be added to.  These nodes should each have a condition that matches the intents answered by the answer sheet and chould contain a node with the condition "true" that jumps to the anything_else node at the bottom of the dialog tree.  These nodes act as "folders" to contain all the answers.

![Example dialog layout in Conversation Tool](https://media.github.ibm.com/user/17877/files/56e00fba-9c97-11e7-8730-335eabd4577d)

Any answers that are more complex than allowed for by the WCS-Excel2JSON tool can be implemented manually in the WCS Tool, for example complex process flows.  These should be put under different nodes to where the simple answer content is being added, so that they are not deleted when the simple answers are updated.

You will need to export the Watson Conversation Service workspace as a JSON file in order to use the WCS-Excel2JSON scripts.

## Configuration files

How to take the data from the spreadsheets and update the Conversation Worksapce JSON file is controlled by three config files.

### Config file for replacing intents
./src/replace_intents_config.json

- Workspace Name: What to name this workspace.
- Old Workspace.filename: Location and name of JSON workspace file.
- Output File: Location and name of the file to write with the intents added.
- Keep Previous Intents: Set this to false to remove all the old training data for intents.
- New Intents: An array listing the sections to add.

Then for each named section...
- filename: Name and location of the spreadsheet containing the intents.
- sheet: Name of the tab within the spreadsheet to take intents from.
- intent header: Column name to use as the intent name.
- intent prefix: This prefix will be added to the name of each intent, to group intents together.
- question header: Column name for the training example.
- filter header: This column is used for controlling which rows to import.
- filter by regex: This is a regular expression (regex) for how to match the filter column text.

### Config file for replacing entities
./src/replace_entities_config.json

- Workspace Name: What to name the workspace.
- Old Workspace.filename: Path to the source JSON workspace file.   If the entities are being replaced following the intents, make sure this file is the same name as the output file in the intents config file.
- Output File: Location and filename where to put the output JSON workspace with etities added.
- Keep Previous Entities: Set to false to remove all the entities currently in the workspace.
- New Entities: Array listing all the entities sections.

Then for each section...
- filename: Source spreadsheet filename and path.
- sheet: Name of the tab within the spreadsheet to take entities from.
- entity header: Column heading for the entity type.
- value header: Column heading for the entity value.
- synonym header: Column heading for the synonym.
- filter header: Column heading for whether to import the row.
- filter by regex: A regular expression that can be matched to values in the filter header column to know whether to import that row.

### Config file for replacing simple answers
./src/replace_simple_answers_config.json

- Workspace Name: Title to set on the workspace.
- Old Workspace.filename: Location and filename of the JSON workspace. If the answers are being replaced following the entities, make sure this file is the same name as the output file in the entities config file.
- Output File: Location and filename to write the output JSON workspace with answers added.
- Collapse dialog by intent: Enable using *Multiple Conditional Responses* to combine answers that address one intent.
- breakTag: For answers with line breaks in the spreadsheet, this can be used to replace the linebreak with markup.
- long answer question: For rows that have a long answer column filled in, this text will be added to the end of the brief answer.
- yesNoTag: This text will be added after the first half of the brief answer and other places where a yes or no response from the user is wanted.  Useful for adding buttons.
- yesCondition: The node condition used to identify that the user said "yes".
- noCondition: The node condition used to identify that the user said "no".
- responseToNo: This answer will be given when the user says no in response to a long answer prompt.
- sameIntentCondition: This condition is used to identify if the user did not mention a new intent.  This allows the system to remember the last intent when only an entity is mentioned.
- Stitching Nodes: Array of objects specifying the dialog node to attach answers to and the section that contains the data to add to it.
  - prune_node: Title or ID of the dialog node to attach answers to.
  - prune_topic: Name of a section below.

And then for each section...
- filename: Location and filename of the JSON workspace file to add answers to.
- sheet: The tab within the spreadsheet that contains answers.
- intent: Column heading for the name of the intent that this answer is for.
- intent prefix: This prefix will be added to the intent names for this section.  Useful for grouping answers together.
- entity type: Column heading for the entity type that this answer is for.
- entity value: Column heading for the entity value that this answer is for.
- node code: Node IDs generated by the script for each answer start at 1.  This *node code* is prepended to the node IDs so that the nodes in each section get unique IDs.  Make sure to give each section a different number.
- answers: Column heading for the answer.  This column is also used for the first half of a long answer.
- long answer: (Optional) Column heading for the second part of a long answer.
- long answer filter by regex: (Optional) Regex used to identity if a long answer has been supplied.
- follow on wording: (Optional) Column heading for the leading question to ask the user that they may wish to know once they read this answer.
- follow on filter by regex: (Optional) Regex used to identity if a follow-on question has been supplied.
- follow on intent: (Optional) Column heading for the intent to use to answer the follow-on question.
- filter header: Column heading for whether to include the answer.
- filter by regex: Regular expression to match the filter column for whether to include this answer.

## To Run
The WCS-Excel2JSON scripts are written in Python.  You can run them from the command line or from executing a script.

You can run each python script on its own, or one after the other in a script.  There is an example script in the ./src folder.
### Requirements
python3.6 <br />
pip3.6 install -r requirements.txt 
### Execute program given current configurations
#### Unix or Mac Shell
$ cd ./src <br />
$ ./updateEverything.sh
#### Windows Command Prompt
C:> cd src <br />
C:> updateEverything.bat
### Expected Output
./output/answers_added.json

## Use On Customer Engagements

This script has not yet gone through the open source approval process, so if you want to provide it to a customer
you will need to have it listed in your contractual agreement as IBM IP, provided on an "unsupported, provided
as-is" basis.  Please check with legal about the most appropriate method for your customer.
