*** Settings ***
Library    SSHLibrary
Resource    kopia.resource

*** Test Cases ***
Check if a password reset disconnects the machine
    ${rc} =    Execute Command    api-cli run module/${module_id}/reset-client-password --data '{"name": "ci@runner"}' >/dev/null
    ...    return_rc=True  return_stdout=False
    Should Be Equal As Integers    ${rc}  0
    ${output}  ${rc} =    Execute Command    ${CLIENT} --entrypoint sh ${KOPIA_IMAGE} -c 'kopia snapshot create /home/u'
    ...    return_rc=True    return_stderr=True    return_stdout=False
    Should Not Be Equal As Integers    ${rc}  0
    Execute Command    rm -rf /root/kopia-ci-home /root/kopia-ci.sh

Check if the enrollment output is sealed for the key of a browser
    # The Python of the core plays the browser: it sends an RSA key and opens the sealed output
    ${output}  ${rc} =    Execute Command    /usr/local/agent/pyenv/bin/python3 -c 'import base64 as b, json, subprocess; from cryptography.hazmat.primitives import hashes, serialization as s; from cryptography.hazmat.primitives.asymmetric import padding, rsa; from cryptography.hazmat.primitives.ciphers.aead import AESGCM; k = rsa.generate_private_key(65537, 2048); pub = b.b64encode(k.public_key().public_bytes(s.Encoding.DER, s.PublicFormat.SubjectPublicKeyInfo)).decode(); out = subprocess.run(["api-cli", "run", "module/${module_id}/reset-client-password", "--data", json.dumps({"name": "ci@runner", "public_key": pub})], check=True, capture_output=True, text=True).stdout; assert "KOPIA_PASSWORD" not in out; e = json.loads(out)["sealed"]; aes = k.decrypt(b.b64decode(e["key"]), padding.OAEP(padding.MGF1(hashes.SHA256()), hashes.SHA256(), None)); print(len(json.loads(AESGCM(aes).decrypt(b.b64decode(e["iv"]), b.b64decode(e["data"]), None))["password"]))'
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}  0
    Should Be Equal As Strings    ${output}    24

Check if a bad browser key is refused
    ${rc} =    Execute Command    api-cli run module/${module_id}/reset-client-password --data '{"name": "ci@runner", "public_key": "bm90IGEga2V5"}'
    ...    return_rc=True  return_stdout=False
    Should Not Be Equal As Integers    ${rc}  0
