from typing import List, Optional, TypeVar

import toml
from pydantic import BaseModel


class PartialConfig(BaseModel):
    download_path: Optional[str] = None
    verbose: Optional[int] = None
    speedup: Optional[float] = None


class BaseConfig(BaseModel):
    download_path: str
    verbose: int
    speedup: float


class TomlConfig(BaseModel):
    default: PartialConfig
    series: dict[str, PartialConfig]


_system_defaults = BaseConfig(download_path=".", verbose=0, speedup=1)


class Config:
    cmd_line: PartialConfig
    toml_config = TomlConfig

    def __init__(self, cmd_line: PartialConfig, path: str | None):
        self.cmd_line = cmd_line

        if path is None:
            self.toml_config = TomlConfig(
                default=PartialConfig(download_path=".", verbose=0, speedup=1),
                series={},
            )
            return

        config_data = toml.load(path)
        self.toml_config = TomlConfig.model_validate(config_data)

    def for_series(self, series_title: str | None) -> BaseConfig:
        series_overrides = {}
        if series_title is not None and series_title in self.toml_config.series:
            series_overrides = self.toml_config.series[series_title].model_dump()

        # merge in priority order,
        # 1. cmd line options
        # 2. series specific options
        # 3. default options
        # if there are duplicates, the first one wins
        dicts = [
            self.cmd_line.model_dump(),
            series_overrides,
            self.toml_config.default.model_dump(),
            _system_defaults.model_dump(),
        ]
        return BaseConfig(
            download_path=_get_first_key("download_path", dicts),
            verbose=_get_first_key("verbose", dicts),
            speedup=_get_first_key("speedup", dicts),
        )


T = TypeVar("T")


def _get_first_key(key: str, dicts: List[dict[str, T]]) -> T:
    for d in dicts:
        if key in d and d[key] is not None:
            return d[key]
    raise KeyError(f"Key {key} not found in any of the dicts")
