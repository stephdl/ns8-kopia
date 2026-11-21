*** Settings ***
Library    SSHLibrary
Resource    kopia.resource
# 10_install put the stable release in this scenario: back up a machine with it, move it to the
# image under test, and check the account, the folder and the snapshot are still there
Suite Setup    Skip If    '${SCENARIO}' != 'update'    scenario is ${SCENARIO}, nothing to update

*** Variables ***
${SCENARIO}    install
${UPD_CLIENT}    podman run --rm --network=host --add-host kopia.test.example.org:127.0.0.1 -e HOME=/home/u -e KOPIA_CONFIG_PATH=/home/u/.config/kopia/repository.config -e KOPIA_PERSIST_CREDENTIALS_ON_CONNECT=true -v /root/kopia-upd-home:/home/u:Z

*** Test Cases ***
Back up a machine with the stable release
    ${rc} =    Execute Command    api-cli run module/${module_id}/add-client --data '{"username": "upd", "hostname": "runner"}' | python3 -c 'import json,sys; open("/root/kopia-upd.sh","w").write(json.load(sys.stdin)["shell"])'
    ...    return_rc=True  return_stdout=False
    Should Be Equal As Integers    ${rc}  0
    ${rc} =    Execute Command    api-cli run module/${module_id}/add-client-folder --data '{"name": "upd@runner", "path": "/home/u/docs"}'
    ...    return_rc=True  return_stdout=False
    Should Be Equal As Integers    ${rc}  0
    ${rc} =    Execute Command    mkdir -p /root/kopia-upd-home/docs && echo before-update > /root/kopia-upd-home/docs/file.txt
    ...    return_rc=True  return_stdout=False
    Should Be Equal As Integers    ${rc}  0
    ${rc} =    Execute Command    ${UPD_CLIENT} -v /root/kopia-upd.sh:/enroll.sh:ro,Z --entrypoint sh ${KOPIA_IMAGE} -c 'sh -i < /enroll.sh && kopia snapshot create /home/u/docs'
    ...    return_rc=True  return_stdout=False
    Should Be Equal As Integers    ${rc}  0
    ${output}  ${rc} =    Execute Command    api-cli run module/${module_id}/get-configuration
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}  0
    Set Suite Variable    ${config_before}    ${output}

Update to the image under test
    ${rc} =    Execute Command    api-cli run update-module --data '{"force":true,"module_url":"${IMAGE_URL}","instances":["${module_id}"]}'
    ...    return_rc=True  return_stdout=False
    Should Be Equal As Integers    ${rc}  0
    ${output} =    Execute Command    runagent -m ${module_id} printenv IMAGE_URL
    Should Be Equal    ${output}    ${IMAGE_URL}

Check if kopia answers after the update
    Wait Until Keyword Succeeds    60 seconds    5 seconds    Kopia server answers

Check if the settings survive the update
    ${output}  ${rc} =    Execute Command    api-cli run module/${module_id}/get-configuration
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}  0
    # Only the keys the stable release had: a new release may add settings with their default,
    # and refresh the built-in excludes
    # Robot variables are only visible in the first iterable of a comprehension
    ${changed} =    Evaluate    [k for before, after in [(json.loads($config_before), json.loads($output))] for k in before if k != "default_excludes" and after.get(k) != before[k]]    modules=json
    Should Be Empty    ${changed}

Check if the machine still backs up after the update
    # Same password and certificate: the machine connects without a new script
    ${rc} =    Execute Command    ${UPD_CLIENT} -v /root/kopia-upd.sh:/enroll.sh:ro,Z --entrypoint sh ${KOPIA_IMAGE} -c 'sh -i < /enroll.sh && kopia snapshot create /home/u/docs'
    ...    return_rc=True  return_stdout=False
    Should Be Equal As Integers    ${rc}  0
    ${output}  ${rc} =    Execute Command    runagent -m ${module_id} python3 -c 'import sys, kopia_module as km; print(len(km.machine_snapshots(sys.argv[1])))' upd@runner
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}  0
    Should Be Equal As Strings    ${output}    2
    ${output}  ${rc} =    Execute Command    api-cli run module/${module_id}/list-client-folders --data '{"name": "upd@runner"}' | python3 -c 'import json,sys; print([f["path"] for f in json.load(sys.stdin)["folders"]])'
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}  0
    Should Be Equal As Strings    ${output}    ['/home/u/docs']

Remove the machine of the update test
    ${rc} =    Execute Command    api-cli run module/${module_id}/remove-client --data '{"name": "upd@runner", "delete_snapshots": true}'
    ...    return_rc=True  return_stdout=False
    Should Be Equal As Integers    ${rc}  0

*** Keywords ***
Kopia server answers
    ${rc} =    Execute Command    curl -sk -o /dev/null -w '\%{http_code}' https://127.0.0.1:51515/ | grep -q 401
    ...    return_rc=True  return_stdout=False
    Should Be Equal As Integers    ${rc}  0
