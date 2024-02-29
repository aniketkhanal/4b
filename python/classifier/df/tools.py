from __future__ import annotations

from typing import TYPE_CHECKING

from ..config.setting.df import Columns
from ..config.state.label import MultiClass

if TYPE_CHECKING:
    import pandas as pd


class add_label_index:
    def __init__(self, label: str):
        MultiClass.add(label)
        self.label = label

    def __call__(self, df: pd.DataFrame) -> pd.DataFrame:
        import numpy as np

        df.loc[:, (Columns.label_index,)] = np.dtype(
            Columns.index_dtype).type(MultiClass.index(self.label))
        return df


class add_label_flag:
    def __init__(self, *labels: str):
        MultiClass.add(*labels)
        self.labels = {*labels}

    def __call__(self, df: pd.DataFrame) -> pd.DataFrame:
        for label in MultiClass.labels:
            df.loc[:, (label,)] = label in self.labels
        return df


class add_event_offset:
    """
    a workaround for no ``uint64`` in torch.Tensor
    """

    def __init__(self, kfold: int):
        self.kfold = kfold

    def __call__(self, df: pd.DataFrame) -> pd.DataFrame:
        df.loc[:, (Columns.event_offset,)] = (
            df[Columns.event] % self.kfold).astype(Columns.index_dtype)
        return df


class add_region_index:
    def __init__(self, *args: str, **kwargs: int):
        self.regions = dict(zip(args, range(len(args))))
        self.regions.update(kwargs)

    def __call__(self, df: pd.DataFrame) -> pd.DataFrame:
        df.loc[:, (Columns.region_index,)] = (
            df.loc[:, [*self.regions]]
            .mul(self.regions)
            .sum(axis=1)
            .astype(Columns.index_dtype)
        )
        return df


class drop_columns:
    def __init__(self, *columns: str):
        self.columns = [*columns]

    def __call__(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.drop(columns=self.columns)


def normalize_weight(df: pd.DataFrame) -> pd.DataFrame:
    df.loc[:, (Columns.weight_normalized,)] = (
        df[Columns.weight] / df[Columns.weight].sum())
    return df
