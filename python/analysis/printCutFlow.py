import os, sys
import yaml
import hist
import argparse
#matplotlib.use('Agg')
import matplotlib.pyplot as plt
from coffea.util import load
from hist.intervals import ratio_uncertainty


def _round(val):
    return round(float(val),1)
    

def printLine(words):
    print(f'\t{words[0]:<20}\t{words[1]:<10}   {words[2]:<10} \t\t {words[3]:<10}\t{words[4]:<10}')

def printCF(procKey, cf4, cf4_unit, cf3, cf3_unit):


    bar = "-"*10
    print('\n')
    print(procKey,':\n')
    printLine(["Cuts","FourTag","","ThreeTag",""])
    printLine(["",bar,bar,bar,bar])
    printLine(["","weighted","(unit weight)","weighted","(unit weight)"])
    print('\n')
    for cut in cf4.keys():
        printLine([cut,_round(cf4[cut]),_round(cf4_unit[cut]),_round(cf3[cut]),_round(cf3_unit[cut])])
                   
    print("\n")

    

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='uproot_plots')
    parser.add_argument('-i','--inputFile', default='hists.pkl', help='Input File. Default: hists.pkl')
    parser.add_argument('-p','--process',   default='data', help='Input process. Default: hists.pkl')
    parser.add_argument('-e','--era',   nargs='+', dest='eras', default=['UL17C'], help='Input process. Default: hists.pkl')
    #parser.add_argument('-d', '--datasets', nargs='+', dest='datasets', , help="Name of dataset to run. Example if more than one: -d HH4b ZZ4b")
    #parser.add_argument('-p','--process',   default='data', help='Input process. Default: hists.pkl')
    args = parser.parse_args()

    

    with open(f'{args.inputFile}', 'rb') as hfile:
        hists = load(hfile)
        
    cf4      = hists["cutFlowFourTag"]
    cf4_unit = hists["cutFlowFourTagUnitWeight"]
    cf3      = hists["cutFlowThreeTag"]
    cf3_unit = hists["cutFlowThreeTagUnitWeight"]

        #process = "data"
    #era = "UL17F"

    eras = args.eras
    eraString = " ".join(eras)
    print(eras)
    print(eraString)

    for e in eras:
        key = args.process+"_"+e
    
        #cutList = hists["cutFlowThreeTagUnitWeight"][key].keys()
        printCF(key, cf4[key], cf4_unit[key], cf3[key], cf3_unit[key])
