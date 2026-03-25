from dataclasses import dataclass
from pathlib import Path

from giellaltgramtools.finaloutput import FinalOutput
from giellaltgramtools.nooutput import NoOutput
from giellaltgramtools.normaloutput import NormalOutput


@dataclass
class CorpusConfig:
    spec: Path = Path()
    variant: str = "default"
    output: NormalOutput | FinalOutput | NoOutput = NormalOutput()
    hide_passes: bool = False
    ignore_typos: bool = False
