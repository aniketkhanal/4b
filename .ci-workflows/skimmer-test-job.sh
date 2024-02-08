echo "############### Including proxy"
export X509_USER_PROXY=${PWD}/proxy/x509_proxy
echo "############### Checking proxy"
voms-proxy-info
echo "############### Moving to python folder"
cd python/
echo "############### Changing metadata"
sed "s?base_path.*?base_path: $CI_PROJECT_DIR?" skimmer/metadata/HH4b.yml > skimmer/metadata/tmp.yml
echo "############### Running test processor"
python runner.py -s -p skimmer/processor/skimmer_4b.py -c skimmer/metadata/tmp.yml -y UL18 -d TTToHadronic -op skimmer/metadata/ -o picoaod_datasets_TTToHadronic_UL18.yml -t
ls -R skimmer/
cp /tmp/coffea4bees*html coffea3bees-dask-report.html
cd ../
