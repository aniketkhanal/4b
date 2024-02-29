from __future__ import annotations

import logging
from datetime import datetime
from functools import cached_property
from itertools import chain
from typing import TYPE_CHECKING

from base_class.utils import unique
from classifier.task import ArgParser, EntryPoint, Main, converter

if TYPE_CHECKING:
    from classifier.task.dataset import Dataset, TrainingSetLoader


class SetupMultiprocessing(Main):
    argparser = ArgParser()
    argparser.add_argument(
        '--preload', action='extend', nargs='+', default=['torch'], help='preloaded imports when using multiprocessing')

    @cached_property
    def mp_context(self):
        from classifier import process

        return process.get_context(method='forkserver', library='torch', preload=unique(self.opts.preload))

    @cached_property
    def mp_initializer(self):
        from classifier.process.initializer import (
            DefaultInitializer, inherit_context_initializer,
            torch_set_sharing_strategy)

        initializer = DefaultInitializer(
            torch_set_sharing_strategy('file_system'))
        initializer.add(inherit_context_initializer(
            self.mp_context, initializer))
        return initializer


class SelectDevice(Main):
    argparser = ArgParser()
    argparser.add_argument(
        '--device', nargs='+', default=['cuda'], help='the [green]torch.device[/green] used for training')

    @cached_property
    def device(self):
        from classifier.process.device import Device
        return Device(*self.opts.device)


class _load_datasets:
    def __call__(self, loader: TrainingSetLoader):
        return loader()


class LoadTrainingSets(SetupMultiprocessing):
    _workflow = [
        ('main', 'call [blue]dataset.train()[/blue]'),
        ('sub', 'load [blue]dataset[/blue]'),
    ]
    argparser = ArgParser()
    argparser.add_argument(
        '--max-loaders', type=converter.int_pos, default=1, help='the maximum number of datasets to load in parallel')

    def load_training_sets(self, parser: EntryPoint):
        from concurrent.futures import ProcessPoolExecutor as Pool

        from torch.utils.data import ConcatDataset, StackDataset

        # load datasets in parallel
        d_mods: list[Dataset] = parser.mods['dataset']
        d_loaders = [*chain(*(k.train() for k in d_mods))]
        if len(d_loaders) == 0:
            raise ValueError('No dataset to load')
        timer = datetime.now()
        with Pool(
            max_workers=self.opts.max_loaders,
            mp_context=self.mp_context,
            initializer=self.mp_initializer
        ) as pool:
            datasets = [*pool.map(_load_datasets(), d_loaders)]
        logging.info(
            f'Loaded {len(d_loaders)} datasets in {datetime.now() - timer}')
        # concatenate datasets
        d_keys = [set(d.keys()) for d in datasets]
        kept = set.intersection(*d_keys)
        ignored = set.union(*d_keys) - kept
        kept = sorted(kept)
        logging.info(
            f'The following keys will be kept: {kept}')
        if ignored:
            logging.warn(
                f'The following keys will be ignored: {sorted(ignored)}')
        datasets = {k: ConcatDataset(d[k] for d in datasets) for k in kept}
        logging.info(
            f'Loaded {len(next(iter(datasets.values())))} data entries')
        return StackDataset(**datasets)
