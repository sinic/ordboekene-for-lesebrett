#!/usr/bin/env python3
# Copyright (C) 2026 Simon Nicolussi

import argparse
import json
import sys

from pyglossary.glossary_v2 import Glossary

Glossary.init()


def extract(var, key):
    if isinstance(var, dict):
        for k, v in var.items():
            if k == key and v:
                yield v
            if isinstance(v, (dict, list)):
                yield from extract(v, key)
    elif isinstance(var, list):
        for d in var:
            yield from extract(d, key)


def words(lemmas):
    headwords, variants = set(), set()
    for lemma in lemmas:
        headwords.add(lemma["lemma"])
        variants |= set(extract(lemma, "word_form"))
    result = [", ".join(sorted(headwords))]
    for variant in sorted(variants):
        if variant != result[0]:
            result.append(variant)
    return result


class Dictionary:
    def __init__(self, title, articles, concepts, headings):
        self.title = title
        with open(articles) as file:
            self.articles = json.load(file)
        with open(concepts) as file:
            self.concepts = json.load(file)["concepts"]
        self.headings = headings

    def generate_glossary(self):
        glossary = Glossary()
        glossary.setInfo("title", self.title)
        glossary.setInfo("author", "Språkrådet og Universitetet i Bergen")
        glossary.setInfo("copyright", "CC BY 4.0")
        glossary.setDefaultDefiFormat("h")
        for article in self.articles.values():
            if lemmas := article["lemmas"]:
                entry = f"[{self.generate_tags(lemmas)}]"
                entry += self.generate_etymology_section(article["body"])
                entry += self.generate_definition_section(article["body"])
                glossary.addEntry(glossary.newEntry(words(lemmas), entry))
        return glossary

    def generate_tags(self, lemmas):
        tags = set()
        for lemma in lemmas:
            for paradigm in lemma["paradigm_info"]:
                tags.add(", ".join(sorted(set(paradigm["tags"]))))
        return "; ".join(sorted(tags))

    def generate_etymology_section(self, body):
        if "etymology" in body:
            etymologies = "; ".join(
                self.instantiate(etymology) for etymology in body["etymology"]
            )
            return f"<h4>{self.headings['etymology']}</h4>{etymologies}"
        return ""

    def generate_definition_section(self, body):
        if "definitions" in body:
            subs = []
            definitions = "; ".join(
                self.parse_definition(definition, subs)
                for definition in body["definitions"]
            )
            result = f"<h4>{self.headings['definitions']}</h4>{definitions}"
            if subs := sorted(subs):  # v. BM 60685 'til'
                result += f"<h4>{self.headings['expressions']}</h4>"
                result += f"<dl>{''.join(subs)}</dl>"
            return result
        return ""

    def parse_definition(self, definition, subs):
        parsed = []
        nested = False
        for element in definition.get("elements", []):
            if new := self.parse_element(element, subs):
                if element["type_"] == "definition":
                    if element.get("sub_definition", False):
                        new = f"<ul><li>{new}</li></ul>"
                    else:
                        nested = True
                parsed.append(new)
        if nested:
            return f"<ol>{''.join(f'<li>{e}</li>' for e in parsed)}</ol>"
        return "<br/>".join(parsed)

    def parse_element(self, element, subs):
        match element["type_"]:
            case "definition":
                return self.parse_definition(element, subs)
            case "explanation":
                return f"{self.instantiate(element)}"
            case "example":
                return f"<i>{self.instantiate(element['quote'])}</i>"
            case "compound_list":
                if "elements" in element:  # cf. NN 49676 'mikro-'
                    compounds = ", ".join(
                        self.parse_item(item) for item in element["elements"]
                    )
                    return f"{self.instantiate(element['intro'])} {compounds}"
            case "sub_article":
                title = ", ".join(element["lemmas"])
                body = "; ".join(
                    self.parse_definition(definition, subs)
                    for definition in element["article"]["body"]["definitions"]
                )
                subs.append(f"<dt><b>{title}</b></dt><dd>{body}<dd>")
            case _:
                print("unknown element:", element, file=sys.stderr)

    def parse_item(self, item):
        match item["type_"]:
            case "fraction":  # incl. time signatures!
                return f"{item['numerator']}/{item['denominator']}"
            case "subscript" | "superscript":
                tag = item["type_"][:3]
                return f"<{tag}>{item['text']}</{tag}>"
            case "usage":
                return f"<i>{item['text']}</i>"
            case "article_ref":
                link = item.get("word_form", item["lemmas"][0]["lemma"])
                return f"<a>{link}</a>"  # no ref
            case "quote_inset":
                return self.instantiate(item)
            case _:
                return self.concepts[item["id"]]["expansion"]

    def instantiate(self, var):
        trans = str.maketrans({"{": "{{", "}": "}}", "$": "{}"})
        fstr = var.get("content", "").translate(trans)
        args = list(self.parse_item(item) for item in var.get("items", []))
        return fstr.format(*args)


parser = argparse.ArgumentParser(description="Generate Norwegian dictionaries")
parser.add_argument("-a", "--articles", default="articles.json", metavar="JSON_FILE")
parser.add_argument("-c", "--concepts", default="concepts.json", metavar="JSON_FILE")
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("-s", "--stardict", metavar="OUTPUT_FILE")
group.add_argument("-k", "--kobo", metavar="OUTPUT_FILE")
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("-b", "--bokmaal", action="store_true")
group.add_argument("-n", "--nynorsk", action="store_true")
args = parser.parse_args()

headings = dict(
    etymology="Opphav",
    definitions="Betydning og bruk",
    expressions="Faste uttrykk",
)
if args.bokmaal:
    dictionary = Dictionary("Bokmålsordboka", args.articles, args.concepts, headings)
else:
    headings["definitions"] = "Tyding og bruk"
    dictionary = Dictionary("Nynorskordboka", args.articles, args.concepts, headings)
glossary = dictionary.generate_glossary()
print(f"{len(glossary)} entries in total")
if args.stardict:
    glossary.write(args.stardict, formatName="Stardict")
if args.kobo:
    glossary.write(args.kobo, formatName="Kobo")
