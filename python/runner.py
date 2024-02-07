import pickle
import os
import time
import gc
import argparse
import sys
import numpy as np
import uproot
import yaml
import dask
dask.config.set({'logging.distributed': 'error'})

uproot.open.defaults["xrootd_handler"] = uproot.source.xrootd.MultithreadedXRootDSource
from coffea.nanoevents import NanoEventsFactory, NanoAODSchema, BaseSchema
NanoAODSchema.warn_missing_crossrefs = False
import warnings
warnings.filterwarnings("ignore")
from coffea import processor
from coffea.util import save
import cachetools
import importlib
import logging
from functools import partial
from multiprocessing import Pool

from datetime import datetime

from base_class.addhash import get_git_revision_hash, get_git_diff
from base_class.dataset_tools import rucio_utils  ### can be modified when move to coffea2023
from skimmer.processor.picoaod import fetch_metadata, resize

def list_of_files( ifile, allowlist_sites=['T3_US_FNALLPC'], test=False, test_files=5 ):
    '''Check if ifile is root file or dataset to check in rucio'''

    if isinstance(ifile, list):
        return ifile
    elif ifile.endswith('.txt'):
        file_list = [f'root://cmseos.fnal.gov/{jfile.rstrip()}' for jfile in open(ifile).readlines() ]
        return file_list
    else:
        rucio_client = rucio_utils.get_rucio_client()
        outfiles, outsite, sites_counts = rucio_utils.get_dataset_files_replicas( ifile, client=rucio_client, mode="first", allowlist_sites=allowlist_sites )
        return outfiles[:(test_files if test else -1)]


if __name__ == '__main__':

    #
    # input parameters
    #
    parser = argparse.ArgumentParser(description='Run coffea processor', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-t', '--test', dest="test", action="store_true", default=False, help='Run as a test with few files')
    parser.add_argument('-o', '--output', dest="output_file", default="hists.coffea", help='Output file.')
    parser.add_argument('-p', '--processor', dest="processor", default="analysis/processors/processor_HH4b.py", help='Processor file.')
    parser.add_argument('-c', '--configs', dest="configs", default="analysis/metadata/HH4b.yml", help='Config file.')
    parser.add_argument('-m', '--metadata', dest="metadata", default="metadata/datasets_HH4b.yml", help='Metadata datasets file.')
    parser.add_argument('-op', '--outputPath', dest="output_path", default="hists/", help='Output path, if you want to save file somewhere else.')
    parser.add_argument('-y', '--year', nargs='+', dest='years', default=['UL18'], choices=['UL16_postVFP', 'UL16_preVFP', 'UL17', 'UL18'], help="Year of data to run. Example if more than one: --year UL17 UL18")
    parser.add_argument('-d', '--datasets', nargs='+', dest='datasets', default=['HH4b', 'ZZ4b', 'ZH4b'], help="Name of dataset to run. Example if more than one: -d HH4b ZZ4b")
    parser.add_argument('-s', '--skimming', dest="skimming", action="store_true", default=False, help='Run skimming instead of analysis')
    parser.add_argument('--condor', dest="condor", action="store_true", default=False, help='Run in condor')
    parser.add_argument('--debug', help="Print lots of debugging statements", action="store_true", dest="debug", default=False)
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)

    logging.info(f"\nRunning with these parameters: {args}")

    #
    # Metadata
    #
    configs = yaml.safe_load(open(args.configs, 'r'))
    metadata = yaml.safe_load(open(args.metadata, 'r'))

    config_runner = configs['runner'] if 'runner' in configs.keys() else {}
    config_runner.setdefault( 'data_tier', 'picoAOD' )
    config_runner.setdefault( 'chunksize', (1_000 if args.test else 100_000 ) )
    config_runner.setdefault( 'maxchunks', (1 if args.test else None ) )
    config_runner.setdefault( 'schema', NanoAODSchema )
    config_runner.setdefault( 'test_files', 5 )
    config_runner.setdefault( 'allowlist_sites', ['T3_US_FNALLPC'] )
    config_runner.setdefault( 'class_name', 'analysis' )
    config_runner.setdefault( 'condor_cores', 2 )
    config_runner.setdefault( 'condor_memory', '4GB' )

    if 'all' in args.datasets:
        metadata['datasets'].pop("mixeddata")   # AGE: this is temporary
        args.datasets = metadata['datasets'].keys()

    metadata_dataset = {}
    fileset = {}
    for year in args.years:
        logging.info(f"\nconfig year: {year}")
        for dataset in args.datasets:
            logging.info(f"\nconfig dataset: {dataset}")
            if dataset not in metadata['datasets'].keys():
                logging.error(f"{dataset} name not in metadatafile")
                continue

            if year not in metadata['datasets'][dataset]:
                logging.warning(f"{year} name not in metadatafile for {dataset}")
                continue

            if dataset in ['data', 'mixeddata'] or not ('xs' in metadata['datasets'][dataset].keys()):
                xsec = 1.
            elif isinstance(metadata['datasets'][dataset]['xs'], float):
                xsec = metadata['datasets'][dataset]['xs']
            else:
                xsec = eval(metadata['datasets'][dataset]['xs'])

            metadata_dataset[dataset] = { 'year': year,
                                         'processName': dataset,
                                         'xs': xsec,
                                         'lumi': float(metadata['datasets']['data'][year]['lumi']),
                                         'trigger':  metadata['datasets']['data'][year]['trigger'],
                                         }

            if not dataset.endswith('data'):
                if config_runner['data_tier'].startswith('pico'):
                    metadata_dataset[dataset]['genEventSumw'] = metadata['datasets'][dataset][year][config_runner['data_tier']]['sumw']
                    meta_files = metadata['datasets'][dataset][year][config_runner['data_tier']]['files']
                else:
                    meta_files = metadata['datasets'][dataset][year][config_runner['data_tier']]

                fileset[dataset + "_" + year] = {'files': list_of_files(meta_files, test=args.test, test_files=config_runner['test_files'], allowlist_sites=config_runner['allowlist_sites']),
                                                 'metadata': metadata_dataset[dataset]}

                logging.info(f'\nDataset {dataset+"_"+year} with '
                             f'{len(fileset[dataset+"_"+year]["files"])} files')

            else:

                for iera, ifile in metadata['datasets'][dataset][year][config_runner['data_tier']].items():
                    idataset = f'{dataset}_{year}{iera}'
                    metadata_dataset[idataset] = metadata_dataset[dataset]
                    metadata_dataset[idataset]['era'] = iera
                    fileset[idataset] = {'files': list_of_files( (ifile['files'] if config_runner['data_tier'].startswith('pico') else ifile ), test=args.test, test_files=config_runner['test_files'], allowlist_sites=config_runner['allowlist_sites'] ),
                                         'metadata': metadata_dataset[idataset]}
                    logging.info(f'\nDataset {idataset} with {len(fileset[idataset]["files"])} files')

    #
    # IF run in condor
    #
    if args.condor:

        from distributed import Client
        from lpcjobqueue import LPCCondorCluster

        transfer_input_files = ['analysis/', 'base_class/',
                                'data/', 'skimmer/']

        cluster_args = {'transfer_input_files': transfer_input_files,
                        'shared_temp_directory': '/tmp',
                        'cores': config_runner['condor_cores'],
                        'memory': config_runner['condor_memory'],
                        'ship_env': False}
        logging.info("\nCluster arguments: ", cluster_args)

        cluster = LPCCondorCluster(**cluster_args)
        cluster.adapt(minimum=1, maximum=200)
        client = Client(cluster)
        # client = Client()

        logging.info('\nWaiting for at least one worker...')
        client.wait_for_workers(1)

        executor_args = {
            'client': client,
            'savemetrics': True,
            'schema': config_runner['schema'],
            'align_clusters': False,
        }
    else:
        from dask.distributed import Client, LocalCluster
        client = Client()
        cluster = LocalCluster(nanny=False)
        client = Client(cluster.scheduler.address)

        executor_args = {
            'client': client,
            'schema': config_runner['schema'],
            #'workers': 6,
            'savemetrics': True}

    logging.info(f"\nExecutor arguments: {executor_args}")

    #
    # Run processor
    #
    processorName = args.processor.split('.')[0].replace("/", '.')
    analysis = getattr(importlib.import_module(processorName), config_runner['class_name'])
    logging.info(f"\nRunning processsor: {processorName}")

    tstart = time.time()
    logging.info(f"fileset keys are {fileset.keys()}")
    logging.debug(f"fileset is {fileset}")

    output, metrics = processor.run_uproot_job(
        fileset,
        treename='Events',
        processor_instance=analysis(**configs['config']),
        executor=processor.dask_executor, # if args.condor else processor.futures_executor,
        executor_args=executor_args,
        chunksize=config_runner['chunksize'],
        maxchunks=config_runner['maxchunks'],
    )
    elapsed = time.time() - tstart
    nEvent = metrics['entries']
    processtime = metrics['processtime']
    logging.info(f'\n{nEvent/elapsed:,.0f} events/s total '
                 f'({nEvent}/{elapsed})')

    if args.skimming:
        # merge output into new chunks each have `chunksize` events
        # FIXME can use a different chunksize
        output = dask.compute(resize(configs['config']['base_path'], output, 80000, 100000))[0]
        # only keep file name for each chunk
        for dataset, chunks in output.items():
            chunks['files'] = [str(f.path) for f in chunks['files']]

        metadata = fetch_metadata(fileset)

        for ikey in metadata:
            if ikey in output:
                metadata[ikey].update(output[ikey])
                metadata[ikey]['reproducible'] = {
                    'date': datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
                    'hash': get_git_revision_hash(),
                    'args': str(args),
                    'diff': str(get_git_diff()),
                    }

        args.output_file = 'picoaod_datasets.yml' if args.output_file.endswith('coffea') else args.output_file
        dfile = f'{args.output_path}/{args.output_file}'
        yaml.dump(metadata, open(dfile, 'w'), default_flow_style=False)
        logging.info(f'\nSaving metadata file {dfile}')

    else:
        #
        # Adding reproducible info
        #
        output['reproducible'] = {
            'date': datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
            'hash': get_git_revision_hash(),
            'args': args,
            'diff': get_git_diff(),
        }

        #
        #  Saving file
        #
        if not os.path.exists(args.output_path):
            os.makedirs(args.output_path)
        hfile = f'{args.output_path}/{args.output_file}'
        logging.info(f'\nSaving file {hfile}')
        save(output, hfile)
