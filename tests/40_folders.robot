*** Settings ***
Library    SSHLibrary
Resource    kopia.resource

*** Test Cases ***
Check if read errors of a backup are reported
    # Root in the client container reads any file, so drop the capabilities that bypass the modes
    ${rc} =    Execute Command    mkdir -p /root/kopia-ci-err && echo secret > /root/kopia-ci-err/locked && chmod 000 /root/kopia-ci-err/locked
    ...    return_rc=True  return_stdout=False
    Should Be Equal As Integers    ${rc}  0
    ${rc} =    Execute Command    ${CLIENT} --cap-drop=DAC_OVERRIDE,DAC_READ_SEARCH -v /root/kopia-ci-err:/err:Z --entrypoint sh ${KOPIA_IMAGE} -c 'kopia snapshot create /err; true'
    ...    return_rc=True  return_stdout=False
    Should Be Equal As Integers    ${rc}  0
    ${output}  ${rc} =    Execute Command    api-cli run module/${module_id}/list-clients | python3 -c 'import json,sys; print([c["error_count"] for c in json.load(sys.stdin)["clients"] if c["name"] == "ci@runner"])'
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}  0
    Should Be Equal As Strings    ${output}    [1]
    ${output}  ${rc} =    Execute Command    api-cli run module/${module_id}/list-client-folders --data '{"name": "ci@runner"}' | python3 -c 'import json,sys; print([e["path"] for f in json.load(sys.stdin)["folders"] if f["path"] == "/err" for e in f["errors"]])'
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}  0
    Should Be Equal As Strings    ${output}    ['locked']
    ${rc} =    Execute Command    api-cli run module/${module_id}/remove-client-folder --data '{"name": "ci@runner", "path": "/err"}'
    ...    return_rc=True  return_stdout=False
    Should Be Equal As Integers    ${rc}  0
    ${output}  ${rc} =    Execute Command    api-cli run module/${module_id}/list-clients | python3 -c 'import json,sys; print([c["error_count"] for c in json.load(sys.stdin)["clients"] if c["name"] == "ci@runner"])'
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}  0
    Should Be Equal As Strings    ${output}    [0]
    Execute Command    rm -rf /root/kopia-ci-err

Check if a folder can be added without the Kopia web UI
    ${rc} =    Execute Command    api-cli run module/${module_id}/add-client-folder --data '{"name": "ci@runner", "path": "C:\\\\Users\\\\ci\\\\Documents"}'
    ...    return_rc=True  return_stdout=False
    Should Be Equal As Integers    ${rc}  0
    ${output}  ${rc} =    Execute Command    api-cli run module/${module_id}/list-client-folders --data '{"name": "ci@runner"}' | python3 -c 'import json,sys; print([f["policy"] for f in json.load(sys.stdin)["folders"] if f["path"].endswith("Documents")])'
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}  0
    Should Be Equal As Strings    ${output}    [True]

Check if a folder can be disabled, enabled and removed
    ${rc} =    Execute Command    api-cli run module/${module_id}/disable-client-folder --data '{"name": "ci@runner", "path": "/home/u"}'
    ...    return_rc=True  return_stdout=False
    Should Be Equal As Integers    ${rc}  0
    ${output}  ${rc} =    Execute Command    api-cli run module/${module_id}/list-client-folders --data '{"name": "ci@runner"}' | python3 -c 'import json,sys; print([f["disabled"] for f in json.load(sys.stdin)["folders"] if f["path"] == "/home/u"])'
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}  0
    Should Be Equal As Strings    ${output}    [True]
    ${rc} =    Execute Command    api-cli run module/${module_id}/enable-client-folder --data '{"name": "ci@runner", "path": "/home/u"}'
    ...    return_rc=True  return_stdout=False
    Should Be Equal As Integers    ${rc}  0
    ${output}  ${rc} =    Execute Command    api-cli run module/${module_id}/list-client-folders --data '{"name": "ci@runner"}' | python3 -c 'import json,sys; print([f["disabled"] for f in json.load(sys.stdin)["folders"] if f["path"] == "/home/u"])'
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}  0
    Should Be Equal As Strings    ${output}    [False]
    ${rc} =    Execute Command    api-cli run module/${module_id}/remove-client-folder --data '{"name": "ci@runner", "path": "/home/u"}'
    ...    return_rc=True  return_stdout=False
    Should Be Equal As Integers    ${rc}  0
    ${output}  ${rc} =    Execute Command    api-cli run module/${module_id}/list-client-folders --data '{"name": "ci@runner"}' | python3 -c 'import json,sys; print(len([f for f in json.load(sys.stdin)["folders"] if f["path"] == "/home/u"]))'
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}  0
    Should Be Equal As Strings    ${output}    0
