*** Variables ***
${KOPIA_IMAGE}    docker.io/kopia/kopia:0.23.1
# The node is its own client: a kopia container with the home of the enrolled machine
${CLIENT}    podman run --rm --network=host --add-host kopia.test.example.org:127.0.0.1 -e HOME=/home/u -e KOPIA_CONFIG_PATH=/home/u/.config/kopia/repository.config -e KOPIA_PERSIST_CREDENTIALS_ON_CONNECT=true -v /root/kopia-ci-home:/home/u:Z
