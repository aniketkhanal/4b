import awkward as ak
import numpy as np
from coffea.nanoevents import NanoEventsFactory, NanoAODSchema, BaseSchema
NanoAODSchema.warn_missing_crossrefs = False
import warnings
warnings.filterwarnings("ignore")
from coffea.nanoevents.methods import vector
ak.behavior.update(vector.behavior)
from coffea import processor, util
import correctionlib
import cachetools
import logging
import copy

# following example here: https://github.com/CoffeaTeam/coffea/blob/master/tests/test_jetmet_tools.py#L529
def init_jet_factory(weight_sets, event):   #### AGE: this is temporary, it should be updated with correctionlib

    event['Jet', 'pt_raw']    = (1 - event.Jet.rawFactor) * event.Jet.pt
    event['Jet', 'mass_raw']  = (1 - event.Jet.rawFactor) * event.Jet.mass
    nominal_jet = event.Jet
    # nominal_jet['pt_raw']   = (1 - nominal_jet.rawFactor) * nominal_jet.pt
    # nominal_jet['mass_raw'] = (1 - nominal_jet.rawFactor) * nominal_jet.mass
    nominal_jet['pt_gen'] = ak.values_astype(ak.fill_none(nominal_jet.matched_gen.pt, 0), np.float32)
    nominal_jet['rho']      = ak.broadcast_arrays(event.fixedGridRhoFastjetAll, nominal_jet.pt)[0]

    from coffea.lookup_tools import extractor
    extract = extractor()
    extract.add_weight_sets(weight_sets)
    extract.finalize()
    evaluator = extract.make_evaluator()

    from coffea.jetmet_tools import CorrectedJetsFactory, CorrectedMETFactory, JECStack, JetResolution, JetResolutionScaleFactor
    jec_stack_names = []
    for key in evaluator.keys():
        jec_stack_names.append(key)
        if 'UncertaintySources' in key:
            jec_stack_names.append(key)

    # print(jec_stack_names)
    jec_inputs = {name: evaluator[name] for name in jec_stack_names}
    # print('jec_inputs:')
    # print(jec_inputs)
    jec_stack = JECStack(jec_inputs)
    # print('jec_stack')
    # print(jec_stack.__dict__)
    name_map = jec_stack.blank_name_map
    name_map["JetPt"]    = "pt"
    name_map["JetMass"]  = "mass"
    name_map["JetEta"]   = "eta"
    name_map["JetA"]     = "area"
    name_map['ptGenJet'] = 'pt_gen'
    name_map['ptRaw']    = 'pt_raw'
    name_map['massRaw']  = 'mass_raw'
    name_map['Rho']      = 'rho'
    # print(name_map)

    jet_factory = CorrectedJetsFactory(name_map, jec_stack)
    uncertainties = jet_factory.uncertainties()
    if uncertainties:
        for unc in uncertainties:
            logging.debug(unc)
    else:
        logging.warning('WARNING: No uncertainties were loaded in the jet factory')

    jec_cache = cachetools.Cache(np.inf)
    jet_variations = jet_factory.build(nominal_jet, lazy_cache=jec_cache)

    return jet_variations

##### JER needs to be included
def jet_corrections( uncorrJets,
                    fixedGridRhoFastjetAll,
                    jercFile="/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/JME/2018_UL/jet_jerc.json.gz",
                    data_campaign="Summer19UL18",
                    jec_campaign='V5_MC',
                    jer_campaign='JRV2_MC',
                    jec_type=["L1L2L3Res"],  ####, "PtResolution", 'ScaleFactor'
                    jettype='AK4PFchs',
                    variation='nom'
                    ):

    JECFile = correctionlib.CorrectionSet.from_file(jercFile)
    # preparing jets
    uncorrJets['pt_raw'] = (1 - uncorrJets['rawFactor']) * uncorrJets['pt']
    uncorrJets['rho'] = ak.broadcast_arrays(fixedGridRhoFastjetAll, uncorrJets.pt)[0]
    j, nj = ak.flatten(uncorrJets), ak.num(uncorrJets)

    total_flat_jec = np.ones( len(j) )
    for ijec in jec_type:

        if 'L1' in ijec:
            corr = JECFile.compound[f'{data_campaign}_{jec_campaign}_{ijec}_{jettype}'] if 'L1L2L3' in ijec else JECFile[f'{data_campaign}_{jec_campaign}_{ijec}_{jettype}']
            flat_jec = corr.evaluate( j['area'], j['eta'], j['pt_raw'], j['rho']  )
        else:
            if 'PtResolution' in ijec:
                corr = JECFile[f'{data_campaign}_{jer_campaign}_{ijec}_{jettype}']
                flat_jec = corr.evaluate( j['eta'], j['pt_raw'], j['rho'] )   ###### AGE: to check, I think pt has to be after corrections
            elif 'ScaleFactor' in ijec:
                corr = JECFile[f'{data_campaign}_{jer_campaign}_{ijec}_{jettype}']
                flat_jec = corr.evaluate( j['eta'], variation )
            else:
                corr = JECFile[f'{data_campaign}_{jec_campaign}_{ijec}_{jettype}']
                flat_jec = corr.evaluate( j['eta'], j['pt_raw']  )
        total_flat_jec *= flat_jec
    jec = ak.unflatten(total_flat_jec, nj)

    #correctP4Jets = uncorrJets * jec
    correctJets = copy.deepcopy(uncorrJets)
    correctJets['jet_energy_correction'] = jec
    correctJets['pt'] = correctJets.pt_raw * jec
    correctJets['mass'] = correctJets.mass_raw * jec

    return correctJets


def mask_event_decision(event, decision='OR', branch='HLT', list_to_mask=[''], list_to_skip=['']):
    '''
    Takes event.branch and passes an boolean array mask with the decisions of all the list_to_mask
    '''

    tmp_list = []
    if branch in event.fields:
        for i in list_to_mask:
            if i in event[branch].fields:
                tmp_list.append( event[branch][i] )
            elif i in list_to_skip: continue
            else: logging.warning(f'\n{i} branch not in {branch} for event.')
    else: logging.warning(f'\n{branch} branch not in event.')
    tmp_array = np.array( tmp_list )

    if decision.lower().startswith('or'): decision_array = np.any( tmp_array, axis=0 )
    else: decision_array = np.all( tmp_array, axis=0 )

    return decision_array

def apply_btag_sf( events, jets,
                  correction_file='data/JEC/BTagSF2016/btagging_legacy16_deepJet_itFit.json.gz',
                  correction_type="deepJet_shape",
                  btag_var=['central'],
                  btagSF_norm=1.,
                  weight=1.,
                  ):
    '''
    This nees a work to make it more generic
    '''

    btagSF = correctionlib.CorrectionSet.from_file(correction_file)[correction_type]

    selev = {}
    #central = 'central'
    use_central = True
    btag_jes = []
    cj, nj = ak.flatten(jets), ak.num(jets)
    hf, eta, pt, tag = np.array(cj.hadronFlavour), np.array(abs(cj.eta)), np.array(cj.pt), np.array(cj.btagDeepFlavB)

    cj_bl = jets[jets.hadronFlavour!=4]
    nj_bl = ak.num(cj_bl)
    cj_bl = ak.flatten(cj_bl)
    hf_bl, eta_bl, pt_bl, tag_bl = np.array(cj_bl.hadronFlavour), np.array(abs(cj_bl.eta)), np.array(cj_bl.pt), np.array(cj_bl.btagDeepFlavB)
    SF_bl= btagSF.evaluate('central', hf_bl, eta_bl, pt_bl, tag_bl)
    SF_bl = ak.unflatten(SF_bl, nj_bl)
    SF_bl = np.prod(SF_bl, axis=1)

    cj_c = jets[jets.hadronFlavour==4]
    nj_c = ak.num(cj_c)
    cj_c = ak.flatten(cj_c)
    hf_c, eta_c, pt_c, tag_c = np.array(cj_c.hadronFlavour), np.array(abs(cj_c.eta)), np.array(cj_c.pt), np.array(cj_c.btagDeepFlavB)
    SF_c= btagSF.evaluate('central', hf_c, eta_c, pt_c, tag_c)
    SF_c = ak.unflatten(SF_c, nj_c)
    SF_c = np.prod(SF_c, axis=1)

    for sf in btag_var+btag_jes:
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
        selev[f'weight_btagSF_{sf}'] = weight * SF * btagSF_norm

    return selev[f'weight_btagSF_{"central" if use_central else btag_jes[0]}']


def drClean(coll1,coll2,cone=0.4):

    from coffea.nanoevents.methods import vector
    j_eta = coll1.eta
    j_phi = coll1.phi
    l_eta = coll2.eta
    l_phi = coll2.phi

    j_eta, l_eta = ak.unzip(ak.cartesian([j_eta, l_eta], nested=True))
    j_phi, l_phi = ak.unzip(ak.cartesian([j_phi, l_phi], nested=True))
    delta_eta = j_eta - l_eta
    delta_phi = vector._deltaphi_kernel(j_phi,l_phi)
    dr = np.hypot(delta_eta, delta_phi)
    nolepton_mask = ~ak.any(dr < cone, axis=2)
    jets_noleptons = coll1[nolepton_mask]
    return [jets_noleptons, nolepton_mask]

