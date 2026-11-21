*** Settings ***
Library    SSHLibrary
Resource    kopia.resource

*** Test Cases ***
Check if a machine can enroll, back up and restore
    # The node is its own client: the script returned by add-client runs in a kopia container.
    # The desktop script only enrolls, so the test takes the snapshot a user would start in KopiaUI
    # sh -i reads the script like a paste in a terminal
    ${rc} =    Execute Command    api-cli run module/${module_id}/add-client --data '{"username": "ci", "hostname": "runner"}' | python3 -c 'import json,sys; open("/root/kopia-ci.sh","w").write(json.load(sys.stdin)["shell"])'
    ...    return_rc=True  return_stdout=False
    Should Be Equal As Integers    ${rc}  0
    # Random data neither compresses nor dedups, so Kopia really splits, encrypts and sends 150M
    ${rc} =    Execute Command    mkdir -p /root/kopia-ci-home && echo ci-data > /root/kopia-ci-home/file.txt && for i in 1 2 3; do head -c 50M /dev/urandom > /root/kopia-ci-home/big$i.bin; done
    ...    return_rc=True  return_stdout=False
    ${output}  ${rc} =    Execute Command    ${CLIENT} -v /root/kopia-ci.sh:/enroll.sh:ro,Z --entrypoint sh ${KOPIA_IMAGE} -c 'sh -i < /enroll.sh && cd /home/u && sha256sum big*.bin > /tmp/sums && kopia snapshot create /home/u && kopia snapshot restore /home/u /tmp/restored && cat /tmp/restored/file.txt && cd /tmp/restored && sha256sum -c /tmp/sums'
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}  0
    Should Contain    ${output}    ci-data
    Should Contain    ${output}    big1.bin: OK
    Should Contain    ${output}    big2.bin: OK
    Should Contain    ${output}    big3.bin: OK
    ${rc} =    Execute Command    api-cli run module/${module_id}/list-clients | grep -q '"state": "ok"'
    ...    return_rc=True  return_stdout=False
    Should Be Equal As Integers    ${rc}  0
    ${output}  ${rc} =    Execute Command    api-cli run module/${module_id}/list-clients | python3 -c 'import json,sys; print([c["error_count"] for c in json.load(sys.stdin)["clients"] if c["name"] == "ci@runner"])'
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}  0
    Should Be Equal As Strings    ${output}    [0]
    ${output}  ${rc} =    Execute Command    api-cli run module/${module_id}/list-clients | python3 -c 'import json,sys; print([c["total_size"] > 150000000 for c in json.load(sys.stdin)["clients"] if c["name"] == "ci@runner"])'
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}  0
    Should Be Equal As Strings    ${output}    [True]
    ${output}  ${rc} =    Execute Command    api-cli run module/${module_id}/list-client-folders --data '{"name": "ci@runner"}' | python3 -c 'import json,sys; print([f["size"] > 0 for f in json.load(sys.stdin)["folders"] if f["path"] == "/home/u"])'
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}  0
    Should Be Equal As Strings    ${output}    [True]

Check if a machine cannot delete its snapshots
    ${output}  ${rc} =    Execute Command    ${CLIENT} --entrypoint sh ${KOPIA_IMAGE} -c 'kopia snapshot delete --delete "$(kopia snapshot list /home/u --json | grep -o -m1 "\\"id\\": *\\"[0-9a-f]*" | grep -o "[0-9a-f]*$")"'
    ...    return_rc=True    return_stderr=True    return_stdout=False
    Should Not Be Equal As Integers    ${rc}  0
    Should Contain    ${output}    access denied

Check if the server still expires old snapshots
    # One snapshot kept: the machine asks the server to apply the retention, it cannot delete itself
    ${rc} =    Execute Command    api-cli run module/${module_id}/get-configuration | python3 -c 'import json,sys; d=json.load(sys.stdin); d.update(keep_latest=1, keep_hourly=0, keep_daily=0, keep_weekly=0, keep_monthly=0, keep_annual=0); print(json.dumps({k: d[k] for k in ("host", "keep_latest", "keep_hourly", "keep_daily", "keep_weekly", "keep_monthly", "keep_annual")}))' | api-cli run module/${module_id}/configure-module --data -
    ...    return_rc=True  return_stdout=False
    Should Be Equal As Integers    ${rc}  0
    ${output}  ${rc} =    Execute Command    ${CLIENT} --entrypoint sh ${KOPIA_IMAGE} -c 'for i in 1 2 3; do echo $i > /home/u/file.txt; kopia snapshot create /home/u >/dev/null || exit 1; done; kopia snapshot list /home/u | grep -c UTC'
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}  0
    Should Be Equal As Strings    ${output}    1

Check if the cluster backup can leave the repository out
    # module-dump-state runs before each cluster backup, as the core would call it
    ${rc} =    Execute Command    api-cli run module/${module_id}/configure-module --data '{"backup_repository": false}'
    ...    return_rc=True  return_stdout=False
    Should Be Equal As Integers    ${rc}  0
    ${rc} =    Execute Command    runagent -m ${module_id} module-dump-state
    ...    return_rc=True  return_stdout=False
    Should Be Equal As Integers    ${rc}  0
    ${rc} =    Execute Command    runagent -m ${module_id} sh -c 'grep -qx volumes/kopia-repository/data "$AGENT_INSTALL_DIR/etc/state-exclude.conf" && python3 -c "import json; json.load(open(\"policies.json\"))" && test ! -e maintenance-paused'
    ...    return_rc=True  return_stdout=False
    Should Be Equal As Integers    ${rc}  0
    ${rc} =    Execute Command    api-cli run module/${module_id}/configure-module --data '{"backup_repository": true}'
    ...    return_rc=True  return_stdout=False
    Should Be Equal As Integers    ${rc}  0
    ${rc} =    Execute Command    runagent -m ${module_id} sh -c 'module-dump-state && ! grep -q kopia-repository/data "$AGENT_INSTALL_DIR/etc/state-exclude.conf" && test -e maintenance-paused && module-cleanup-state'
    ...    return_rc=True  return_stdout=False
    Should Be Equal As Integers    ${rc}  0
