*** Settings ***
Library    SSHLibrary
Resource    kopia.resource

*** Variables ***
${SCENARIO}    install

*** Test Cases ***
Check if kopia is installed correctly
    # The update scenario starts from the release published in the stephdl forge,
    # and 12_update moves it to the image under test
    IF    '${SCENARIO}' == 'update'
        ${rc} =    Execute Command    api-cli run add-repository --data '{"name":"stephdl","url":"https://forge.de-labrusse.fr/ns8/updates/","status":true}'
        ...    return_rc=True  return_stdout=False
        Should Be Equal As Integers    ${rc}  0
        ${image} =    Set Variable    kopia
    ELSE
        ${image} =    Set Variable    ${IMAGE_URL}
    END
    ${output}  ${rc} =    Execute Command    add-module ${image} 1
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
