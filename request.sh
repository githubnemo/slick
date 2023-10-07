#!/bin/sh

set -eu

api_url="http://127.0.0.1:8080"
readonly api_url

prompt="$1"
readonly prompt

n_keep=100
readonly n_keep

request="$(echo -n "$prompt" | jq -Rs --argjson n_keep $n_keep '{
	prompt: .,
	temperature: 0.2,
	top_k: 40,
	top_p: 0.9,
	n_keep: $n_keep,
	n_predict: 1024,
	stop: ["[INST]"],
	stream: true
}')"
readonly request

echo $request
curl \
        --silent \
        --no-buffer \
        --request POST \
        --url "${api_url}/completion" \
        --header "Content-Type: application/json" \
        --data-raw "${request}"

