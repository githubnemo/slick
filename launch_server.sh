#!/bin/bash

set -e

if [ -z "$LLAMA_CPP_PATH" ]; then
    echo "Set LLAMA_CPP_PATH in the environment."
    exit 1
fi

server_path="${LLAMA_CPP_PATH}/server"
readonly server_path

if ! [ -f "${server_path}" ]; then
    echo "In ${LLAMA_CPP_PATH} there is no 'server' executable."
    exit 1
fi

"${server_path}" \
    -c 4095 \
    -m "${LLAMA_CPP_PATH}/models/mistral/ggml-model-q4_0.gguf"
