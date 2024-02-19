import logging
import re
from abc import abstractmethod
from concurrent.futures import Future, ProcessPoolExecutor

import awkward as ak
import uproot
from base_class.awkward.zip import NanoAOD
from base_class.dask.delayed import delayed
from base_class.root import Chunk, TreeReader, TreeWriter, merge
from base_class.system.eos import EOS, PathLike
from coffea.processor import ProcessorABC

_PICOAOD = 'picoAOD'
_ROOT = '.root'


class PicoAOD(ProcessorABC):
    def __init__(
        self,
        base_path: PathLike,
        step: int,
        skip_collections: list[str] = None,
        skip_branches: list[str] = None,
    ):
        self._base = EOS(base_path)
        self._step = step
        if skip_collections is None:
            skip_collections = []
        if skip_branches is None:
            skip_branches = []
        skipped = (
            [f'{collection}_.*' for collection in skip_collections] +
            [f'n{collection}' for collection in skip_collections] +
            skip_branches)
        self._filter_branches = re.compile(f'^(?!({"|".join(skipped)})).*$')
        self._transform = NanoAOD(regular=False, jagged=True)

    def _filter(self, branches: set[str]):
        return {*filter(self._filter_branches.match, branches)}

    @abstractmethod
    def select(self, events):
        pass

    def process(self, events):
        selected = self.select(events)
        chunk = Chunk.from_coffea_events(events)
        dataset = events.metadata['dataset']
        result = {dataset: {
            'total_events': len(events),
            'saved_events': int(ak.sum(selected)),
            'source': {
                str(chunk.path): [(chunk.entry_start, chunk.entry_stop)]
            }
        }}
        filename = f'{dataset}/{_PICOAOD}_{chunk.uuid}_{chunk.entry_start}_{chunk.entry_stop}{_ROOT}'
        path = self._base / filename
        with TreeWriter()(path) as writer:
            for i, data in enumerate(TreeReader(self._filter, self._transform).iterate(chunk, step=self._step)):
                writer.extend(data[selected[i*self._step:(i+1)*self._step]])
        result[dataset]['files'] = [writer.tree]

        return result

    def postprocess(self, accumulator):
        pass


@delayed
def _fetch_metadata(dataset: str, path: PathLike, dask: bool = False):
    with uproot.open(path) as f:
        if 'genEventCount' in f['Runs'].keys():
            data = f['Runs'].arrays(
                ['genEventCount', 'genEventSumw', 'genEventSumw2'])
            return {
                dataset: {
                    'count': float(ak.sum(data['genEventCount'])),
                    'sumw': float(ak.sum(data['genEventSumw'])),
                    'sumw2': float(ak.sum(data['genEventSumw2'])),
                }
            }
        else:
            data = f['Events'].arrays(['event'])
            return {
                dataset: {
                    'count' : float(ak.num(data['event'], axis=0))
                }
            }


def fetch_metadata(
        fileset: dict[str, dict[str, list[str]]],
        n_process: int = None,
        dask: bool = True) -> list[dict[str, dict[str]]]:
    if not dask:
        with ProcessPoolExecutor(max_workers=n_process) as executor:
            tasks: list[Future] = []
            for dataset, files in fileset.items():
                for file in files['files']:
                    tasks.append(executor.submit(
                        _fetch_metadata, dataset, file, dask=dask))
            results = [task.result() for task in tasks]
    else:
        results = []
        for dataset, files in fileset.items():
            for file in files['files']:
                results.append(_fetch_metadata(dataset, file, dask=dask))
    return results


def integrity_check(
    fileset: dict[str, dict[str, list[str]]],
    output: dict[str, dict[str, dict[str, list[tuple[int, int]]]]],
    num_entries: dict[str, dict[str, int]] = None,
):
    logging.info('Checking integrity of the picoAOD...')
    diff = set(fileset) - set(output)
    miss_dict = {}
    if diff:
        logging.error(f'The whole dataset is missing: {diff}')
        miss_dict["dataset_missing"] = "Run again :P"
    for dataset in fileset:
        inputs = map(EOS, fileset[dataset]['files'])
        outputs = {EOS(k): v for k, v in output[dataset]['source'].items()}
        ns = None if num_entries is None else {
            EOS(k): v for k, v in num_entries[dataset].items()}
        file_missing = []
        chunk_missing = []
        for file in inputs:
            if file not in outputs:
                logging.error(f'The whole file is missing: "{file}"')
                file_missing.append( str(file) )
            else:
                chunks = sorted(outputs[file], key=lambda x: x[0])
                if ns is not None:
                    chunks.append((ns[file], ns[file]))
                merged = []
                start, stop = 0, 0
                for _start, _stop in chunks:
                    if _start != stop:
                        if start != stop:
                            merged.append([str(start), str(stop)])
                        start = _start
                        logging.error(
                            f'Missing chunk: [{stop}, {_start}) in "{file}"')
                        chuck_missing.append( f'[{stop}, {_start}) in "{file}"' )
                    stop = _stop
                if start != stop:
                    merged.append([start, stop])
        if file_missing: miss_dict["file_missing"] = file_missing
        if chunk_missing: miss_dict["chunk_missing"] = chunk_missing
    output[dataset].pop('source')
    output[dataset]['missing'] = miss_dict
    return output


def resize(
    base_path: PathLike,
    output: dict[str, dict[str, list[Chunk]]],
    step: int,
    chunk_size: int
):
    base = EOS(base_path)
    transform = NanoAOD(regular=False, jagged=True)
    for dataset, chunks in output.items():
        output[dataset]['files'] = merge.resize(
            base / dataset/f'{_PICOAOD}{_ROOT}',
            *chunks['files'],
            step=step,
            chunk_size=chunk_size,
            reader_options={'transform': transform},
            dask=True,
        )
    return output
