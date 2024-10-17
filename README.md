# GiellaLTGramTools

This repo contains scripts that creates the GiellaLT gramchecker .zcheck file and runs tests.

Install these tools by running `pipx install -f git+https://github.com/divvun/GiellaLTGramTools`

## Runtime dependency

The test scripts depend on `divvun-checker` which is part of `libdivvun`

For Macs, run
[install-nightly.sh](https://giellalt.github.io/infra/GettingStartedOnTheMac.html#installing-hfst-our-linguistic-compiler)
On Linux, enable the
[nightly Apertium repos](https://wiki.apertium.org/wiki/Install_Apertium_core_using_packaging),
then `<your-package-manager> install libdivvun`

## Test usage

Test options: `gtgramtool test --help`

```text
Usage: gtgramtool test [OPTIONS] COMMAND [ARGS]...

Test the grammars.

Options:
-c, --colour        Colours the output
-s, --spec PATH     Path to the .zcheck or pipespec.xml spec file. Necessary
                    argument for the  xml command, useful for the yaml
                    command when doing out of tree builds.
-V, --variant TEXT  Which variant should be used.
--help              Show this message and exit.

Commands:
xml   Test XML files.
yaml  Test a YAML file.
```

### Check yaml files

- With colors: `gtgramtool test -c yaml <yaml-file>`
- Without colors: `gtgramtool test yaml <yaml-file>`

### Check xml files

xml options: `gtgramtool test xml --help`

```text
Usage: gtgramtool test xml [OPTIONS] [TARGETS]...

  Test XML files.

Options:
  -t, --count_typos  Also count typos as errors
  --help             Show this message and exit.
```

#### Example for South Sámi

- With colors, use pipespec, release variant, ignore typos: `gtgramtool test -c -s $GTLANGS/lang-sma/tools/grammarcheckers/pipespec.xml -V smagram-release xml $GTLANGS/corpus-sma/goldstandard/converted $GTLANGS/corpus-sma-x-closed/goldstandard/converted`
- With colors, use .zcheck-file, development variant, count typos: `gtgramtool test -c -s $GTLANGS/lang-sma/tools/grammarcheckers/sma.zcheck -V smagram xml -t $GTLANGS/corpus-sma/goldstandard/converted $GTLANGS/corpus-sma-x-closed/goldstandard/converted`

For other languages, exchange `sma` for your language

The environment variable `GTLANGS` points to the directory where [giellalt repositories](https://github.com/giellalt) have been cloned. On the writers system it is specified like this:

```sh
export GTLANGS="$HOME/repos/giellalt"
```

Exchange `repos/giellalt` with your path to the giellalt directory on your system.
