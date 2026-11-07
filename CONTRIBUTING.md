# Contributing to REJ

Thank you for helping improve REJ / ¡Gracias por contribuir!

## Getting started

REJ v0.1.0 uses Python 3.11+ and the standard library for normal inspection. Java and Vineflower are only needed for optional decompilation.

```bat
git clone https://github.com/ImIpscanning/rej.git
cd rej
py -3 -m unittest discover -s tests -v
py -3 -m rej inspect examples\HelloPlugin-demo.jar
```

## Pull requests

- Create a focused branch and describe the change and its motivation.
- Add a regression test for new parsers, bug fixes and CLI behavior.
- Make sure your changes do not execute untrusted target JARs.
- Preserve bounded input reading and helpful error reporting.
- Do not include third-party proprietary JARs, credentials or unlicensed source.
- Include expected/actual output and reproduce instructions with bug reports.

Please be respectful and keep security-sensitive disclosures responsible.
