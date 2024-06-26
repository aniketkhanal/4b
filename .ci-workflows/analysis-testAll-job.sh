echo "############### Including proxy"
export X509_USER_PROXY=${PWD}/proxy/x509_proxy
echo "############### Checking proxy"
voms-proxy-info
echo "############### Moving to python folder"
cd python/
echo "############### Running test processor"
python runner.py -d data TTToHadronic TTToSemiLeptonic TTTo2L2Nu ZZ4b ZH4b HH4b   -p analysis/processors/processor_HH4b.py  -y UL17 UL18 UL16_preVFP UL16_postVFP -o histAll.coffea -op analysis/hists/
ls
python analysis/tests/cutflow_test.py   --inputFile analysis/hists/histAll.coffea --knownCounts analysis/tests/histAllCounts.yml
cd ../
