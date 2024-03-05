echo "############### Including proxy"
export X509_USER_PROXY=${PWD}/proxy/x509_proxy
echo "############### Checking proxy"
voms-proxy-info
echo "############### Moving to python folder"
cd python/
echo "############### Changing metadata"
echo "pwd" ${PWD}
echo "project_path" ${CI_PROJECT_PATH}
sed -e "s/base_.*/base_path: " -e "s/\#max.*/maxchunks: 5/" -e "s/\#test.*/test_files: 1/" -e "s/2024_.*/tmp\//" -e "s/T3_US_FNALLPC/T3_CH_PSI/" skimmer/metadata/HH4b.yml > skimmer/metadata/tmp.yml
cat skimmer/metadata/tmp.yml
echo "############### Running test processor"
python runner.py -s -p skimmer/processor/skimmer_4b.py -c skimmer/metadata/tmp.yml -y UL18 -d TTToSemiLeptonic -op skimmer/metadata/ -o picoaod_datasets_TTToSemiLeptonic_UL18.yml -t
ls -R skimmer/
cp /tmp/coffea4bees*html coffea3bees-dask-report.html
cd ../
