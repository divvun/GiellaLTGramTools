from dataclasses import dataclass, field
from pathlib import Path

from giellaltgramtools.finaloutput import FinalOutput
from giellaltgramtools.nooutput import NoOutput
from giellaltgramtools.normaloutput import NormalOutput


@dataclass
class YamlConfig:
    spec: Path = Path()
    variant: str = "default"
    output: NormalOutput|FinalOutput|NoOutput = NormalOutput()
    hide_passes: bool = False
    move_tests: bool = False
    tests: list[str] = field(default_factory=list)
    test_file: Path = Path()
    use_runtime: bool = False