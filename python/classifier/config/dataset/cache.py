import argparse
import logging

from classifier.task import ArgParser, Dataset, parsers


class Torch(Dataset):
    argparser = ArgParser()
    argparser.add_argument(
        '--input', default=argparse.SUPPRESS, required=True, help='the input directory')
    argparser.add_argument(
        '--chunk', action='extend', nargs='+', default=[], help='if given, only load the selected chunks e.g. [yellow]--chunks 0-3 5[/yellow]')

    def train(self):
        import json
        import math

        import fsspec
        from base_class.system.eos import EOS

        base = EOS(self.opts.input)
        with fsspec.open(base/'cache.json') as f:
            metadata = json.load(f)
        total = math.ceil(metadata['size']/metadata['chunksize'])
        if self.opts.chunk:
            chunks = parsers.parse_intervals(self.opts.chunk, total)
        else:
            chunks = list(range(total))
        if len(chunks) == 0:
            logging.warning('No chunk to load')
        else:
            count = len(chunks) * metadata['chunksize']
            if chunks[-1] == total - 1:
                count -= (total * metadata['chunksize'] - metadata['size'])
            logging.info(
                f'Loading {count}/{metadata["size"]} entries from {len(chunks)}/{total} cached chunks (shuffle={metadata["shuffle"]}, compression={metadata["compression"]})')
        return [_read_torch_load(str(base/f'chunk{i}.pt'), metadata['compression']) for i in chunks]


class _read_torch_load:
    def __init__(self, path: str, compression: str):
        self.path = path
        self.compression = compression

    def __call__(self):
        import fsspec
        import torch

        with fsspec.open(self.path, 'rb', compression=self.compression) as f:
            return torch.load(f)
