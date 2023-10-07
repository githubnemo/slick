#!/usr/bin/env python
import argparse
import sys

from transformers import AutoTokenizer, AutoModelForCausalLM
from transformers import T5Tokenizer, T5ForConditionalGeneration


def load_model(name='t5'):
    if name == 't5':
        model_version = 'large'
        tokenizer = T5Tokenizer.from_pretrained(f"t5-{model_version}")
        model = T5ForConditionalGeneration.from_pretrained(f"google/flan-t5-{model_version}")
    else:
        tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-Instruct-v0.1")
        model = AutoModelForCausalLM.from_pretrained("mistralai/Mistral-7B-Instruct-v0.1", dtype='bf16')
        prompt = args.prompt
        device = "cpu"
        model.to(device)
    return tokenizer, model


def generate(prompt, **kwargs):
    input_ids = tokenizer(prefix + sentence, return_tensors="pt").input_ids
    return model.generate(input_ids, max_length=max_target_length, do_sample=False, num_beams=10)


def debug(msg):
    print(msg, file=sys.stderr)


parser = argparse.ArgumentParser()
parser.add_argument('prompt')
parser.add_argument('--max-length', type=int, default=500)
parser.add_argument('--model', type=str, default='t5')

args = parser.parse_args()
prompt = args.prompt
line_wise = False

if '{stdin}' in prompt:
    prompt = prompt.format(stdin=''.join(sys.stdin.readlines()))
elif '{stdin_line}' in prompt:
    stdin_lines = [n.strip() for n in sys.stdin.readlines()]
    line_wise = True

if args.model == 'mistral':
    prompt = "[INST]{prompt}[/INST]"

tokenizer, model = load_model(args.model)

debug("loaded model")


def generate(prompt, **kwargs):
    debug(f'generating for "{prompt}"')
    input_ids = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(**input_ids, **kwargs)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

if line_wise:
    for line in stdin_lines:
        print(generate(
            prompt.format(stdin_line=line),
            max_new_tokens=args.max_length,
            do_sample=False,
            repetition_penalty=4.0,
        ))

else:
    print(generate(
        prompt,
        max_length=args.max_length,
        do_sample=False,
        num_beams=10,
    ))
