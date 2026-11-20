*** Settings ***
Library    SSHLibrary
Resource    kopia.resource

*** Variables ***
# One file per built-in pattern of DEFAULT_EXCLUDES
${EXC_SKIP}    [".cache/f", "a/Cache/f", "Caches/f", "cache2/f", "Temp/f", "tmp/f", "a.tmp", "~$doc.docx", "$RECYCLE.BIN/f", ".Trash-1000/f", "node_modules/f", "Thumbs.db", ".DS_Store", "hiberfil.sys", "pagefile.sys", "swapfile.sys", "u/NTUSER.DAT.LOG1", "u/AppData/Local/Microsoft/Windows/UsrClass.dat", "u/AppData/Local/Microsoft/Windows/WebCache/f", "u/AppData/Local/Microsoft/Windows/WebCacheLock.dat", "u/AppData/Local/Packages/App/Settings/f", "u/AppData/Local/Packages/App/SystemAppData/f", "u/AppData/Local/Packages/App/LocalCache/EBWebView/f", "u/AppData/Local/Comms/UnistoreDB/store.vol", "u/AppData/Roaming/kopia-ui/f", "u/.local/share/containers/storage/overlay/l/f", "u/.local/share/containers/storage/vfs/l/f", "u/.local/share/docker/overlay2/l/f", "u/.local/share/docker/vfs/l/f", "u/.var/app/org.example.App/cache/f", "u/.config/kopia/repository.config.kopia-password"]
# Files next to the excluded ones that must stay in the backup
${EXC_KEEP}    ["keep.txt", "u/AppData/Local/Comms/Unistore/data/f", "u/AppData/Local/Packages/App/LocalState/f", "u/.local/share/containers/storage/volumes/db/_data/f", "u/.local/share/docker/volumes/db/_data/f", "u/.var/app/org.example.App/data/f"]

*** Test Cases ***
Check if the built-in excluded patterns stay with the admin ones
    # A saved list must not drop the built-in patterns: new ones come with module updates
    ${rc} =    Execute Command    api-cli run module/${module_id}/configure-module --data '{"host": "kopia.test.example.org", "excludes": ["*.iso", "node_modules"]}'
    ...    return_rc=True  return_stdout=False
    Should Be Equal As Integers    ${rc}  0
    ${output}  ${rc} =    Execute Command    api-cli run module/${module_id}/get-configuration | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["excludes"], "node_modules" in d["default_excludes"], "**/.local/share/containers/storage/overlay*/" in d["default_excludes"])'
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}  0
    Should Be Equal As Strings    ${output}    ['*.iso'] True True
    ${output}  ${rc} =    Execute Command    ${CLIENT} --entrypoint sh ${KOPIA_IMAGE} -c 'kopia policy show --global --json' | python3 -c 'import json,sys; i=json.load(sys.stdin)["files"]["ignore"]; print("*.iso" in i, "repository.config.kopia-password" in i)'
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}  0
    Should Be Equal As Strings    ${output}    True True

Check if the built-in excluded patterns skip their files
    # A new built-in pattern needs its sample file in EXC_SKIP, or this fails
    ${output}  ${rc} =    Execute Command    api-cli run module/${module_id}/get-configuration | python3 -c 'import json,os,sys; skip=${EXC_SKIP}; keep=${EXC_KEEP}; print(len(json.load(sys.stdin)["default_excludes"]) == len(skip)); [(os.makedirs(os.path.dirname("/root/kopia-ci-exc/" + p), exist_ok=True), open("/root/kopia-ci-exc/" + p, "w").write("x")) for p in skip + keep]'
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}  0
    Should Be Equal As Strings    ${output}    True
    ${obj}  ${rc} =    Execute Command    ${CLIENT} -v /root/kopia-ci-exc:/exc:ro,Z --entrypoint sh ${KOPIA_IMAGE} -c 'kopia snapshot create /exc >/dev/null && kopia snapshot list /exc --json' | python3 -c 'import json,sys; print(json.load(sys.stdin)[-1]["rootEntry"]["obj"])'
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}  0
    ${output}  ${rc} =    Execute Command    ${CLIENT} -v /root/kopia-ci-exc:/exc:ro,Z --entrypoint kopia ${KOPIA_IMAGE} ls -r ${obj} | python3 -c 'import sys; print(sorted(l.strip().split("/", 1)[1] for l in sys.stdin if not l.strip().endswith("/")) == sorted(${EXC_KEEP}))'
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}  0
    Should Be Equal As Strings    ${output}    True
    ${rc} =    Execute Command    api-cli run module/${module_id}/remove-client-folder --data '{"name": "ci@runner", "path": "/exc"}'
    ...    return_rc=True  return_stdout=False
    Should Be Equal As Integers    ${rc}  0
    Execute Command    rm -rf /root/kopia-ci-exc
