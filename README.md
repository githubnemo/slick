# slick LLM CLI

This is a tiny tool to provide a handy CLI tool that combines the versatility
of large language models with your typical UNIX shell.

Give `slick` a command and an input on `stdin` and it will (hopefully)
do what you want!

Some examples:

```bash
cat foo.csv | slick 'convert the following CSV into JSON: """{stdin}"""'
```

```bash
echo "esta es una oración
this is a sentence
dies ist ein satz" | slick 'tell the language of the following sentence: {stdin_line}. one word!'
```

If you use vim you can use it to augment your code with whatever you need,
code completion, summarization, whatever the LLM is capable of.

https://github.com/githubnemo/slick/assets/264196/118d8e88-7751-4ceb-b3f4-ddc00705c1c1

# Installation

Run

    poetry install

Then, assuming you `~/bin` folder is in your path, run:

    ln -s `poetry run which slick` ~/bin/slick

You will need a working `llama.cpp` folder with mistral-7b-instruct and a
server binary.  This is very rough for now. See the
[`launch_server.sh`](./launch_server.sh) script for details.
