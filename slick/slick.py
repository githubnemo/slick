#!/usr/bin/env python
import argparse
import asyncio
import json
import os
import sys

from urllib.parse import urljoin

import aiohttp


class RemoteModel:
    def build_generate_request_data(self, prompt, **kwargs):
        ...

    async def request_generate(self, prompt, **kwargs):
        ...


class LlamaCppRemoteModel(RemoteModel):
    def __init__(self, url):
        self.url = url

    def build_generate_request_data(
        self,
        prompt,
        n_predict,
        temperature=0.2,
        top_k=40,
        top_p=0.9,
        stop="<|end_of_text|>",
        stream=False,
    ):
        return dict(
            messages=[{'role': 'user', 'content': prompt}],
            temperature=temperature,
            top_k=top_k,
            top_p=top_p,
            stop=stop,
            stream=stream,
        )

    async def _post(self, url, data, do_stream):
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as resp:
                if do_stream:
                    async for line in resp.content:
                        if line == b'\n':
                            continue
                        yield str(line, encoding='utf8')
                else:
                    yield await resp.text()

    async def request_generate(self, prompt, do_stream=False, **kwargs):
        data = self.build_generate_request_data(
            prompt,
            stream=do_stream,
            **kwargs
        )

        partial_result = {}

        async for chunk in self._post(
            url=urljoin(self.url, '/chat/completions'),
            data=data,
            do_stream=do_stream,
        ):
            if chunk == 'data: [DONE]\n':
                yield partial_result
            elif chunk.startswith('data: '):
                chunk = json.loads(chunk[6:])
                for choice in chunk['choices']:
                    for key in choice['delta']:
                        if key in partial_result and partial_result[key] is not None:
                            partial_result[key] += choice['delta'][key]
                        else:
                            partial_result[key] = choice['delta'][key]



async def generate(remote, prompt, **kwargs):
    async for foo in remote.request_generate(prompt, **kwargs):
        yield foo


def debug(msg):
    print(msg, file=sys.stderr)


def model_format_prompt(prompt):
    return prompt  # let server handle prompt tokens


async def main(args):
    prompt = args.prompt
    remote = LlamaCppRemoteModel(url=args.server_address)

    # modes of operation:
    #
    # - block: pass in stdin fully as one block of text, generate one output
    # - line: pass one line of stdin, generate one output, no state
    # - stream: pass one line of stdin, generate one output, stateful
    #
    # TODO: streaming is not implemented yet as this would be infficient with
    # the standard llama.cpp server. Ideally the server would implement a
    # sliding window approach. Then we could feed the input line-by-line,
    # generate output and repeat with a new line.
    #
    # streaming is, i think, only useful when input and output can be
    # intermixed to record the current state to set off of given the next
    # input.

    line_wise = False
    stateful = False

    if "{stdin}" in prompt:
        prompt = prompt.format(stdin="".join(sys.stdin.readlines()))
    elif "{stdin_line}" in prompt:
        stdin_lines = [n.strip() for n in sys.stdin.readlines()]
        line_wise = True
        stateful = False
    elif "{stdin_stream}" in prompt:
        stdin_lines = [n.strip() for n in sys.stdin.readlines()]
        line_wise = True
        stateful = False

    if line_wise:
        # TODO this case might benefit from batched processing
        for line in stdin_lines:
            prompt = model_format_prompt(prompt)
            part = None

            async for part in generate(
                remote=remote,
                prompt=prompt.format(stdin_line=line),
                n_predict=args.max_length,
                do_stream=args.do_stream,
            ):
                part = part['content']
                print(part, end='')

            if part is not None:
                if not part.endswith('\n'):
                    print()
                print('\0', end='')

    else:
        prompt = model_format_prompt(prompt)
        part = None
        async for part in generate(
                remote=remote,
                prompt=prompt,
                n_predict=args.max_length,
                do_stream=args.do_stream,
        ):
            part = part['content']
            print(part, end='')

        if part is not None:
            if not part.endswith('\n'):
                print()
            print('\0', end='')


def get_address_from_env():
    return os.environ.get("SLICK_SERVER_ADDRESS",  "http://127.0.0.1:8080")


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt")
    parser.add_argument("--max-length", type=int, default=500)

    # make it possible to stream the data - this might be useful when piping
    # long data
    parser.add_argument("--do-stream", dest='do_stream', action="store_true", default=True)
    parser.add_argument("--dont-stream", dest='do_stream', action="store_false")

    # use protocol as well if someone wants to outsource their server and
    # serve via https instead of tunneling
    parser.add_argument("--server-address", type=str,
                        default=get_address_from_env())

    args = parser.parse_args()

    asyncio.run(main(args))


if __name__ == "__main__":
    cli()
