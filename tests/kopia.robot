*** Settings ***
Library    SSHLibrary

*** Variables ***
${ADMIN_USER}    admin
${ADMIN_PASSWORD}    Nethesis,1234
${module_id}    ${EMPTY}

*** Keywords ***
Login to cluster-admin
    New Page    https://${NODE_ADDR}/cluster-admin/
    Fill Text    text="Username"    ${ADMIN_USER}
    Click    button >> text="Continue"
    Fill Text    text="Password"    ${ADMIN_PASSWORD}
    Click    button >> text="Log in"
    Wait For Elements State    css=#main-content    visible    timeout=10s

*** Test Cases ***
Check if kopia is installed correctly
    ${output}  ${rc} =    Execute Command    add-module ${IMAGE_URL} 1
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}  0
    &{output} =    Evaluate    ${output}
    Set Global Variable    ${module_id}    ${output.module_id}

Take screenshots
    [Tags]    ui
    Import Library    Browser
    New Browser    chromium    headless=True
    New Context    ignoreHTTPSErrors=True
    Login to cluster-admin
    Go To    https://${NODE_ADDR}/cluster-admin/#/apps/${module_id}
    Wait For Elements State    iframe >>> h2 >> text="Status"    visible    timeout=10s
    Sleep    5s
    Take Screenshot    filename=${OUTPUT DIR}/browser/screenshot/1._Status.png
    Go To    https://${NODE_ADDR}/cluster-admin/#/apps/${module_id}?page=settings
    Wait For Elements State    iframe >>> h2 >> text="Settings"    visible    timeout=10s
    Sleep    5s
    Take Screenshot    filename=${OUTPUT DIR}/browser/screenshot/2._Settings.png
    Close Browser

Check if kopia can be configured
    ${rc} =    Execute Command    api-cli run module/${module_id}/configure-module --data '{"host": "kopia.test.example.org", "admin_password": "Admin-pass-2026"}'
    ...    return_rc=True  return_stdout=False
    Should Be Equal As Integers    ${rc}  0

Check if kopia works as expected
    ${rc} =    Execute Command    curl -sk -o /dev/null -w '\%{http_code}' https://127.0.0.1:51515/ | grep -q 401
    ...    return_rc=True  return_stdout=False
    Should Be Equal As Integers    ${rc}  0

Check if a machine can enroll, back up and restore
    # The node is its own client: the script returned by add-client runs in a kopia container.
    # The desktop script only enrolls, so the test takes the snapshot a user would start in KopiaUI
    # sh -i reads the script like a paste in a terminal
    ${rc} =    Execute Command    api-cli run module/${module_id}/add-client --data '{"username": "ci", "hostname": "runner"}' | python3 -c 'import json,sys; open("/root/kopia-ci.sh","w").write(json.load(sys.stdin)["shell"])'
    ...    return_rc=True  return_stdout=False
    Should Be Equal As Integers    ${rc}  0
    ${rc} =    Execute Command    mkdir -p /root/kopia-ci-home && echo ci-data > /root/kopia-ci-home/file.txt
    ...    return_rc=True  return_stdout=False
    ${output}  ${rc} =    Execute Command    podman run --rm --network=host --add-host kopia.test.example.org:127.0.0.1 -e HOME=/home/u -e KOPIA_CONFIG_PATH=/home/u/.config/kopia/repository.config -e KOPIA_PERSIST_CREDENTIALS_ON_CONNECT=true -v /root/kopia-ci-home:/home/u:Z -v /root/kopia-ci.sh:/enroll.sh:ro,Z --entrypoint sh docker.io/kopia/kopia:0.23.1 -c 'sh -i < /enroll.sh && kopia snapshot create /home/u && kopia snapshot restore /home/u /tmp/restored && cat /tmp/restored/file.txt'
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}  0
    Should Contain    ${output}    ci-data
    ${rc} =    Execute Command    api-cli run module/${module_id}/list-clients | grep -q '"state": "ok"'
    ...    return_rc=True  return_stdout=False
    Should Be Equal As Integers    ${rc}  0

Check if a machine cannot delete its snapshots
    ${output}  ${rc} =    Execute Command    podman run --rm --network=host --add-host kopia.test.example.org:127.0.0.1 -e HOME=/home/u -e KOPIA_CONFIG_PATH=/home/u/.config/kopia/repository.config -e KOPIA_PERSIST_CREDENTIALS_ON_CONNECT=true -v /root/kopia-ci-home:/home/u:Z --entrypoint sh docker.io/kopia/kopia:0.23.1 -c 'kopia snapshot delete --delete "$(kopia snapshot list /home/u --json | grep -o -m1 "\\"id\\": *\\"[0-9a-f]*" | grep -o "[0-9a-f]*$")"'
    ...    return_rc=True    return_stderr=True    return_stdout=False
    Should Not Be Equal As Integers    ${rc}  0
    Should Contain    ${output}    access denied

Check if the server still expires old snapshots
    # One snapshot kept: the machine asks the server to apply the retention, it cannot delete itself
    ${rc} =    Execute Command    api-cli run module/${module_id}/get-configuration | python3 -c 'import json,sys; d=json.load(sys.stdin); d.update(keep_latest=1, keep_hourly=0, keep_daily=0, keep_weekly=0, keep_monthly=0, keep_annual=0); print(json.dumps({k: d[k] for k in ("host", "keep_latest", "keep_hourly", "keep_daily", "keep_weekly", "keep_monthly", "keep_annual")}))' | api-cli run module/${module_id}/configure-module --data -
    ...    return_rc=True  return_stdout=False
    Should Be Equal As Integers    ${rc}  0
    ${output}  ${rc} =    Execute Command    podman run --rm --network=host --add-host kopia.test.example.org:127.0.0.1 -e HOME=/home/u -e KOPIA_CONFIG_PATH=/home/u/.config/kopia/repository.config -e KOPIA_PERSIST_CREDENTIALS_ON_CONNECT=true -v /root/kopia-ci-home:/home/u:Z --entrypoint sh docker.io/kopia/kopia:0.23.1 -c 'for i in 1 2 3; do echo $i > /home/u/file.txt; kopia snapshot create /home/u >/dev/null || exit 1; done; kopia snapshot list /home/u | grep -c UTC'
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}  0
    Should Be Equal As Strings    ${output}    1

Check if a password reset disconnects the machine
    ${rc} =    Execute Command    api-cli run module/${module_id}/reset-client-password --data '{"name": "ci@runner"}' >/dev/null
    ...    return_rc=True  return_stdout=False
    Should Be Equal As Integers    ${rc}  0
    ${output}  ${rc} =    Execute Command    podman run --rm --network=host --add-host kopia.test.example.org:127.0.0.1 -e HOME=/home/u -e KOPIA_CONFIG_PATH=/home/u/.config/kopia/repository.config -e KOPIA_PERSIST_CREDENTIALS_ON_CONNECT=true -v /root/kopia-ci-home:/home/u:Z --entrypoint sh docker.io/kopia/kopia:0.23.1 -c 'kopia snapshot create /home/u'
    ...    return_rc=True    return_stderr=True    return_stdout=False
    Should Not Be Equal As Integers    ${rc}  0
    Execute Command    rm -rf /root/kopia-ci-home /root/kopia-ci.sh

Check if kopia is removed correctly
    ${rc} =    Execute Command    remove-module --no-preserve ${module_id}
    ...    return_rc=True  return_stdout=False
    Should Be Equal As Integers    ${rc}  0
