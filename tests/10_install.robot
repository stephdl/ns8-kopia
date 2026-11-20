*** Settings ***
Library    SSHLibrary
Resource    kopia.resource

*** Test Cases ***
Check if kopia is installed correctly
    ${output}  ${rc} =    Execute Command    add-module ${IMAGE_URL} 1
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}  0
    &{output} =    Evaluate    ${output}
    Set Global Variable    ${module_id}    ${output.module_id}

Check if kopia can be configured
    ${rc} =    Execute Command    api-cli run module/${module_id}/configure-module --data '{"host": "kopia.test.example.org", "admin_password": "Admin-pass-2026"}'
    ...    return_rc=True  return_stdout=False
    Should Be Equal As Integers    ${rc}  0

Check if kopia works as expected
    ${rc} =    Execute Command    curl -sk -o /dev/null -w '\%{http_code}' https://127.0.0.1:51515/ | grep -q 401
    ...    return_rc=True  return_stdout=False
    Should Be Equal As Integers    ${rc}  0
