# WatsonAssistant-DevOp-Example
DevOp Example for Watson Assistant.

## Before you begin

Check if `perl` and `curl` is installed on your system.

## Update a workspace
1. Edit `updateWorkspace.pl` with the appropriate credentials. Modify the following in the file

>$toUserName = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx";

>$toPassword = "yyyyyyyyyyyy";

>$answerFile = "./path_to/answers_added.json";

>$toWorkspace = "zzzzzzzz-zzzz-zzzz-zzzz-zzzzzzzzzzzz";

>$api_url = "https://gateway.watsonplatform.net/assistant/api";

2. Make the `updateWorkspace.pl` file executable

On MAC/LINUX, execute the following in Terminal:

> $ chmod 755 ./updateWorkspace.pl

3. Run the file

> $ ./updateWorkspace.pl


## Promoting a Workspace from A to B
1. Edit `promote_workspace.pl` with the appropriate credentials. Modify the following in the file:

>$fromUserName="XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX";

>$fromPassword="XXXXXX";

>$fromWorkspace="YYYYYYYY-YYYY-YYYY-YYYY-YYYYYYYYYYYY";

>$fromAPI="https://gateway.watsonplatform.net/assistant/api";

>$toUserName = $fromUserName;

>$toPassword = $fromPassword;

>$toWorkspace = "ZZZZZZZZ-ZZZZ-ZZZZ-ZZZZ-ZZZZZZZZZZZZ";

>$toAPI = $fromAPI;

2. Make the `promote_workspace.pl` file executable

On MAC/LINUX, execute the following in Terminal:

> $ chmod 755 ./promote_workspace.pl

3. Run the file

> $ ./promote_workspace.pl
