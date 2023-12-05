import pickle, os, time, gc, argparse
from copy import deepcopy
from dataclasses import dataclass
import awkward as ak
import numpy as np
import uproot
uproot.open.defaults["xrootd_handler"] = uproot.source.xrootd.MultithreadedXRootDSource
from coffea.nanoevents import NanoEventsFactory, NanoAODSchema, BaseSchema
NanoAODSchema.warn_missing_crossrefs = False
import warnings
warnings.filterwarnings("ignore")
from coffea.nanoevents.methods import vector
ak.behavior.update(vector.behavior)
from coffea import processor, hist, util
# import hist as shh # https://hist.readthedocs.io/en/latest/
# import hist
import correctionlib
import correctionlib._core as core
import cachetools
import yaml

from analysis.helpers.MultiClassifierSchema import MultiClassifierSchema
from analysis.helpers.correctionFunctions import btagVariations, juncVariations
from analysis.helpers.correctionFunctions import btagSF_norm as btagSF_norm_file
from functools import partial
from multiprocessing import Pool

import torch
import torch.nn.functional as F
from analysis.helpers.networks import HCREnsemble
# torch.set_num_threads(1)
# torch.set_num_interop_threads(1)
# print(torch.__config__.parallel_info())

from analysis.helpers.jetCombinatoricModel import jetCombinatoricModel
from analysis.helpers.common import init_jet_factory, jet_corrections
import logging


@dataclass
class variable:
    def __init__(self, name, bins, label='Events'):
        self.name = name
        self.bins = bins
        self.label = label


def fourvectorhists(name, title, pt=(100, 0, 500), mass=(100, 0, 500), label='Events', extras=[]):
    variables = []
    variables += [variable(f'{name}.pt',   hist.Bin('x', f'{title} p$_{{\\mathrm{{T}}}}$ [GeV]', pt[0], pt[1], pt[2]), label)]
    variables += [variable(f'{name}.eta',  hist.Bin('x', f'{title} $\\eta$', 100, -5, 5), label)]
    variables += [variable(f'{name}.phi',  hist.Bin('x', f'{title} $\\phi$',  60, -np.pi, np.pi), label)]
    variables += [variable(f'{name}.mass', hist.Bin('x', f'{title} Mass [GeV]',  mass[0], mass[1], mass[2]), label)]

    variables += [variable(f'{name}.pz',     hist.Bin('x', f'{title} p$_{{\\mathrm{{z}}}}$ [GeV]', 150, 0, 1500), label)]
    variables += [variable(f'{name}.energy', hist.Bin('x', f'{title} Energy [GeV]', 100, 0, 500), label)]

    for var in extras:
        bins = deepcopy(var.bins)
        bins.label = f'{title} {var.bins.label}'
        variables += [variable(f'{name}.{var.name}', bins, label)]

    return variables


def count_nested_dict(nested_dict, c=0):
    for key in nested_dict:
        if isinstance(nested_dict[key], dict):
            c = count_nested_dict(nested_dict[key], c)
        else:
            c += 1
    return c

class analysis(processor.ProcessorABC):
    def __init__(self, JCM = '', addbtagVariations=None, addjuncVariations=None, SvB=None, SvB_MA=None, threeTag = True, apply_puWeight = False, apply_prefire = False, apply_trigWeight = True, regions=['SR'], corrections_metadata='analysis/metadata/corrections.yml', year='UL18', btagSF=True):
        logging.debug('\nInitialize Analysis Processor')
        self.blind = True
        self.year = year
        self.cuts = ['passPreSel']
        self.threeTag = threeTag
        self.tags = ['threeTag','fourTag'] if threeTag else ['fourTag']
        self.regions = regions
        self.signals = ['zz','zh','hh']
        self.JCM = jetCombinatoricModel(JCM)
        self.btagVar = btagVariations(systematics=addbtagVariations)  #### AGE: these two need to be review later
        self.juncVar = juncVariations(systematics=addjuncVariations)
        self.classifier_SvB = HCREnsemble(SvB) if SvB else None
        self.classifier_SvB_MA = HCREnsemble(SvB_MA) if SvB_MA else None
        self.apply_puWeight = apply_puWeight
        self.apply_prefire  = apply_prefire
        self.apply_trigWeight = apply_trigWeight
        self.corrections_metadata = yaml.safe_load(open(corrections_metadata, 'r'))
        self.btagSF  = btagSF

        self.variables = []
        self.variables += [variable(f'SvB_ps_{bb}', hist.Bin('x', f'SvB Regressed P(Signal) $|$ P({bb.upper()}) is largest', 100, 0, 1)) for bb in self.signals]
        self.variables += [variable(f'SvB_ps_all',  hist.Bin('x', f'SvB Regressed P(Signal)',                                100, 0, 1))]
        self.variables += [variable(f'SvB_MA_ps_{bb}', hist.Bin('x', f'SvB MA Regressed P(Signal) $|$ P({bb.upper()}) is largest', 100, 0, 1)) for bb in self.signals]
        self.variables += [variable(f'SvB_MA_ps_all',  hist.Bin('x', f'SvB MA Regressed P(Signal)',                                100, 0, 1))]
        self.variables_systematics = self.variables[0:8]
        self.variables += [variable('nJet_selected', hist.Bin('x', 'Number of Selected Jets', 16, -0.5, 15.5))]
        jet_extras = [variable('calibration', hist.Bin('x','Calibration Factor', 20, 0, 2))]
        self.variables += fourvectorhists('canJet', 'Boson Candidate Jets', mass=(50, 0, 50), label='Jets', extras=jet_extras)
        self.variables += fourvectorhists('v4j', 'Diboson Candidate', mass=(120, 0, 1200))

        diJet_extras = [variable('dr', hist.Bin('x', '$\\Delta$R(j,j)', 50, 0, 5)),
                        variable('st', hist.Bin('x', 's$_{{\\mathrm{{T}}}}$ [GeV]', 100, 0, 1000))]
        self.variables += fourvectorhists('quadJet_selected.lead', 'Leading Boson Candidate', extras=diJet_extras)
        self.variables += fourvectorhists('quadJet_selected.subl', 'Subleading Boson Candidate', extras=diJet_extras)
        self.variables += [variable('quadJet_selected.dr', hist.Bin('x', 'Selected Diboson Candidate $\\Delta$R(d,d)', 50, 0, 5))]
        self.variables += [variable(f'quadJet_selected.x{bb.upper()}', hist.Bin('x', f'Selected Diboson Candidate X$_{{\\mathrm{bb.upper()}}}$', 100, 0, 10)) for bb in self.signals]

        self._accumulator = processor.dict_accumulator({'cutflow': processor.defaultdict_accumulator(partial(processor.defaultdict_accumulator,
                                                                                                             partial(processor.defaultdict_accumulator,
                                                                                                                     partial(processor.defaultdict_accumulator, float)
                                                                                                                 )
                                                                                                             )
                                                                                                         ),
                                                        'nEvent' : processor.defaultdict_accumulator(int),
                                                        'hists'  : processor.dict_accumulator()})

        for junc in self.juncVar:
            logging.info(f'Making hists for {junc}')
            self._accumulator['hists'][junc] = processor.dict_accumulator()
            for cut in self.cuts:
                logging.info(f'    {cut}')
                self._accumulator['hists'][junc][cut] = processor.dict_accumulator()
                for tag in self.tags:
                    logging.info(f'        {tag}')
                    self._accumulator['hists'][junc][cut][tag] = processor.dict_accumulator()
                    for region in self.regions:
                        logging.info(f'            {region}')
                        self._accumulator['hists'][junc][cut][tag][region] = processor.dict_accumulator()
                        for var in self.variables:
                            self._accumulator['hists'][junc][cut][tag][region][var.name] = hist.Hist(var.label, hist.Cat('dataset', 'Dataset'), var.bins)

            self._accumulator['hists'][junc]['passPreSel']['fourTag']['SR']['trigWeight_Bool'] = processor.dict_accumulator()
            self._accumulator['hists'][junc]['passPreSel']['fourTag']['SR']['trigWeight_Data'] = processor.dict_accumulator()
            self._accumulator['hists'][junc]['passPreSel']['fourTag']['SR']['trigWeight_MC']   = processor.dict_accumulator()
            for syst in self.btagVar:
                self._accumulator['hists'][junc]['passPreSel']['fourTag']['SR'][f'btagSF_{syst}'] = processor.dict_accumulator()
            for syst in self.juncVar:
                self._accumulator['hists'][junc]['passPreSel']['fourTag']['SR'][       f'{syst}'] = processor.dict_accumulator()
            for syst in ['unit', 'up', 'down', 'central']:
                if self.apply_puWeight:
                    self._accumulator['hists'][junc]['passPreSel']['fourTag']['SR'][f'puWeight_{syst}'] = processor.dict_accumulator()
                if self.apply_prefire:
                    self._accumulator['hists'][junc]['passPreSel']['fourTag']['SR'][f'prefire_{syst}'] = processor.dict_accumulator()

            for var in self.variables_systematics:
                self._accumulator['hists'][junc]['passPreSel']['fourTag']['SR']['trigWeight_Bool'][var.name] = hist.Hist(var.label, hist.Cat('dataset', 'Dataset'), var.bins)
                self._accumulator['hists'][junc]['passPreSel']['fourTag']['SR']['trigWeight_Data'][var.name] = hist.Hist(var.label, hist.Cat('dataset', 'Dataset'), var.bins)
                self._accumulator['hists'][junc]['passPreSel']['fourTag']['SR']['trigWeight_MC'  ][var.name] = hist.Hist(var.label, hist.Cat('dataset', 'Dataset'), var.bins)
                for syst in self.btagVar:
                    self._accumulator['hists'][junc]['passPreSel']['fourTag']['SR'][f'btagSF_{syst}'][var.name] = hist.Hist(var.label, hist.Cat('dataset', 'Dataset'), var.bins)
                # for syst in self.juncVar:
                #     self._accumulator['hists'][junc]['passPreSel']['fourTag']['SR'][       f'{syst}'][var.name] = hist.Hist(var.label, hist.Cat('dataset', 'Dataset'), var.bins)
                for syst in ['unit', 'up', 'down', 'central']:
                    if self.apply_puWeight:
                        self._accumulator['hists'][junc]['passPreSel']['fourTag']['SR'][f'puWeight_{syst}'][var.name] = hist.Hist(var.label, hist.Cat('dataset', 'Dataset'), var.bins)
                    if self.apply_prefire:
                        self._accumulator['hists'][junc]['passPreSel']['fourTag']['SR'][f'prefire_{syst}'][var.name] = hist.Hist(var.label, hist.Cat('dataset', 'Dataset'), var.bins)

        self.nHists = count_nested_dict(self._accumulator['hists'])
        logging.info(f'{self.nHists} total histograms')

    @property
    def accumulator(self):
        return self._accumulator

    def cutflow(self, output, dataset, event, cut, allTag=False, junc='JES_Central'):
        if allTag:
            w = event.weight
            sumw = np.sum(w)
            sumw_3, sumw_4 = sumw, sumw
        else:
            e3, e4 = event[event.threeTag], event[event.fourTag]
            sumw_3 = np.sum(e3.weight)
            sumw_4 = np.sum(e4.weight)

        output['cutflow'][junc]['threeTag'][cut][dataset] += sumw_3
        output['cutflow'][junc][ 'fourTag'][cut][dataset] += sumw_4

        if event.metadata.get('isMC', False) and not allTag:   ##### AGE: why isMC to False?
            output['cutflow'][junc]['threeTag'][cut+'_HLT_Bool'][dataset] += np.sum(e3.weight*e3.passHLT)
            output['cutflow'][junc][ 'fourTag'][cut+'_HLT_Bool'][dataset] += np.sum(e4.weight*e4.passHLT)

            output['cutflow'][junc]['threeTag'][cut+'_HLT_MC'  ][dataset] += np.sum(e3.weight*e3.trigWeight.MC)
            output['cutflow'][junc][ 'fourTag'][cut+'_HLT_MC'  ][dataset] += np.sum(e4.weight*e4.trigWeight.MC)

            output['cutflow'][junc]['threeTag'][cut+'_HLT_Data'][dataset] += np.sum(e3.weight*e3.trigWeight.Data)
            output['cutflow'][junc][ 'fourTag'][cut+'_HLT_Data'][dataset] += np.sum(e4.weight*e4.trigWeight.Data)


    def process(self, event):
        tstart = time.time()
        output = self.accumulator.identity()

        fname   = event.metadata['filename']
        dataset = event.metadata['dataset']
        estart  = event.metadata['entrystart']
        estop   = event.metadata['entrystop']
        chunk   = f'{dataset}::{estart:6d}:{estop:6d} >>> '
        year    = self.year
        isMC    = True if event.run[0] == 1 else False
        lumi    = event.metadata.get('lumi',    1.0)
        xs      = event.metadata.get('xs',      1.0)
        kFactor = event.metadata.get('kFactor', 1.0)
        btagSF_norm = btagSF_norm_file(dataset)
        nEvent = len(event)
        np.random.seed(0)
        output['nEvent'][dataset] += nEvent
        puWeight= self.corrections_metadata[year]['PU']
        juncWS = [ self.corrections_metadata[year]["JERC"][0].replace('STEP', istep) for istep in ['L1FastJet', 'L2Relative', 'L2L3Residual', 'L3Absolute'] ]  ###### AGE: to be reviewed for data, but should be remove with jsonpog
        if isMC: juncWS += self.corrections_metadata[year]["JERC"][1:]

        self.apply_puWeight   = (self.apply_puWeight  ) and isMC and (puWeight is not None)
        self.apply_prefire    = (self.apply_prefire   ) and isMC and ('L1PreFiringWeight' in event.fields) and (year!='2018')
        self.apply_trigWeight = (self.apply_trigWeight) and isMC and ('trigWeight' in event.fields)

        if isMC:
            with uproot.open(fname) as rfile:
                Runs = rfile['Runs']
                genEventSumw = np.sum(Runs['genEventSumw'])

            if self.btagSF is not None:
                btagSF = correctionlib.CorrectionSet.from_file(self.corrections_metadata[self.year]['btagSF'])['deepJet_shape']

            if self.apply_puWeight:
                puWeight = list(correctionlib.CorrectionSet.from_file(puWeight).values())[0]

        # dataset_axis = shh.axis.StrCategory([], growth=True, name='dataset', label='Dataset')
        # cut_axis     = shh.axis.StrCategory([], growth=True, name='cut',     label='Cut')
        # tag_axis     = shh.axis.StrCategory(['threeTag', 'fourTag'], name='tag', label='b-tag Category')
        # region_axis  = shh.axis.StrCategory([], growth=True, name='region',  label='Region')

        largest_name = np.array(['None', 'ZZ', 'ZH', 'HH'])
        # SvB_largest_axis   = shh.axis.StrCategory(largest_name, name='SvB_largest', label='Highest probability signal class')
        # SvB_ps_axis        = shh.axis.Regular(100, 0, 1, name='SvB', label='SvB Regressed P(Signal)')
        # nJet_selected_axis = shh.axis.Integer(0, 15, name='nJet_selected', label='Number of selected jets')
        # output['hists']['SvB_ps_zz_nJet_selected'] = shh.Hist(dataset_axis,
        #                                                       cut_axis,
        #                                                       tag_axis,
        #                                                       region_axis,
        #                                                       SvB_largest_axis,
        #                                                       SvB_ps_axis,
        #                                                       nJet_selected_axis,
        #                                                       storage='weight', label='Events')

        logging.debug(fname)
        logging.debug(f'{chunk}Process {nEvent} Events')

        #
        # Reading SvB friend trees
        #
        path = fname.replace(fname.split('/')[-1],'')
        event['SvB']    = NanoEventsFactory.from_root(f'{path}{"SvB_newSBDef.root" if "mix" in dataset else "SvB.root"}',    entry_start=estart, entry_stop=estop, schemaclass=MultiClassifierSchema).events().SvB
        event['SvB_MA'] = NanoEventsFactory.from_root(f'{path}{"SvB_MA_newSBDef.root" if "mix" in dataset else "SvB_MA.root"}', entry_start=estart, entry_stop=estop, schemaclass=MultiClassifierSchema).events().SvB_MA

        if not ak.all(event.SvB.event == event.event):
            logging.error('ERROR: SvB events do not match events ttree')
            return
        if not ak.all(event.SvB_MA.event == event.event):
            logging.error('ERROR: SvB_MA events do not match events ttree')
            return

        #
        # defining SvB for different SR
        #
        event['SvB', 'passMinPs'] = (event.SvB.pzz>0.01) | (event.SvB.pzh>0.01) | (event.SvB.phh>0.01)
        event['SvB', 'zz'] = (event.SvB.pzz >  event.SvB.pzh) & (event.SvB.pzz >  event.SvB.phh)
        event['SvB', 'zh'] = (event.SvB.pzh >  event.SvB.pzz) & (event.SvB.pzh >  event.SvB.phh)
        event['SvB', 'hh'] = (event.SvB.phh >= event.SvB.pzz) & (event.SvB.phh >= event.SvB.pzh)
        event['SvB', 'largest'] = largest_name[ event.SvB.passMinPs*(1*event.SvB.zz + 2*event.SvB.zh + 3*event.SvB.hh) ]

        event['SvB_MA', 'passMinPs'] = (event.SvB_MA.pzz>0.01) | (event.SvB_MA.pzh>0.01) | (event.SvB_MA.phh>0.01)
        event['SvB_MA', 'zz'] = (event.SvB_MA.pzz >  event.SvB_MA.pzh) & (event.SvB_MA.pzz >  event.SvB_MA.phh)
        event['SvB_MA', 'zh'] = (event.SvB_MA.pzh >  event.SvB_MA.pzz) & (event.SvB_MA.pzh >  event.SvB_MA.phh)
        event['SvB_MA', 'hh'] = (event.SvB_MA.phh >= event.SvB_MA.pzz) & (event.SvB_MA.phh >= event.SvB_MA.pzh)

        if isMC:
            for junc in self.juncVar:
                output['cutflow'][junc]['threeTag']['all'][dataset] = lumi * xs * kFactor
                output['cutflow'][junc][ 'fourTag']['all'][dataset] = lumi * xs * kFactor
        else:
            self.cutflow(output, dataset, event, 'all', allTag = True)

        #
        # Get trigger decisions
        #
        if year == '2016':
            event['passHLT'] = event.HLT.QuadJet45_TripleBTagCSV_p087 | event.HLT.DoubleJet90_Double30_TripleBTagCSV_p087 | event.HLT.DoubleJetsC100_DoubleBTagCSV_p014_DoublePFJetsC100MaxDeta1p6
        if year == '2017':
            event['passHLT'] = event.HLT.PFHT300PT30_QuadPFJet_75_60_45_40_TriplePFBTagCSV_3p0 | event.HLT.DoublePFJets100MaxDeta1p6_DoubleCaloBTagCSV_p33
        if year == '2018':
            event['passHLT'] = event.HLT.DoublePFJets116MaxDeta1p6_DoubleCaloBTagDeepCSV_p71 | event.HLT.PFHT330PT30_QuadPFJet_75_60_45_40_TriplePFBTagDeepCSV_4p5

        if not isMC and not 'mix' in dataset: # for data, apply trigger cut first thing, for MC, keep all events and apply trigger in cutflow and for plotting
            event = event[event.passHLT]

        if isMC:
            event['weight'] = event.genWeight * (lumi * xs * kFactor / genEventSumw)
            logging.debug(f"event['weight'] = event.genWeight * (lumi * xs * kFactor / genEventSumw) = {event.genWeight[0]} * ({lumi} * {xs} * {kFactor} / {genEventSumw}) = {event.weight[0]}")

        #
        # METFilter
        #
        passMETFilter = np.ones(len(event), dtype=bool) if 'mix' in dataset else ( event.Flag.goodVertices & event.Flag.globalSuperTightHalo2016Filter & event.Flag.HBHENoiseFilter   & event.Flag.HBHENoiseIsoFilter & event.Flag.EcalDeadCellTriggerPrimitiveFilter & event.Flag.BadPFMuonFilter & event.Flag.eeBadScFilter)
        # passMETFilter *= event.Flag.EcalDeadCellTriggerPrimitiveFilter & event.Flag.BadPFMuonFilter                & event.Flag.BadPFMuonDzFilter & event.Flag.hfNoisyHitsFilter & event.Flag.eeBadScFilter
        if 'mix' not in dataset:
            if 'BadPFMuonDzFilter' in event.Flag.fields:
                passMETFilter = passMETFilter & event.Flag.BadPFMuonDzFilter
            if 'hfNoisyHitsFilter' in event.Flag.fields:
                passMETFilter = passMETFilter & event.Flag.hfNoisyHitsFilter
            if year == '2017' or year == '2018':
                passMETFilter = passMETFilter & event.Flag.ecalBadCalibFilter # in UL the name does not have "V2"
        event['passMETFilter'] = passMETFilter
        event = event[event.passMETFilter]
        self.cutflow(output, dataset, event, 'passMETFilter', allTag = True)


        #
        # Calculate and apply Jet Energy Calibration   ## AGE: currently not applying to data and mixeddata
        #
        if isMC and juncWS is not None:
            jet_factory = init_jet_factory(juncWS)

            event['Jet', 'pt_raw']    = (1 - event.Jet.rawFactor) * event.Jet.pt
            event['Jet', 'mass_raw']  = (1 - event.Jet.rawFactor) * event.Jet.mass
            nominal_jet = event.Jet
            # nominal_jet['pt_raw']   = (1 - nominal_jet.rawFactor) * nominal_jet.pt
            # nominal_jet['mass_raw'] = (1 - nominal_jet.rawFactor) * nominal_jet.mass
            if isMC: nominal_jet['pt_gen']   = ak.values_astype(ak.fill_none(nominal_jet.matched_gen.pt, 0), np.float32)
            nominal_jet['rho']      = ak.broadcast_arrays(event.fixedGridRhoFastjetAll, nominal_jet.pt)[0]

            jec_cache = cachetools.Cache(np.inf)
            jet_variations = jet_factory.build(nominal_jet, lazy_cache=jec_cache)
            jet_tmp = jet_corrections( event.Jet, event.fixedGridRhoFastjetAll, jec_type=['L1L2L3Res'] )   ##### AGE: jsonpog+correctionlib but not final, that is why it is not used yet

        #
        # Loop over jet energy uncertainty variations running event selection, filling hists/cuflows independently for each jet calibration
        #
        for junc in self.juncVar:
            if junc != 'JES_Central':
                logging.debug(f'{chunk} running selection for {junc}')
                variation = '_'.join(junc.split('_')[:-1]).replace('YEAR', year)
                if 'JER' in junc: variation = variation.replace(f'_{year}','')
                direction = junc.split('_')[-1]
                # del event['Jet']
                event['Jet'] = jet_variations[variation, direction]

            event['Jet', 'calibration'] = event.Jet.pt/( 1 if 'data' in dataset else event.Jet.pt_raw )  ### AGE: I include the mix condition, I think it is wrong, to check later
            # if junc=='JES_Central':
            #     print(f'calibration nominal: \n{ak.mean(event.Jet.calibration)}')
            # else:
            #     print(f'calibration {variation} {direction}: \n{ak.mean(event.Jet.calibration)}')

            event['Jet', 'pileup'] = ((event.Jet.puId<0b110)&(event.Jet.pt<50)) | ((np.abs(event.Jet.eta)>2.4)&(event.Jet.pt<40))
            event['Jet', 'selected_loose'] = (event.Jet.pt>=20) & ~event.Jet.pileup
            event['Jet', 'selected'] = (event.Jet.pt>=40) & (np.abs(event.Jet.eta)<=2.4) & ~event.Jet.pileup
            event['nJet_selected'] = ak.sum(event.Jet.selected, axis=1)
            event['selJet'] = event.Jet[event.Jet.selected]

            selev = event[event.nJet_selected >= 4]
            self.cutflow(output, dataset, selev, 'passJetMult', allTag = True, junc=junc)

            selev['Jet', 'tagged']       = selev.Jet.selected & (selev.Jet.btagDeepFlavB>=0.6)
            selev['Jet', 'tagged_loose'] = selev.Jet.selected & (selev.Jet.btagDeepFlavB>=0.3)
            selev['nJet_tagged']         = ak.num(selev.Jet[selev.Jet.tagged])
            selev['nJet_tagged_loose']   = ak.num(selev.Jet[selev.Jet.tagged_loose])

            fourTag  = (selev['nJet_tagged']       >= 4)
            threeTag = (selev['nJet_tagged_loose'] == 3) & (selev['nJet_selected'] >= 4)

            # check that coffea jet selection agrees with c++
            if junc == 'JES_Central':
                selev['issue'] = (threeTag!=selev.threeTag)|(fourTag!=selev.fourTag)
                if ak.any(selev.issue):
                    logging.warning(f'{chunk}WARNING: selected jets or fourtag calc not equal to picoAOD values')
                    logging.warning('nSelJets')
                    logging.warning(selev[selev.issue].nSelJets)
                    logging.warning(selev[selev.issue].nJet_selected)
                    logging.warning('fourTag')
                    logging.warning(selev.fourTag[selev.issue])
                    logging.warning(fourTag[selev.issue])

            selev[ 'fourTag']   =  fourTag
            selev['threeTag']   = threeTag * self.threeTag
            selev['passPreSel'] = selev.threeTag | selev.fourTag

            #
            # Calculate and apply pileup weight, L1 prefiring weight
            #
            if self.apply_puWeight:
                for var in ['nominal', 'up', 'down']:
                    selev[f'PU_weight_{var}'] = puWeight.evaluate(selev.Pileup.nTrueInt.to_numpy(), var)
                selev['weight'] = selev.weight * selev.PU_weight_nominal
            if self.apply_prefire:
                selev['weight'] = selev.weight * selev.L1PreFiringWeight.Nom

            #
            # Calculate and apply btag scale factors
            #
            if isMC and btagSF is not None:
                #central = 'central'
                use_central = True
                btag_jes = []
                if junc != 'JES_Central':# and 'JER' not in junc:# and 'JES_Total' not in junc:
                    use_central = False
                    jes_or_jer = 'jer' if 'JER' in junc else 'jes'
                    btag_jes = [f'{direction}_{jes_or_jer}{variation.replace("JES_","").replace("Total","")}']
                cj, nj = ak.flatten(selev.selJet), ak.num(selev.selJet)
                hf, eta, pt, tag = np.array(cj.hadronFlavour), np.array(abs(cj.eta)), np.array(cj.pt), np.array(cj.btagDeepFlavB)

                cj_bl = selev.selJet[selev.selJet.hadronFlavour!=4]
                nj_bl = ak.num(cj_bl)
                cj_bl = ak.flatten(cj_bl)
                hf_bl, eta_bl, pt_bl, tag_bl = np.array(cj_bl.hadronFlavour), np.array(abs(cj_bl.eta)), np.array(cj_bl.pt), np.array(cj_bl.btagDeepFlavB)
                SF_bl= btagSF.evaluate('central', hf_bl, eta_bl, pt_bl, tag_bl)
                SF_bl = ak.unflatten(SF_bl, nj_bl)
                SF_bl = np.prod(SF_bl, axis=1)

                cj_c = selev.selJet[selev.selJet.hadronFlavour==4]
                nj_c = ak.num(cj_c)
                cj_c = ak.flatten(cj_c)
                hf_c, eta_c, pt_c, tag_c = np.array(cj_c.hadronFlavour), np.array(abs(cj_c.eta)), np.array(cj_c.pt), np.array(cj_c.btagDeepFlavB)
                SF_c= btagSF.evaluate('central', hf_c, eta_c, pt_c, tag_c)
                SF_c = ak.unflatten(SF_c, nj_c)
                SF_c = np.prod(SF_c, axis=1)

                for sf in self.btagVar+btag_jes:
                    if sf == 'central':
                        SF = btagSF.evaluate('central', hf, eta, pt, tag)
                        SF = ak.unflatten(SF, nj)
                        # hf = ak.unflatten(hf, nj)
                        # pt = ak.unflatten(pt, nj)
                        # eta = ak.unflatten(eta, nj)
                        # tag = ak.unflatten(tag, nj)
                        # for i in range(len(selev)):
                        #     for j in range(nj[i]):
                        #         print(f'jetPt/jetEta/jetTagScore/jetHadronFlavour/SF = {pt[i][j]}/{eta[i][j]}/{tag[i][j]}/{hf[i][j]}/{SF[i][j]}')
                        #     print(np.prod(SF[i]))
                        SF = np.prod(SF, axis=1)
                    if '_cf' in sf:
                        SF = btagSF.evaluate(sf, hf_c, eta_c, pt_c, tag_c)
                        SF = ak.unflatten(SF, nj_c)
                        SF = SF_bl * np.prod(SF, axis=1) # use central value for b,l jets
                    if '_hf' in sf or '_lf' in sf or '_jes' in sf:
                        SF = btagSF.evaluate(sf, hf_bl, eta_bl, pt_bl, tag_bl)
                        SF = ak.unflatten(SF, nj_bl)
                        SF = SF_c * np.prod(SF, axis=1) # use central value for charm jets

                    selev[f'btagSF_{sf}'] = SF * btagSF_norm
                    selev[f'weight_btagSF_{sf}'] = selev.weight * SF * btagSF_norm

                selev['weight'] = selev[f'weight_btagSF_{"central" if use_central else btag_jes[0]}']
                self.cutflow(output, dataset, selev, 'passJetMult_btagSF', allTag = True, junc=junc)


            # for i in range(len(selev)):
            #     print(selev.event[i], selev.btagSF_central[i])

            #
            # Preselection: keep only three or four tag events
            #
            selev = selev[selev.passPreSel]

            #
            # Build and select boson candidate jets with bRegCorr applied
            #
            sorted_idx = ak.argsort(selev.Jet.btagDeepFlavB * selev.Jet.selected, axis=1, ascending=False)
            canJet_idx = sorted_idx[:,0:4]
            notCanJet_idx = sorted_idx[:,4:]
            canJet = selev.Jet[canJet_idx]
            # apply bJES to canJets
            canJet = canJet * canJet.bRegCorr
            canJet['bRegCorr'] = selev.Jet.bRegCorr[canJet_idx]
            canJet['btagDeepFlavB'] = selev.Jet.btagDeepFlavB[canJet_idx]
            if isMC:
                canJet['hadronFlavour'] = selev.Jet.hadronFlavour[canJet_idx]
            canJet['calibration'] = selev.Jet.calibration[canJet_idx]

            # pt sort canJets
            canJet = canJet[ak.argsort(canJet.pt, axis=1, ascending=False)]
            selev['canJet'] = canJet
            selev['v4j'] = canJet.sum(axis=1)
            # selev['Jet', 'canJet'] = False
            # selev.Jet.canJet.Fill(canJet_idx, True)
            notCanJet = selev.Jet[notCanJet_idx]
            notCanJet = notCanJet[notCanJet.selected_loose]
            notCanJet = notCanJet[ak.argsort(notCanJet.pt, axis=1, ascending=False)]
            notCanJet['isSelJet'] = 1*((notCanJet.pt>40) & (np.abs(notCanJet.eta)<2.4)) # should have been defined as notCanJet.pt>=40, too late to fix this now...
            selev['notCanJet_coffea'] = notCanJet
            selev['nNotCanJet'] = ak.num(selev.notCanJet_coffea)

            # if junc=='JES_Central':
            #     print(f'{ak.mean(canJet.calibration)} (canJets)')
            # else:
            #     print(f'{ak.mean(canJet.calibration)} (canJets)')
            # print(canJet_idx[0])
            # print(selev[0].Jet[canJet_idx[0]].pt)
            # print(selev[0].Jet[canJet_idx[0]].bRegCorr)
            # print(selev[0].Jet[canJet_idx[0]].calibration)


            if self.threeTag:
                #
                # calculate pseudoTagWeight for threeTag events
                #
                selev['Jet_untagged_loose'] = selev.Jet[selev.Jet.selected & ~selev.Jet.tagged_loose]
                nJet_pseudotagged = np.zeros(len(selev), dtype=int)
                pseudoTagWeight = np.ones(len(selev))
                pseudoTagWeight[selev.threeTag], nJet_pseudotagged[selev.threeTag] = self.JCM(selev[selev.threeTag]['Jet_untagged_loose'])
                selev['nJet_pseudotagged'] = nJet_pseudotagged

                # check that pseudoTagWeight calculation agrees with c++
                if junc == 'JES_Central':
                    selev.issue = (abs(selev.pseudoTagWeight - pseudoTagWeight)/selev.pseudoTagWeight > 0.0001) & (selev.pseudoTagWeight!=1)
                    if ak.any(selev.issue):
                        logging.warning(f'{chunk}WARNING: python pseudotag calc not equal to c++ calc')
                        logging.warning(f'{chunk}Issues:',ak.sum(selev.issue),'of',ak.sum(selev.threeTag))

                # add pseudoTagWeight to event
                selev['pseudoTagWeight'] = pseudoTagWeight

                # apply pseudoTagWeight to threeTag events
                e3 = selev[selev.threeTag]
                selev[selev.threeTag]['weight'] = e3.weight * e3.pseudoTagWeight

            # presel cutflow with pseudotag weight included
            self.cutflow(output, dataset, selev, 'passPreSel', junc=junc)


            #
            # Build diJets, indexed by diJet[event,pairing,0/1]
            #
            canJet = selev['canJet']
            pairing = [([0,2],[0,1],[0,1]),
                       ([1,3],[2,3],[3,2])]
            diJet       = canJet[:,pairing[0]]     +   canJet[:,pairing[1]]
            diJet['st'] = canJet[:,pairing[0]].pt  +   canJet[:,pairing[1]].pt
            diJet['dr'] = canJet[:,pairing[0]].delta_r(canJet[:,pairing[1]])
            diJet['lead'] = canJet[:,pairing[0]]
            diJet['subl'] = canJet[:,pairing[1]]
            # Sort diJets within views to be lead st, subl st
            diJet = diJet[ak.argsort(diJet.st, axis=2, ascending=False)]
            # Now indexed by diJet[event,pairing,lead/subl st]

            # Compute diJetMass cut with independent min/max for lead/subl
            minDiJetMass = np.array([[[ 52, 50]]])
            maxDiJetMass = np.array([[[180,173]]])
            diJet['passDiJetMass'] = (minDiJetMass < diJet.mass) & (diJet.mass < maxDiJetMass)

            # Compute MDRs
            min_m4j_scale = np.array([[ 360, 235]])
            min_dr_offset = np.array([[-0.5, 0.0]])
            max_m4j_scale = np.array([[ 650, 650]])
            max_dr_offset = np.array([[ 0.5, 0.7]])
            max_dr        = np.array([[ 1.5, 1.5]])
            m4j = np.repeat(np.reshape(np.array(selev['v4j'].mass), (-1,1,1)), 2, axis=2)
            diJet['passMDR'] = (min_m4j_scale/m4j + min_dr_offset < diJet.dr) & (diJet.dr < np.maximum(max_m4j_scale/m4j + max_dr_offset, max_dr))

            # Compute consistency of diJet masses with boson masses
            mZ =  91.0
            mH = 125.0
            st_bias = np.array([[[1.02, 0.98]]])
            cZ = mZ * st_bias
            cH = mH * st_bias

            diJet['xZ'] = (diJet.mass - cZ)/(0.1*diJet.mass)
            diJet['xH'] = (diJet.mass - cH)/(0.1*diJet.mass)


            #
            # Build quadJets
            #
            quadJet = ak.zip({'lead': diJet[:,:,0],
                              'subl': diJet[:,:,1],
                              'passDiJetMass': ak.all(diJet.passDiJetMass, axis=2),
                              'random': np.random.uniform(low=0.1, high=0.9, size=(diJet.__len__(), 3))
                          })#, with_name='quadJet')
            quadJet['dr'] = quadJet['lead'].delta_r(quadJet['subl'])
            quadJet['SvB_q_score'] = np.concatenate((np.reshape(np.array(selev.SvB.q_1234), (-1,1)),
                                                     np.reshape(np.array(selev.SvB.q_1324), (-1,1)),
                                                     np.reshape(np.array(selev.SvB.q_1423), (-1,1))), axis=1)
            quadJet['SvB_MA_q_score'] = np.concatenate((np.reshape(np.array(selev.SvB_MA.q_1234), (-1,1)),
                                                        np.reshape(np.array(selev.SvB_MA.q_1324), (-1,1)),
                                                        np.reshape(np.array(selev.SvB_MA.q_1423), (-1,1))), axis=1)

            # Compute Signal Regions
            quadJet['xZZ'] = np.sqrt(quadJet.lead.xZ**2 + quadJet.subl.xZ**2)
            quadJet['xHH'] = np.sqrt(quadJet.lead.xH**2 + quadJet.subl.xH**2)
            quadJet['xZH'] = np.sqrt(np.minimum(quadJet.lead.xH**2 + quadJet.subl.xZ**2,
                                                quadJet.lead.xZ**2 + quadJet.subl.xH**2))
            max_xZZ = 2.6
            max_xZH = 1.9
            max_xHH = 1.9
            quadJet['ZZSR'] = quadJet.xZZ < max_xZZ
            quadJet['ZHSR'] = quadJet.xZH < max_xZH
            quadJet['HHSR'] = quadJet.xHH < max_xHH
            quadJet['SR'] = quadJet.ZZSR | quadJet.ZHSR | quadJet.HHSR
            quadJet['SB'] = quadJet.passDiJetMass & ~quadJet.SR

            # pick quadJet at random giving preference to ones which passDiJetMass and MDRs
            quadJet['rank'] = 10*quadJet.passDiJetMass + quadJet.lead.passMDR + quadJet.subl.passMDR + quadJet.random
            quadJet['selected'] = quadJet.rank == np.max(quadJet.rank, axis=1)

            selev[  'diJet'] =   diJet
            selev['quadJet'] = quadJet
            selev['quadJet_selected'] = quadJet[quadJet.selected][:,0]

            # selev.issue = (selev.leadStM<0) | (selev.sublStM<0)
            # if ak.any(selev.issue):
            #     print(f'{chunk}WARNING: Negative diJet masses in picoAOD variables generated by the c++')
            #     issue = selev[selev.issue]
            #     print(f'{chunk}{len(issue)} events with issues')
            #     print(f'{chunk}c++ values:',issue.passDiJetMass, issue.leadStM,issue.sublStM)
            #     print(f'{chunk}py  values:',issue.quadJet_selected.passDiJetMass, issue.quadJet_selected.lead.mass, issue.quadJet_selected.subl.mass)

            # if junc == 'JES_Central':
            #     selev.issue = selev.passDijetMass != selev['quadJet_selected'].passDiJetMass
            #     selev.issue = selev.issue & ~((selev.leadStM<0) | (selev.sublStM<0))
            #     if ak.any(selev.issue):
            #         print(f'{chunk}WARNING: passDiJetMass calc not equal to picoAOD value')
            #         issue = selev[selev.issue]
            #         print(f'{chunk}{len(issue)} events with issues')
            #         print(f'{chunk}c++ values:',issue.passDijetMass, issue.leadStM,issue.sublStM)
            #         print(f'{chunk}py  values:',issue.quadJet_selected.passDiJetMass, issue.quadJet_selected.lead.mass, issue.quadJet_selected.subl.mass)


            # Blind data in fourTag SR
            if not (isMC or 'mixed' in dataset) and self.blind:
                selev = selev[~(selev.SR & selev.fourTag)]

            self.cutflow(output, dataset, selev[selev['quadJet_selected'].passDiJetMass], 'passDiJetMass', junc=junc)
            self.cutflow(output, dataset, selev[selev['quadJet_selected'].SR], 'SR', junc=junc)

            if self.classifier_SvB is not None:
                self.compute_SvB(selev, junc=junc)


            #
            # fill histograms
            #
            self.fill(selev, output, junc=junc)



            if isMC:
                self.fill_systematics(selev, output, junc=junc)
            garbage = gc.collect()
            # print('Garbage:',garbage)


        # Done
        elapsed = time.time() - tstart
        logging.debug(f'{chunk}{nEvent/elapsed:,.0f} events/s')
        return output


    def compute_SvB(self, event, junc='JES_Central'):
        n = len(event)

        j = torch.zeros(n, 4, 4)
        j[:,0,:] = torch.tensor( event.canJet.pt   )
        j[:,1,:] = torch.tensor( event.canJet.eta  )
        j[:,2,:] = torch.tensor( event.canJet.phi  )
        j[:,3,:] = torch.tensor( event.canJet.mass )

        o = torch.zeros(n, 5, 8)
        o[:,0,:] = torch.tensor( ak.fill_none(ak.to_regular(ak.pad_none(event.notCanJet_coffea.pt,       target=8, clip=True)),  0) )
        o[:,1,:] = torch.tensor( ak.fill_none(ak.to_regular(ak.pad_none(event.notCanJet_coffea.eta,      target=8, clip=True)),  0) )
        o[:,2,:] = torch.tensor( ak.fill_none(ak.to_regular(ak.pad_none(event.notCanJet_coffea.phi,      target=8, clip=True)),  0) )
        o[:,3,:] = torch.tensor( ak.fill_none(ak.to_regular(ak.pad_none(event.notCanJet_coffea.mass,     target=8, clip=True)),  0) )
        o[:,4,:] = torch.tensor( ak.fill_none(ak.to_regular(ak.pad_none(event.notCanJet_coffea.isSelJet, target=8, clip=True)), -1) )

        a = torch.zeros(n, 4)
        a[:,0] =        float( event.metadata['year'][3] )
        a[:,1] = torch.tensor( event.nJet_selected )
        a[:,2] = torch.tensor( event.xW )
        a[:,3] = torch.tensor( event.xbW )

        e = torch.tensor(event.event)%3

        for classifier in ['SvB', 'SvB_MA']:
            if classifier == 'SvB':
                c_logits, q_logits = self.classifier_SvB(j, o, a, e)
            if classifier == 'SvB_MA':
                c_logits, q_logits = self.classifier_SvB_MA(j, o, a, e)

            c_score, q_score = F.softmax(c_logits, dim=-1).numpy(), F.softmax(q_logits, dim=-1).numpy()

            # classes = [mj,tt,zz,zh,hh]
            SvB = ak.zip({'pmj': c_score[:,0],
                          'ptt': c_score[:,1],
                          'pzz': c_score[:,2],
                          'pzh': c_score[:,3],
                          'phh': c_score[:,4],
                          'q_1234': q_score[:,0],
                          'q_1324': q_score[:,1],
                          'q_1423': q_score[:,2],
                      })
            SvB['ps'] = SvB.pzz + SvB.pzh + SvB.phh
            SvB['passMinPs'] = (SvB.pzz>0.01) | (SvB.pzh>0.01) | (SvB.phh>0.01)
            SvB['zz'] = (SvB.pzz >  SvB.pzh) & (SvB.pzz >  SvB.phh)
            SvB['zh'] = (SvB.pzh >  SvB.pzz) & (SvB.pzh >  SvB.phh)
            SvB['hh'] = (SvB.phh >= SvB.pzz) & (SvB.phh >= SvB.pzh)

            if junc == 'JES_Central':
                error = ~np.isclose(event[classifier].ps, SvB.ps, atol=1e-5, rtol=1e-3)
                if np.any(error):
                    delta = np.abs(event[classifier].ps - SvB.ps)
                    worst = np.max(delta) == delta #np.argmax(np.abs(delta))
                    worst_event = event[worst][0]
                    logging.warning(f'WARNING: Calculated {classifier} does not agree within tolerance for some events ({np.sum(error)}/{len(error)})', delta[worst])
                    logging.warning('----------')
                    for field in event[classifier].fields:
                          logging.warning(field, worst_event[classifier][field])
                    logging.warning('----------')
                    for field in SvB.fields:
                        logging.warning( f'{field}, {SvB[worst][field]}')

            # del event[classifier]
            event[classifier] = SvB


    def fill_SvB(self, hist, event, weight):
        dataset = event.metadata.get('dataset','')
        for classifier in ['SvB', 'SvB_MA']:
            for bb in self.signals:
                mask = event[classifier][bb]
                x, w = event[mask][classifier].ps, weight[mask]
                hist[f'{classifier}_ps_{bb}'].fill(dataset=dataset, x=x, weight=w)

            mask = event[classifier]['zz'] | event[classifier]['zh'] | event[classifier]['hh']
            x, w = event[mask][classifier].ps, weight[mask]
            hist[f'{classifier}_ps_all'].fill(dataset=dataset, x=x, weight=w)


    def fill_fourvectorhists(self, name, hist, event, weight):
        dataset = event.metadata.get('dataset','')
        namepath = tuple(name.split('.'))

        obj = event
        for p in namepath:
            obj = obj[p]
        _, w = ak.broadcast_arrays(obj.pt, weight)#, depth_limit=1) # duplicate event weights so that we can fill with multiple objects per event
        try:
            w = ak.flatten(w) # flatten arrays for filling, allows for multiple objects per event
        except ValueError:
            pass

        for var in ['pt','eta','phi','mass', 'pz','energy','dr','st']:
            try:
                v = getattr(obj,var)
            except AttributeError:
                # print('AttributeError',name,var)
                continue # var attribute was not initialized
            try:
                v = ak.flatten(v)
            except ValueError:
                # print('flatten error',v)
                pass # already flat?

            try:
                hist[f'{name}.{var}'].fill(dataset=dataset, x=v, weight=w)
            except KeyError:
                # print('KeyError', f'{name}.{var}')
                pass # histogram for this attribute was not initialized


    def fill(self, event, output, junc='JES_Central'):
        dataset = event.metadata.get('dataset','')
        for cut in self.cuts:
            for tag in self.tags:
                mask_cut_tag = event[tag] & event[cut]
                for region in self.regions:
                    if   region == 'SBSR':
                        mask = mask_cut_tag & (event['quadJet_selected'].SB | event['quadJet_selected'].SR)
                    elif region == 'SB':
                        mask = mask_cut_tag & event['quadJet_selected'].SB
                    elif region == 'SR':
                        mask = mask_cut_tag & event['quadJet_selected'].SR
                    elif region == 'inclusive':
                        mask = mask_cut_tag

                    hist_event = event[mask]
                    weight = hist_event.weight
                    if self.apply_trigWeight:
                        weight = weight * hist_event.trigWeight.Data

                    hist = output['hists'][junc][cut][tag][region]
                    hist['nJet_selected'].fill(dataset=dataset, x=hist_event.nJet_selected, weight=weight)
                    #hist['canJet_pt'].fill(dataset=dataset, x=hist_event.canJet.pt, weight=weight)
                    self.fill_fourvectorhists('canJet', hist, hist_event, weight)
                    self.fill_fourvectorhists('v4j', hist, hist_event, weight)
                    self.fill_fourvectorhists('quadJet_selected.lead', hist, hist_event, weight)
                    self.fill_fourvectorhists('quadJet_selected.subl', hist, hist_event, weight)
                    hist['quadJet_selected.dr'].fill(dataset=dataset, x=hist_event['quadJet_selected'].dr, weight=weight)
                    for bb in self.signals: hist[f'quadJet_selected.x{bb.upper()}'].fill(dataset=dataset, x=hist_event['quadJet_selected'][f'x{bb.upper()}'], weight=weight)
                    self.fill_SvB(hist, hist_event, weight)

    # def fill_shh(self, output, event, dataset='', cut='', tag='', region=''):
    #     output['hists']['SvB_ps_zz_nJet_selected'].fill(
    #         dataset=dataset, cut=cut, tag=tag, region=region, SvB_largest=event.SvB.largest,
    #         SvB_ps=event.SvB.ps, nJet_selected=event.nJet_selected, weight=event.weight)

    def fill_systematics(self, event, output, junc='JES_Central'):
        mask = event['fourTag']
        mask = mask & event['quadJet_selected'].SR
        event = event[mask]

        for trig in ['Bool', 'MC', 'Data']:
            hist = output['hists'][junc]['passPreSel']['fourTag']['SR'][f'trigWeight_{trig}']
            weight = event.weight * event.passHLT if trig == 'Bool' else event.weight * event.trigWeight[trig]
            self.fill_SvB(hist, event, weight)

        for sf in self.btagVar:
            hist = output['hists'][junc]['passPreSel']['fourTag']['SR'][f'btagSF_{sf}']
            weight = event[f'weight_btagSF_{sf}']
            if self.apply_trigWeight:
                weight = weight * event.trigWeight.Data
            self.fill_SvB(hist, event, weight)

        if self.apply_puWeight:
            hist = output['hists'][junc]['passPreSel']['fourTag']['SR']['puWeight_unit']
            unit_weight = event.weight#/event.PU_weight_nominal # this will break if any nominal pilup weights are zero
            if self.apply_trigWeight:
                unit_weight = unit_weight * event.trigWeight.Data
            self.fill_SvB(hist, event, unit_weight)
            branch = {'up': 'up', 'down':'down', 'central': 'nominal'}
            for var in branch:
                hist = output['hists'][junc]['passPreSel']['fourTag']['SR'][f'puWeight_{var}']
                weight = unit_weight * event[f'PU_weight_{branch[var]}']
                self.fill_SvB(hist, event, weight)

        if self.apply_prefire:
            hist = output['hists'][junc]['passPreSel']['fourTag']['SR']['prefire_unit']
            unit_weight = event.weight#/event.L1PreFiringWeight.Nom # this will break if any nominal prefire weights are zero
            if self.apply_trigWeight:
                unit_weight = unit_weight * event.trigWeight.Data
            self.fill_SvB(hist, event, unit_weight)
            branch = {'up': 'Up', 'down':'Dn', 'central': 'Nom'}
            for var in branch:
                hist = output['hists'][junc]['passPreSel']['fourTag']['SR'][f'prefire_{var}']
                weight = unit_weight * event.L1PreFiringWeight[branch[var]]
                self.fill_SvB(hist, event, weight)


    def postprocess(self, accumulator):
        return accumulator

