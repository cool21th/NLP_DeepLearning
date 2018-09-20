import os

toUserNaem="XXXX-XXXX-XXXX-XXXX"
toPassword = "YYYYYY"
answerFile = './path_to/answers_added.json"
toWorkspace = "zzzzzz-zzzzz-zzzz"

api_url="https://gateway.watsonplatform.net/assistant/api"

os.system('curl -k -u"' + toUserNeame + '":"' + toPassword+ '" -X POST --header "Content-Type: application/json" --data @"' + answerFile + '" "' + apu_url + '/v1/workspaces/' + toWorkspace + '?version=2018-02-16"')

