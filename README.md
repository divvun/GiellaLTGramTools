# GiellaLTGramTools

This repo contains scripts that makes the GiellaLT gramchecker .zcheck file and runs tests.

Install these tools by running `pipx install https://github.com/giellalt/GiellaLTGramTools`

## Runtime dependency

The test scripts depend on `divvun-checker` which is part of `libdivvun`

For Macs, run
[install-nightly.sh](https://giellalt.github.io/infra/GettingStartedOnTheMac.html#installing-hfst-our-linguistic-compiler)
On Linux, enable the
[nightly Apertium repos](https://wiki.apertium.org/wiki/Install_Apertium_core_using_packaging),
then `<your-package-manager> install libdivvun`
