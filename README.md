# Ordbøkene for lesebrett

Norwegian is unfortunately not among the languages
that Kobo provides morphological dictionaries for
(i.e., dictionaries where you can tap on *drukket*
and be shown the entry for the verb *å drikke*).

Thankfully,
[Språkrådet](https://sprakradet.no/)
and [Universitetet i Bergen](https://www4.uib.no/)
publish
their excellent [Ordbøkene](https://ordbokene.no/)
also as [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) licensed
(if underdocumented)
[JSON dumps](https://ord.uib.no/ord_1_Ordlister.html).

The Python script in this repository parses those,
feeds them to [PyGlossary](https://github.com/ilius/pyglossary),
and produces offline dictionaries (for Bokmål and for Nynorsk!)
usable both on [KOReader](https://koreader.rocks/)
and on Kobo's proprietary stock reader,
with support for other formats easily added.