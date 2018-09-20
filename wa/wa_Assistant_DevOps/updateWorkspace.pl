#!/usr/bin/perl -w


$toUserName = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx";
$toPassword = "yyyyyyyyyyyy";
$answerFile = "./path_to/answers_added.json";
$toWorkspace = "zzzzzzzz-zzzz-zzzz-zzzz-zzzzzzzzzzzz";

$api_url = "https://gateway.watsonplatform.net/assistant/api";

`curl -k -u "$toUserName":"$toPassword" -X POST --header "Content-Type: application/json" --data @"$answerFile" "$api_url/v1/workspaces/$toWorkspace?version=2018-02-16"`;


