from dataclasses import dataclass
from pathlib import Path

from giellaltgramtools.finaloutput import FinalOutput
from giellaltgramtools.nooutput import NoOutput
from giellaltgramtools.normaloutput import NormalOutput


@dataclass
class YamlConfig:
    output: NormalOutput|FinalOutput|NoOutput
    hide_passes: bool
    move_tests: bool
    spec: Path
    variant: str
    tests: list[str]
    test_file: Path
    use_runtime: bool