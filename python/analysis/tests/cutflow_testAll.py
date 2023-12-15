import unittest
from coffea.util import load

class CutFlowTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(self):

        inputFile = "hists/histAll.coffea"
        with open(f'{inputFile}', 'rb') as hfile:
            hists = load(hfile)
        
        self.cf4      = hists["cutFlowFourTag"]
        self.cf4_unit = hists["cutFlowFourTagUnitWeight"]
        self.cf3      = hists["cutFlowThreeTag"]
        self.cf3_unit = hists["cutFlowThreeTagUnitWeight"]

        #  Make these numbers with:
        #  >  python     analysis/tests/dumpCutFlow.py  -i hists/histAll.coffea  
        #
        self.counts4 = {}
        self.counts4['data_UL18D'] = {'passJetMult' : 1874829.0, 'passPreSel' : 70684.0, 'passDiJetMass' : 29608.0, 'SR' : 11081.0, 'SB' : 18527.0, 'passSvB' : 56.0, 'failSvB' : 41737.0, }
        self.counts4['data_UL18C'] = {'passJetMult' : 418436.0, 'passPreSel' : 15758.0, 'passDiJetMass' : 6560.0, 'SR' : 2430.0, 'SB' : 4130.0, 'passSvB' : 9.0, 'failSvB' : 9337.0, }
        self.counts4['data_UL18B'] = {'passJetMult' : 448667.0, 'passPreSel' : 16933.0, 'passDiJetMass' : 7028.0, 'SR' : 2648.0, 'SB' : 4380.0, 'passSvB' : 8.0, 'failSvB' : 10048.0, }
        self.counts4['data_UL18A'] = {'passJetMult' : 902005.0, 'passPreSel' : 34344.0, 'passDiJetMass' : 14465.0, 'SR' : 5486.0, 'SB' : 8979.0, 'passSvB' : 27.0, 'failSvB' : 20510.0, }
        self.counts4['data_UL17F'] = {'passJetMult' : 710245.0, 'passPreSel' : 27712.0, 'passDiJetMass' : 12225.0, 'SR' : 4478.0, 'SB' : 7747.0, 'passSvB' : 14.0, 'failSvB' : 15810.0, }
        self.counts4['data_UL17E'] = {'passJetMult' : 549026.0, 'passPreSel' : 26873.0, 'passDiJetMass' : 12165.0, 'SR' : 4308.0, 'SB' : 7857.0, 'passSvB' : 14.0, 'failSvB' : 15622.0, }
        self.counts4['data_UL17D'] = {'passJetMult' : 234161.0, 'passPreSel' : 12959.0, 'passDiJetMass' : 5904.0, 'SR' : 2065.0, 'SB' : 3839.0, 'passSvB' : 7.0, 'failSvB' : 7372.0, }
        self.counts4['data_UL17C'] = {'passJetMult' : 498557.0, 'passPreSel' : 26897.0, 'passDiJetMass' : 12237.0, 'SR' : 4424.0, 'SB' : 7813.0, 'passSvB' : 12.0, 'failSvB' : 15156.0, }
        self.counts4['data_UL16_preVFPE'] = {'passJetMult' : 395976.0, 'passPreSel' : 9779.0, 'passDiJetMass' : 4964.0, 'SR' : 1810.0, 'SB' : 3154.0, 'passSvB' : 2.0, 'failSvB' : 5762.0, }
        self.counts4['data_UL16_preVFPD'] = {'passJetMult' : 421098.0, 'passPreSel' : 11270.0, 'passDiJetMass' : 5909.0, 'SR' : 2115.0, 'SB' : 3794.0, 'passSvB' : 9.0, 'failSvB' : 6595.0, }
        self.counts4['data_UL16_preVFPC'] = {'passJetMult' : 256268.0, 'passPreSel' : 7263.0, 'passDiJetMass' : 3721.0, 'SR' : 1344.0, 'SB' : 2377.0, 'passSvB' : 4.0, 'failSvB' : 4229.0, }
        self.counts4['data_UL16_preVFPB'] = {'passJetMult' : 598690.0, 'passPreSel' : 17900.0, 'passDiJetMass' : 9211.0, 'SR' : 3424.0, 'SB' : 5787.0, 'passSvB' : 15.0, 'failSvB' : 10432.0, }
        self.counts4['data_UL16_postVFPH'] = {'passJetMult' : 903644.0, 'passPreSel' : 24327.0, 'passDiJetMass' : 12698.0, 'SR' : 4676.0, 'SB' : 8022.0, 'passSvB' : 16.0, 'failSvB' : 14548.0, }
        self.counts4['data_UL16_postVFPG'] = {'passJetMult' : 877903.0, 'passPreSel' : 22800.0, 'passDiJetMass' : 12090.0, 'SR' : 4439.0, 'SB' : 7651.0, 'passSvB' : 11.0, 'failSvB' : 13699.0, }
        self.counts4['data_UL16_postVFPF'] = {'passJetMult' : 311677.0, 'passPreSel' : 7731.0, 'passDiJetMass' : 3964.0, 'SR' : 1449.0, 'SB' : 2515.0, 'passSvB' : 6.0, 'failSvB' : 4549.0, }
        self.counts4['ZZ4b_UL18'] = {'passJetMult' : 142.32, 'passPreSel' : 26.35, 'passDiJetMass' : 21.9, 'SR' : 17.9, 'SB' : 4.0, 'passSvB' : 1.49, 'failSvB' : 2.28, }
        self.counts4['ZZ4b_UL17'] = {'passJetMult' : 93.05, 'passPreSel' : 18.4, 'passDiJetMass' : 15.66, 'SR' : 12.69, 'SB' : 2.97, 'passSvB' : 0.85, 'failSvB' : 1.39, }
        self.counts4['ZZ4b_UL16_preVFP'] = {'passJetMult' : 80.04, 'passPreSel' : 9.4, 'passDiJetMass' : 8.17, 'SR' : 6.29, 'SB' : 1.88, 'passSvB' : 0.39, 'failSvB' : 0.75, }
        self.counts4['ZZ4b_UL16_postVFP'] = {'passJetMult' : 70.75, 'passPreSel' : 7.77, 'passDiJetMass' : 6.78, 'SR' : 5.4, 'SB' : 1.37, 'passSvB' : 0.34, 'failSvB' : 0.58, }
        self.counts4['ZH4b_UL18'] = {'passJetMult' : 76.22, 'passPreSel' : 19.76, 'passDiJetMass' : 17.83, 'SR' : 15.14, 'SB' : 2.69, 'passSvB' : 1.9, 'failSvB' : 0.97, }
        self.counts4['ZH4b_UL17'] = {'passJetMult' : 51.25, 'passPreSel' : 13.97, 'passDiJetMass' : 12.77, 'SR' : 10.66, 'SB' : 2.11, 'passSvB' : 1.16, 'failSvB' : 0.62, }
        self.counts4['ZH4b_UL16_preVFP'] = {'passJetMult' : 43.17, 'passPreSel' : 7.25, 'passDiJetMass' : 6.73, 'SR' : 5.46, 'SB' : 1.27, 'passSvB' : 0.58, 'failSvB' : 0.3, }
        self.counts4['ZH4b_UL16_postVFP'] = {'passJetMult' : 38.6, 'passPreSel' : 6.13, 'passDiJetMass' : 5.69, 'SR' : 4.71, 'SB' : 0.98, 'passSvB' : 0.5, 'failSvB' : 0.25, }
        self.counts4['TTToSemiLeptonic_UL18'] = {'passJetMult' : 89422.91, 'passPreSel' : 2517.32, 'passDiJetMass' : 919.62, 'SR' : 369.81, 'SB' : 549.81, 'passSvB' : 0.9, 'failSvB' : 1534.04, }
        self.counts4['TTToSemiLeptonic_UL17'] = {'passJetMult' : 62256.59, 'passPreSel' : 1609.63, 'passDiJetMass' : 643.75, 'SR' : 258.51, 'SB' : 385.24, 'passSvB' : 0.42, 'failSvB' : 912.9, }
        self.counts4['TTToSemiLeptonic_UL16_preVFP'] = {'passJetMult' : 49005.55, 'passPreSel' : 686.6, 'passDiJetMass' : 294.45, 'SR' : 120.3, 'SB' : 174.15, 'passSvB' : 0.18, 'failSvB' : 379.58, }
        self.counts4['TTToSemiLeptonic_UL16_postVFP'] = {'passJetMult' : 45398.66, 'passPreSel' : 612.33, 'passDiJetMass' : 262.27, 'SR' : 108.29, 'SB' : 153.99, 'passSvB' : 0.17, 'failSvB' : 337.57, }
        self.counts4['TTToHadronic_UL18'] = {'passJetMult' : 175535.22, 'passPreSel' : 3738.85, 'passDiJetMass' : 1641.36, 'SR' : 736.58, 'SB' : 904.77, 'passSvB' : 1.93, 'failSvB' : 1950.99, }
        self.counts4['TTToHadronic_UL17'] = {'passJetMult' : 120751.67, 'passPreSel' : 2415.84, 'passDiJetMass' : 1154.62, 'SR' : 531.85, 'SB' : 622.78, 'passSvB' : 1.27, 'failSvB' : 1125.91, }
        self.counts4['TTToHadronic_UL16_preVFP'] = {'passJetMult' : 95839.33, 'passPreSel' : 1005.02, 'passDiJetMass' : 509.51, 'SR' : 238.17, 'SB' : 271.34, 'passSvB' : 0.86, 'failSvB' : 443.15, }
        self.counts4['TTToHadronic_UL16_postVFP'] = {'passJetMult' : 89935.62, 'passPreSel' : 903.78, 'passDiJetMass' : 466.09, 'SR' : 218.56, 'SB' : 247.53, 'passSvB' : 0.4, 'failSvB' : 400.5, }
        self.counts4['TTTo2L2Nu_UL18'] = {'passJetMult' : 9646.78, 'passPreSel' : 432.38, 'passDiJetMass' : 142.77, 'SR' : 53.36, 'SB' : 89.42, 'passSvB' : 0.13, 'failSvB' : 280.05, }
        self.counts4['TTTo2L2Nu_UL17'] = {'passJetMult' : 6630.64, 'passPreSel' : 278.82, 'passDiJetMass' : 99.3, 'SR' : 37.27, 'SB' : 62.03, 'passSvB' : 0.02, 'failSvB' : 173.02, }
        self.counts4['TTTo2L2Nu_UL16_preVFP'] = {'passJetMult' : 5033.51, 'passPreSel' : 115.91, 'passDiJetMass' : 43.52, 'SR' : 17.22, 'SB' : 26.3, 'passSvB' : 0.09, 'failSvB' : 72.18, }
        self.counts4['TTTo2L2Nu_UL16_postVFP'] = {'passJetMult' : 4612.85, 'passPreSel' : 106.44, 'passDiJetMass' : 41.84, 'SR' : 15.99, 'SB' : 25.85, 'passSvB' : 0.08, 'failSvB' : 65.06, }
        self.counts4['HH4b_UL18'] = {'passJetMult' : 62.77, 'passPreSel' : 15.77, 'passDiJetMass' : 13.97, 'SR' : 12.42, 'SB' : 1.55, 'passSvB' : 2.18, 'failSvB' : 0.87, }
        self.counts4['HH4b_UL17'] = {'passJetMult' : 38.09, 'passPreSel' : 11.1, 'passDiJetMass' : 10.03, 'SR' : 8.73, 'SB' : 1.29, 'passSvB' : 1.31, 'failSvB' : 0.52, }
        self.counts4['HH4b_UL16_preVFP'] = {'passJetMult' : 36.59, 'passPreSel' : 6.17, 'passDiJetMass' : 5.47, 'SR' : 4.74, 'SB' : 0.73, 'passSvB' : 0.54, 'failSvB' : 0.36, }
        
        
        
        self.counts3 = {}
        self.counts3['data_UL18D'] = {'passJetMult' : 1874829.0, 'passPreSel' : 64692.98, 'passDiJetMass' : 28721.12, 'SR' : 10774.45, 'SB' : 17946.67, 'passSvB' : 50.74, 'failSvB' : 37086.26, }
        self.counts3['data_UL18C'] = {'passJetMult' : 418436.0, 'passPreSel' : 14210.12, 'passDiJetMass' : 6275.64, 'SR' : 2365.46, 'SB' : 3910.19, 'passSvB' : 11.69, 'failSvB' : 8213.24, }
        self.counts3['data_UL18B'] = {'passJetMult' : 448667.0, 'passPreSel' : 15303.97, 'passDiJetMass' : 6769.79, 'SR' : 2559.56, 'SB' : 4210.24, 'passSvB' : 12.32, 'failSvB' : 8846.63, }
        self.counts3['data_UL18A'] = {'passJetMult' : 902005.0, 'passPreSel' : 30629.04, 'passDiJetMass' : 13741.92, 'SR' : 5190.21, 'SB' : 8551.71, 'passSvB' : 20.62, 'failSvB' : 17870.46, }
        self.counts3['data_UL17F'] = {'passJetMult' : 710245.0, 'passPreSel' : 30096.13, 'passDiJetMass' : 14370.95, 'SR' : 5225.04, 'SB' : 9145.91, 'passSvB' : 16.79, 'failSvB' : 16819.3, }
        self.counts3['data_UL17E'] = {'passJetMult' : 549026.0, 'passPreSel' : 22916.16, 'passDiJetMass' : 11071.62, 'SR' : 4000.58, 'SB' : 7071.04, 'passSvB' : 12.21, 'failSvB' : 12947.61, }
        self.counts3['data_UL17D'] = {'passJetMult' : 234161.0, 'passPreSel' : 10307.41, 'passDiJetMass' : 4987.56, 'SR' : 1769.52, 'SB' : 3218.04, 'passSvB' : 5.14, 'failSvB' : 5698.53, }
        self.counts3['data_UL17C'] = {'passJetMult' : 498557.0, 'passPreSel' : 21919.59, 'passDiJetMass' : 10567.7, 'SR' : 3784.13, 'SB' : 6783.57, 'passSvB' : 15.72, 'failSvB' : 12086.04, }
        self.counts3['data_UL16_preVFPE'] = {'passJetMult' : 395976.0, 'passPreSel' : 9943.53, 'passDiJetMass' : 5239.36, 'SR' : 1875.15, 'SB' : 3364.21, 'passSvB' : 5.99, 'failSvB' : 5877.92, }
        self.counts3['data_UL16_preVFPD'] = {'passJetMult' : 421098.0, 'passPreSel' : 10871.49, 'passDiJetMass' : 5832.4, 'SR' : 2110.23, 'SB' : 3722.17, 'passSvB' : 7.96, 'failSvB' : 6404.97, }
        self.counts3['data_UL16_preVFPC'] = {'passJetMult' : 256268.0, 'passPreSel' : 6541.45, 'passDiJetMass' : 3501.78, 'SR' : 1270.08, 'SB' : 2231.7, 'passSvB' : 4.01, 'failSvB' : 3854.62, }
        self.counts3['data_UL16_preVFPB'] = {'passJetMult' : 598690.0, 'passPreSel' : 15419.77, 'passDiJetMass' : 8212.07, 'SR' : 2951.21, 'SB' : 5260.86, 'passSvB' : 12.62, 'failSvB' : 9018.74, }
        self.counts3['data_UL16_postVFPH'] = {'passJetMult' : 903644.0, 'passPreSel' : 22182.67, 'passDiJetMass' : 12038.8, 'SR' : 4399.45, 'SB' : 7639.35, 'passSvB' : 11.56, 'failSvB' : 13194.55, }
        self.counts3['data_UL16_postVFPG'] = {'passJetMult' : 877903.0, 'passPreSel' : 21786.44, 'passDiJetMass' : 11875.46, 'SR' : 4318.62, 'SB' : 7556.84, 'passSvB' : 11.81, 'failSvB' : 13001.24, }
        self.counts3['data_UL16_postVFPF'] = {'passJetMult' : 311677.0, 'passPreSel' : 7745.42, 'passDiJetMass' : 4123.27, 'SR' : 1497.43, 'SB' : 2625.84, 'passSvB' : 4.62, 'failSvB' : 4600.36, }
        self.counts3['ZZ4b_UL18'] = {'passJetMult' : 142.32, 'passPreSel' : 4.75, 'passDiJetMass' : 3.05, 'SR' : 2.1, 'SB' : 0.95, 'passSvB' : 0.15, 'failSvB' : 0.78, }
        self.counts3['ZZ4b_UL17'] = {'passJetMult' : 93.05, 'passPreSel' : 3.8, 'passDiJetMass' : 2.58, 'SR' : 1.71, 'SB' : 0.87, 'passSvB' : 0.1, 'failSvB' : 0.59, }
        self.counts3['ZZ4b_UL16_preVFP'] = {'passJetMult' : 80.04, 'passPreSel' : 2.37, 'passDiJetMass' : 1.69, 'SR' : 1.06, 'SB' : 0.63, 'passSvB' : 0.06, 'failSvB' : 0.41, }
        self.counts3['ZZ4b_UL16_postVFP'] = {'passJetMult' : 70.75, 'passPreSel' : 1.93, 'passDiJetMass' : 1.36, 'SR' : 0.89, 'SB' : 0.48, 'passSvB' : 0.05, 'failSvB' : 0.34, }
        self.counts3['ZH4b_UL18'] = {'passJetMult' : 76.22, 'passPreSel' : 2.38, 'passDiJetMass' : 1.79, 'SR' : 1.31, 'SB' : 0.48, 'passSvB' : 0.15, 'failSvB' : 0.3, }
        self.counts3['ZH4b_UL17'] = {'passJetMult' : 51.25, 'passPreSel' : 1.89, 'passDiJetMass' : 1.47, 'SR' : 1.05, 'SB' : 0.42, 'passSvB' : 0.09, 'failSvB' : 0.22, }
        self.counts3['ZH4b_UL16_preVFP'] = {'passJetMult' : 43.17, 'passPreSel' : 1.22, 'passDiJetMass' : 0.98, 'SR' : 0.68, 'SB' : 0.3, 'passSvB' : 0.07, 'failSvB' : 0.16, }
        self.counts3['ZH4b_UL16_postVFP'] = {'passJetMult' : 38.6, 'passPreSel' : 1.02, 'passDiJetMass' : 0.81, 'SR' : 0.57, 'SB' : 0.24, 'passSvB' : 0.05, 'failSvB' : 0.13, }
        self.counts3['TTToSemiLeptonic_UL18'] = {'passJetMult' : 89422.91, 'passPreSel' : 3087.76, 'passDiJetMass' : 1862.51, 'SR' : 881.28, 'SB' : 981.23, 'passSvB' : 10.48, 'failSvB' : 1103.53, }
        self.counts3['TTToSemiLeptonic_UL17'] = {'passJetMult' : 62256.59, 'passPreSel' : 2372.81, 'passDiJetMass' : 1554.74, 'SR' : 728.89, 'SB' : 825.84, 'passSvB' : 6.53, 'failSvB' : 753.24, }
        self.counts3['TTToSemiLeptonic_UL16_preVFP'] = {'passJetMult' : 49005.55, 'passPreSel' : 1209.05, 'passDiJetMass' : 797.57, 'SR' : 374.27, 'SB' : 423.3, 'passSvB' : 3.78, 'failSvB' : 407.16, }
        self.counts3['TTToSemiLeptonic_UL16_postVFP'] = {'passJetMult' : 45398.66, 'passPreSel' : 1120.68, 'passDiJetMass' : 744.18, 'SR' : 350.57, 'SB' : 393.61, 'passSvB' : 3.04, 'failSvB' : 382.09, }
        self.counts3['TTToHadronic_UL18'] = {'passJetMult' : 175535.22, 'passPreSel' : 6388.37, 'passDiJetMass' : 4367.53, 'SR' : 2226.22, 'SB' : 2141.32, 'passSvB' : 14.38, 'failSvB' : 1852.65, }
        self.counts3['TTToHadronic_UL17'] = {'passJetMult' : 120751.67, 'passPreSel' : 4975.54, 'passDiJetMass' : 3599.24, 'SR' : 1823.25, 'SB' : 1775.99, 'passSvB' : 9.29, 'failSvB' : 1255.54, }
        self.counts3['TTToHadronic_UL16_preVFP'] = {'passJetMult' : 95839.33, 'passPreSel' : 2540.12, 'passDiJetMass' : 1892.87, 'SR' : 991.5, 'SB' : 901.37, 'passSvB' : 5.5, 'failSvB' : 642.28, }
        self.counts3['TTToHadronic_UL16_postVFP'] = {'passJetMult' : 89935.62, 'passPreSel' : 2347.39, 'passDiJetMass' : 1755.45, 'SR' : 919.11, 'SB' : 836.34, 'passSvB' : 4.36, 'failSvB' : 600.74, }
        self.counts3['TTTo2L2Nu_UL18'] = {'passJetMult' : 9646.78, 'passPreSel' : 348.8, 'passDiJetMass' : 183.8, 'SR' : 81.98, 'SB' : 101.82, 'passSvB' : 1.98, 'failSvB' : 143.9, }
        self.counts3['TTTo2L2Nu_UL17'] = {'passJetMult' : 6630.64, 'passPreSel' : 258.96, 'passDiJetMass' : 150.82, 'SR' : 65.74, 'SB' : 85.08, 'passSvB' : 1.18, 'failSvB' : 97.57, }
        self.counts3['TTTo2L2Nu_UL16_preVFP'] = {'passJetMult' : 5033.51, 'passPreSel' : 126.76, 'passDiJetMass' : 71.83, 'SR' : 30.35, 'SB' : 41.48, 'passSvB' : 0.51, 'failSvB' : 51.65, }
        self.counts3['TTTo2L2Nu_UL16_postVFP'] = {'passJetMult' : 4612.85, 'passPreSel' : 118.08, 'passDiJetMass' : 67.31, 'SR' : 29.17, 'SB' : 38.13, 'passSvB' : 0.53, 'failSvB' : 48.77, }
        self.counts3['HH4b_UL18'] = {'passJetMult' : 62.77, 'passPreSel' : 1.91, 'passDiJetMass' : 1.3, 'SR' : 1.02, 'SB' : 0.27, 'passSvB' : 0.17, 'failSvB' : 0.34, }
        self.counts3['HH4b_UL17'] = {'passJetMult' : 38.09, 'passPreSel' : 1.39, 'passDiJetMass' : 0.97, 'SR' : 0.74, 'SB' : 0.23, 'passSvB' : 0.1, 'failSvB' : 0.23, }
        self.counts3['HH4b_UL16_preVFP'] = {'passJetMult' : 36.59, 'passPreSel' : 0.85, 'passDiJetMass' : 0.59, 'SR' : 0.43, 'SB' : 0.16, 'passSvB' : 0.05, 'failSvB' : 0.15, }


        self.counts4_unit = {}
        self.counts4_unit['data_UL18D'] = {'passJetMult' : 1874829.0, 'passPreSel' : 70684.0, 'passDiJetMass' : 29608.0, 'SR' : 11081.0, 'SB' : 18527.0, 'passSvB' : 56.0, 'failSvB' : 41737.0, }
        self.counts4_unit['data_UL18C'] = {'passJetMult' : 418436.0, 'passPreSel' : 15758.0, 'passDiJetMass' : 6560.0, 'SR' : 2430.0, 'SB' : 4130.0, 'passSvB' : 9.0, 'failSvB' : 9337.0, }
        self.counts4_unit['data_UL18B'] = {'passJetMult' : 448667.0, 'passPreSel' : 16933.0, 'passDiJetMass' : 7028.0, 'SR' : 2648.0, 'SB' : 4380.0, 'passSvB' : 8.0, 'failSvB' : 10048.0, }
        self.counts4_unit['data_UL18A'] = {'passJetMult' : 902005.0, 'passPreSel' : 34344.0, 'passDiJetMass' : 14465.0, 'SR' : 5486.0, 'SB' : 8979.0, 'passSvB' : 27.0, 'failSvB' : 20510.0, }
        self.counts4_unit['data_UL17F'] = {'passJetMult' : 710245.0, 'passPreSel' : 27712.0, 'passDiJetMass' : 12225.0, 'SR' : 4478.0, 'SB' : 7747.0, 'passSvB' : 14.0, 'failSvB' : 15810.0, }
        self.counts4_unit['data_UL17E'] = {'passJetMult' : 549026.0, 'passPreSel' : 26873.0, 'passDiJetMass' : 12165.0, 'SR' : 4308.0, 'SB' : 7857.0, 'passSvB' : 14.0, 'failSvB' : 15622.0, }
        self.counts4_unit['data_UL17D'] = {'passJetMult' : 234161.0, 'passPreSel' : 12959.0, 'passDiJetMass' : 5904.0, 'SR' : 2065.0, 'SB' : 3839.0, 'passSvB' : 7.0, 'failSvB' : 7372.0, }
        self.counts4_unit['data_UL17C'] = {'passJetMult' : 498557.0, 'passPreSel' : 26897.0, 'passDiJetMass' : 12237.0, 'SR' : 4424.0, 'SB' : 7813.0, 'passSvB' : 12.0, 'failSvB' : 15156.0, }
        self.counts4_unit['data_UL16_preVFPE'] = {'passJetMult' : 395976.0, 'passPreSel' : 9779.0, 'passDiJetMass' : 4964.0, 'SR' : 1810.0, 'SB' : 3154.0, 'passSvB' : 2.0, 'failSvB' : 5762.0, }
        self.counts4_unit['data_UL16_preVFPD'] = {'passJetMult' : 421098.0, 'passPreSel' : 11270.0, 'passDiJetMass' : 5909.0, 'SR' : 2115.0, 'SB' : 3794.0, 'passSvB' : 9.0, 'failSvB' : 6595.0, }
        self.counts4_unit['data_UL16_preVFPC'] = {'passJetMult' : 256268.0, 'passPreSel' : 7263.0, 'passDiJetMass' : 3721.0, 'SR' : 1344.0, 'SB' : 2377.0, 'passSvB' : 4.0, 'failSvB' : 4229.0, }
        self.counts4_unit['data_UL16_preVFPB'] = {'passJetMult' : 598690.0, 'passPreSel' : 17900.0, 'passDiJetMass' : 9211.0, 'SR' : 3424.0, 'SB' : 5787.0, 'passSvB' : 15.0, 'failSvB' : 10432.0, }
        self.counts4_unit['data_UL16_postVFPH'] = {'passJetMult' : 903644.0, 'passPreSel' : 24327.0, 'passDiJetMass' : 12698.0, 'SR' : 4676.0, 'SB' : 8022.0, 'passSvB' : 16.0, 'failSvB' : 14548.0, }
        self.counts4_unit['data_UL16_postVFPG'] = {'passJetMult' : 877903.0, 'passPreSel' : 22800.0, 'passDiJetMass' : 12090.0, 'SR' : 4439.0, 'SB' : 7651.0, 'passSvB' : 11.0, 'failSvB' : 13699.0, }
        self.counts4_unit['data_UL16_postVFPF'] = {'passJetMult' : 311677.0, 'passPreSel' : 7731.0, 'passDiJetMass' : 3964.0, 'SR' : 1449.0, 'SB' : 2515.0, 'passSvB' : 6.0, 'failSvB' : 4549.0, }
        self.counts4_unit['ZZ4b_UL18'] = {'passJetMult' : 1387210.0, 'passPreSel' : 188616.0, 'passDiJetMass' : 170668.0, 'SR' : 135553.0, 'SB' : 35115.0, 'passSvB' : 6415.0, 'failSvB' : 12247.0, }
        self.counts4_unit['ZZ4b_UL17'] = {'passJetMult' : 1399598.0, 'passPreSel' : 194068.0, 'passDiJetMass' : 175414.0, 'SR' : 139529.0, 'SB' : 35885.0, 'passSvB' : 5803.0, 'failSvB' : 12755.0, }
        self.counts4_unit['ZZ4b_UL16_preVFP'] = {'passJetMult' : 574049.0, 'passPreSel' : 60548.0, 'passDiJetMass' : 54893.0, 'SR' : 42461.0, 'SB' : 12432.0, 'passSvB' : 1876.0, 'failSvB' : 6972.0, }
        self.counts4_unit['ZZ4b_UL16_postVFP'] = {'passJetMult' : 495921.0, 'passPreSel' : 55324.0, 'passDiJetMass' : 49973.0, 'SR' : 39621.0, 'SB' : 10352.0, 'passSvB' : 1814.0, 'failSvB' : 6056.0, }
        self.counts4_unit['ZH4b_UL18'] = {'passJetMult' : 324106.0, 'passPreSel' : 68353.0, 'passDiJetMass' : 64630.0, 'SR' : 52725.0, 'SB' : 11905.0, 'passSvB' : 3862.0, 'failSvB' : 2634.0, }
        self.counts4_unit['ZH4b_UL17'] = {'passJetMult' : 329417.0, 'passPreSel' : 71392.0, 'passDiJetMass' : 67566.0, 'SR' : 55036.0, 'SB' : 12530.0, 'passSvB' : 4032.0, 'failSvB' : 2858.0, }
        self.counts4_unit['ZH4b_UL16_preVFP'] = {'passJetMult' : 141711.0, 'passPreSel' : 23072.0, 'passDiJetMass' : 21900.0, 'SR' : 17661.0, 'SB' : 4239.0, 'passSvB' : 1446.0, 'failSvB' : 1868.0, }
        self.counts4_unit['ZH4b_UL16_postVFP'] = {'passJetMult' : 122790.0, 'passPreSel' : 20915.0, 'passDiJetMass' : 19838.0, 'SR' : 16161.0, 'SB' : 3677.0, 'passSvB' : 1431.0, 'failSvB' : 1625.0, }
        self.counts4_unit['TTToSemiLeptonic_UL18'] = {'passJetMult' : 7615050.0, 'passPreSel' : 90656.0, 'passDiJetMass' : 39651.0, 'SR' : 16662.0, 'SB' : 22989.0, 'passSvB' : 23.0, 'failSvB' : 53610.0, }
        self.counts4_unit['TTToSemiLeptonic_UL17'] = {'passJetMult' : 5945526.0, 'passPreSel' : 69812.0, 'passDiJetMass' : 30374.0, 'SR' : 12686.0, 'SB' : 17688.0, 'passSvB' : 13.0, 'failSvB' : 39370.0, }
        self.counts4_unit['TTToSemiLeptonic_UL16_preVFP'] = {'passJetMult' : 1534936.0, 'passPreSel' : 15034.0, 'passDiJetMass' : 6630.0, 'SR' : 2717.0, 'SB' : 3913.0, 'passSvB' : 4.0, 'failSvB' : 8518.0, }
        self.counts4_unit['TTToSemiLeptonic_UL16_postVFP'] = {'passJetMult' : 1945823.0, 'passPreSel' : 19838.0, 'passDiJetMass' : 8736.0, 'SR' : 3613.0, 'SB' : 5123.0, 'passSvB' : 3.0, 'failSvB' : 11262.0, }
        self.counts4_unit['TTToHadronic_UL18'] = {'passJetMult' : 9354148.0, 'passPreSel' : 89007.0, 'passDiJetMass' : 44837.0, 'SR' : 20863.0, 'SB' : 23974.0, 'passSvB' : 39.0, 'failSvB' : 44168.0, }
        self.counts4_unit['TTToHadronic_UL17'] = {'passJetMult' : 7135528.0, 'passPreSel' : 69387.0, 'passDiJetMass' : 35544.0, 'SR' : 16787.0, 'SB' : 18757.0, 'passSvB' : 32.0, 'failSvB' : 31794.0, }
        self.counts4_unit['TTToHadronic_UL16_preVFP'] = {'passJetMult' : 1916581.0, 'passPreSel' : 14905.0, 'passDiJetMass' : 7620.0, 'SR' : 3565.0, 'SB' : 4055.0, 'passSvB' : 11.0, 'failSvB' : 6766.0, }
        self.counts4_unit['TTToHadronic_UL16_postVFP'] = {'passJetMult' : 2435620.0, 'passPreSel' : 19565.0, 'passDiJetMass' : 10199.0, 'SR' : 4781.0, 'SB' : 5418.0, 'passSvB' : 9.0, 'failSvB' : 8957.0, }
        self.counts4_unit['TTTo2L2Nu_UL18'] = {'passJetMult' : 1007066.0, 'passPreSel' : 21454.0, 'passDiJetMass' : 9009.0, 'SR' : 3516.0, 'SB' : 5493.0, 'passSvB' : 6.0, 'failSvB' : 13568.0, }
        self.counts4_unit['TTTo2L2Nu_UL17'] = {'passJetMult' : 780712.0, 'passPreSel' : 15748.0, 'passDiJetMass' : 6379.0, 'SR' : 2493.0, 'SB' : 3886.0, 'passSvB' : 2.0, 'failSvB' : 9718.0, }
        self.counts4_unit['TTTo2L2Nu_UL16_preVFP'] = {'passJetMult' : 197932.0, 'passPreSel' : 3379.0, 'passDiJetMass' : 1377.0, 'SR' : 561.0, 'SB' : 816.0, 'passSvB' : 1.0, 'failSvB' : 2149.0, }
        self.counts4_unit['TTTo2L2Nu_UL16_postVFP'] = {'passJetMult' : 250965.0, 'passPreSel' : 4555.0, 'passDiJetMass' : 1928.0, 'SR' : 728.0, 'SB' : 1200.0, 'passSvB' : 3.0, 'failSvB' : 2916.0, }
        self.counts4_unit['HH4b_UL18'] = {'passJetMult' : 95649.0, 'passPreSel' : 19855.0, 'passDiJetMass' : 18234.0, 'SR' : 15947.0, 'SB' : 2287.0, 'passSvB' : 1945.0, 'failSvB' : 948.0, }
        self.counts4_unit['HH4b_UL17'] = {'passJetMult' : 92695.0, 'passPreSel' : 20323.0, 'passDiJetMass' : 18641.0, 'SR' : 16248.0, 'SB' : 2393.0, 'passSvB' : 2021.0, 'failSvB' : 984.0, }
        self.counts4_unit['HH4b_UL16_preVFP'] = {'passJetMult' : 71430.0, 'passPreSel' : 12513.0, 'passDiJetMass' : 11215.0, 'SR' : 9737.0, 'SB' : 1478.0, 'passSvB' : 1018.0, 'failSvB' : 863.0, }



        self.counts3_unit = {}
        self.counts3_unit['data_UL18D'] = {'passJetMult' : 1874829.0, 'passPreSel' : 1804145.0, 'passDiJetMass' : 555111.0, 'SR' : 218599.0, 'SB' : 336512.0, 'passSvB' : 802.0, 'failSvB' : 1149231.0, }
        self.counts3_unit['data_UL18C'] = {'passJetMult' : 418436.0, 'passPreSel' : 402678.0, 'passDiJetMass' : 121773.0, 'SR' : 47810.0, 'SB' : 73963.0, 'passSvB' : 167.0, 'failSvB' : 259193.0, }
        self.counts3_unit['data_UL18B'] = {'passJetMult' : 448667.0, 'passPreSel' : 431734.0, 'passDiJetMass' : 131403.0, 'SR' : 52148.0, 'SB' : 79255.0, 'passSvB' : 209.0, 'failSvB' : 277130.0, }
        self.counts3_unit['data_UL18A'] = {'passJetMult' : 902005.0, 'passPreSel' : 867661.0, 'passDiJetMass' : 270191.0, 'SR' : 106478.0, 'SB' : 163713.0, 'passSvB' : 329.0, 'failSvB' : 561110.0, }
        self.counts3_unit['data_UL17F'] = {'passJetMult' : 710245.0, 'passPreSel' : 682533.0, 'passDiJetMass' : 226414.0, 'SR' : 86478.0, 'SB' : 139936.0, 'passSvB' : 197.0, 'failSvB' : 425645.0, }
        self.counts3_unit['data_UL17E'] = {'passJetMult' : 549026.0, 'passPreSel' : 522153.0, 'passDiJetMass' : 179149.0, 'SR' : 67871.0, 'SB' : 111278.0, 'passSvB' : 168.0, 'failSvB' : 327319.0, }
        self.counts3_unit['data_UL17D'] = {'passJetMult' : 234161.0, 'passPreSel' : 221202.0, 'passDiJetMass' : 76166.0, 'SR' : 28620.0, 'SB' : 47546.0, 'passSvB' : 65.0, 'failSvB' : 135202.0, }
        self.counts3_unit['data_UL17C'] = {'passJetMult' : 498557.0, 'passPreSel' : 471660.0, 'passDiJetMass' : 160816.0, 'SR' : 60898.0, 'SB' : 99918.0, 'passSvB' : 181.0, 'failSvB' : 288362.0, }
        self.counts3_unit['data_UL16_preVFPE'] = {'passJetMult' : 395976.0, 'passPreSel' : 386197.0, 'passDiJetMass' : 158243.0, 'SR' : 59753.0, 'SB' : 98490.0, 'passSvB' : 130.0, 'failSvB' : 248662.0, }
        self.counts3_unit['data_UL16_preVFPD'] = {'passJetMult' : 421098.0, 'passPreSel' : 409828.0, 'passDiJetMass' : 172162.0, 'SR' : 65369.0, 'SB' : 106793.0, 'passSvB' : 174.0, 'failSvB' : 262289.0, }
        self.counts3_unit['data_UL16_preVFPC'] = {'passJetMult' : 256268.0, 'passPreSel' : 249005.0, 'passDiJetMass' : 104103.0, 'SR' : 39637.0, 'SB' : 64466.0, 'passSvB' : 86.0, 'failSvB' : 159763.0, }
        self.counts3_unit['data_UL16_preVFPB'] = {'passJetMult' : 598690.0, 'passPreSel' : 580790.0, 'passDiJetMass' : 241400.0, 'SR' : 91410.0, 'SB' : 149990.0, 'passSvB' : 256.0, 'failSvB' : 369711.0, }
        self.counts3_unit['data_UL16_postVFPH'] = {'passJetMult' : 903644.0, 'passPreSel' : 879317.0, 'passDiJetMass' : 375509.0, 'SR' : 142948.0, 'SB' : 232561.0, 'passSvB' : 261.0, 'failSvB' : 569771.0, }
        self.counts3_unit['data_UL16_postVFPG'] = {'passJetMult' : 877903.0, 'passPreSel' : 855103.0, 'passDiJetMass' : 368335.0, 'SR' : 139637.0, 'SB' : 228698.0, 'passSvB' : 244.0, 'failSvB' : 554649.0, }
        self.counts3_unit['data_UL16_postVFPF'] = {'passJetMult' : 311677.0, 'passPreSel' : 303946.0, 'passDiJetMass' : 126079.0, 'SR' : 47844.0, 'SB' : 78235.0, 'passSvB' : 114.0, 'failSvB' : 196811.0, }
        self.counts3_unit['ZZ4b_UL18'] = {'passJetMult' : 1387210.0, 'passPreSel' : 1195718.0, 'passDiJetMass' : 782801.0, 'SR' : 475797.0, 'SB' : 307004.0, 'passSvB' : 11074.0, 'failSvB' : 250739.0, }
        self.counts3_unit['ZZ4b_UL17'] = {'passJetMult' : 1399598.0, 'passPreSel' : 1202386.0, 'passDiJetMass' : 785136.0, 'SR' : 476869.0, 'SB' : 308267.0, 'passSvB' : 9228.0, 'failSvB' : 261176.0, }
        self.counts3_unit['ZZ4b_UL16_preVFP'] = {'passJetMult' : 574049.0, 'passPreSel' : 512510.0, 'passDiJetMass' : 345211.0, 'SR' : 210666.0, 'SB' : 134545.0, 'passSvB' : 4566.0, 'failSvB' : 168624.0, }
        self.counts3_unit['ZZ4b_UL16_postVFP'] = {'passJetMult' : 495921.0, 'passPreSel' : 439823.0, 'passDiJetMass' : 289525.0, 'SR' : 178570.0, 'SB' : 110955.0, 'passSvB' : 3989.0, 'failSvB' : 141927.0, }
        self.counts3_unit['ZH4b_UL18'] = {'passJetMult' : 324106.0, 'passPreSel' : 255153.0, 'passDiJetMass' : 190640.0, 'SR' : 124755.0, 'SB' : 65885.0, 'passSvB' : 5773.0, 'failSvB' : 43305.0, }
        self.counts3_unit['ZH4b_UL17'] = {'passJetMult' : 329417.0, 'passPreSel' : 257370.0, 'passDiJetMass' : 191260.0, 'SR' : 125486.0, 'SB' : 65774.0, 'passSvB' : 5262.0, 'failSvB' : 44527.0, }
        self.counts3_unit['ZH4b_UL16_preVFP'] = {'passJetMult' : 141711.0, 'passPreSel' : 118415.0, 'passDiJetMass' : 90975.0, 'SR' : 60807.0, 'SB' : 30168.0, 'passSvB' : 3189.0, 'failSvB' : 29017.0, }
        self.counts3_unit['ZH4b_UL16_postVFP'] = {'passJetMult' : 122790.0, 'passPreSel' : 101704.0, 'passDiJetMass' : 76191.0, 'SR' : 51283.0, 'SB' : 24908.0, 'passSvB' : 2803.0, 'failSvB' : 24355.0, }
        self.counts3_unit['TTToSemiLeptonic_UL18'] = {'passJetMult' : 7615050.0, 'passPreSel' : 7524394.0, 'passDiJetMass' : 4867857.0, 'SR' : 2513997.0, 'SB' : 2353860.0, 'passSvB' : 11520.0, 'failSvB' : 2864261.0, }
        self.counts3_unit['TTToSemiLeptonic_UL17'] = {'passJetMult' : 5945526.0, 'passPreSel' : 5875714.0, 'passDiJetMass' : 3799773.0, 'SR' : 1967413.0, 'SB' : 1832360.0, 'passSvB' : 8444.0, 'failSvB' : 2162905.0, }
        self.counts3_unit['TTToSemiLeptonic_UL16_preVFP'] = {'passJetMult' : 1534936.0, 'passPreSel' : 1519902.0, 'passDiJetMass' : 963603.0, 'SR' : 501165.0, 'SB' : 462438.0, 'passSvB' : 2545.0, 'failSvB' : 678727.0, }
        self.counts3_unit['TTToSemiLeptonic_UL16_postVFP'] = {'passJetMult' : 1945823.0, 'passPreSel' : 1925985.0, 'passDiJetMass' : 1237513.0, 'SR' : 640065.0, 'SB' : 597448.0, 'passSvB' : 2906.0, 'failSvB' : 861629.0, }
        self.counts3_unit['TTToHadronic_UL18'] = {'passJetMult' : 9354148.0, 'passPreSel' : 9265141.0, 'passDiJetMass' : 6819127.0, 'SR' : 3794205.0, 'SB' : 3024922.0, 'passSvB' : 9885.0, 'failSvB' : 2455742.0, }
        self.counts3_unit['TTToHadronic_UL17'] = {'passJetMult' : 7135528.0, 'passPreSel' : 7066141.0, 'passDiJetMass' : 5161401.0, 'SR' : 2862624.0, 'SB' : 2298777.0, 'passSvB' : 6994.0, 'failSvB' : 1793129.0, }
        self.counts3_unit['TTToHadronic_UL16_preVFP'] = {'passJetMult' : 1916581.0, 'passPreSel' : 1901676.0, 'passDiJetMass' : 1392048.0, 'SR' : 794698.0, 'SB' : 597350.0, 'passSvB' : 2290.0, 'failSvB' : 584178.0, }
        self.counts3_unit['TTToHadronic_UL16_postVFP'] = {'passJetMult' : 2435620.0, 'passPreSel' : 2416055.0, 'passDiJetMass' : 1782976.0, 'SR' : 1007516.0, 'SB' : 775460.0, 'passSvB' : 2480.0, 'failSvB' : 746118.0, }
        self.counts3_unit['TTTo2L2Nu_UL18'] = {'passJetMult' : 1007066.0, 'passPreSel' : 985612.0, 'passDiJetMass' : 514547.0, 'SR' : 237611.0, 'SB' : 276936.0, 'passSvB' : 1903.0, 'failSvB' : 493959.0, }
        self.counts3_unit['TTTo2L2Nu_UL17'] = {'passJetMult' : 780712.0, 'passPreSel' : 764964.0, 'passDiJetMass' : 403712.0, 'SR' : 188091.0, 'SB' : 215621.0, 'passSvB' : 1458.0, 'failSvB' : 370026.0, }
        self.counts3_unit['TTTo2L2Nu_UL16_preVFP'] = {'passJetMult' : 197932.0, 'passPreSel' : 194553.0, 'passDiJetMass' : 96447.0, 'SR' : 43958.0, 'SB' : 52489.0, 'passSvB' : 365.0, 'failSvB' : 109014.0, }
        self.counts3_unit['TTTo2L2Nu_UL16_postVFP'] = {'passJetMult' : 250965.0, 'passPreSel' : 246410.0, 'passDiJetMass' : 125081.0, 'SR' : 57371.0, 'SB' : 67710.0, 'passSvB' : 434.0, 'failSvB' : 138208.0, }
        self.counts3_unit['HH4b_UL18'] = {'passJetMult' : 95649.0, 'passPreSel' : 75632.0, 'passDiJetMass' : 43476.0, 'SR' : 30819.0, 'SB' : 12657.0, 'passSvB' : 2055.0, 'failSvB' : 21536.0, }
        self.counts3_unit['HH4b_UL17'] = {'passJetMult' : 92695.0, 'passPreSel' : 72198.0, 'passDiJetMass' : 40780.0, 'SR' : 28452.0, 'SB' : 12328.0, 'passSvB' : 1891.0, 'failSvB' : 20279.0, }
        self.counts3_unit['HH4b_UL16_preVFP'] = {'passJetMult' : 71430.0, 'passPreSel' : 58769.0, 'passDiJetMass' : 33564.0, 'SR' : 23449.0, 'SB' : 10115.0, 'passSvB' : 1300.0, 'failSvB' : 17271.0, }

        self.keysToTest = list(self.counts3_unit.keys())
        self.keysToTest.remove("ZZ4b_UL18")
        self.keysToTest.remove("ZZ4b_UL17")
        self.keysToTest.remove("ZZ4b_UL16_preVFP")
        self.keysToTest.remove("ZZ4b_UL16_postVFP")
        #self.keysToTest = ['TTTo2L2Nu_UL18', 'TTTo2L2Nu_UL17', 'TTTo2L2Nu_UL16_preVFP', 'TTTo2L2Nu_UL16_postVFP']

        
    def test_counts4(self):
        """
        Test the cutflow for four tag events
        """
        for datasetAndEra in self.keysToTest:
            with self.subTest(datasetAndEra=datasetAndEra):
                for cut, v in self.counts4[datasetAndEra].items():
                    self.assertAlmostEqual(float(v), 
                                           float(self.cf4[datasetAndEra][cut]), 
                                           delta=0.1 , 
                                           msg=f'incorrect number of fourTag counts for cut: {cut} of dataset {datasetAndEra}')

    def test_counts3(self):
        """
        Test the cutflow for the weighted three tag events
        """
        for datasetAndEra in self.keysToTest:
            for cut, v in self.counts3[datasetAndEra].items():
                self.assertAlmostEqual(float(v), 
                                       float(self.cf3[datasetAndEra][cut]), 
                                       delta=0.1, 
                                       msg=f'incorrect number of weighted threeTag counts for cut: {cut} of dataset {datasetAndEra}')

    def test_counts3_unitWeight(self):
        """
        Test the cutflow for the unweighted three tag events
        """
        for datasetAndEra in self.keysToTest:
            for cut, v in self.counts3_unit[datasetAndEra].items():
                self.assertEqual(round(v,2),round(float(self.cf3_unit[datasetAndEra][cut]),2),f'incorrect number of threeTag counts for cut: {cut} of dataset {datasetAndEra}')

    def test_counts4_unitWeight(self):
        """
        Test the cutflow for the unweighted fourTag events
        """
        for datasetAndEra in self.keysToTest:
            for cut, v in self.counts4_unit[datasetAndEra].items():
                self.assertEqual(round(v,2),round(float(self.cf4_unit[datasetAndEra][cut]),2),f'incorrect number of fourTag counts for cut: {cut} of dataset {datasetAndEra}')


                
                

if __name__ == '__main__':
    unittest.main()
