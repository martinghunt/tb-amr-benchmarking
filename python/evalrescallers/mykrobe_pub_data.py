import csv
import os

import evalrescallers

eval_dir = os.path.abspath(os.path.dirname(evalrescallers.__file__))
publication_suppl_files_dir = os.path.join(eval_dir, 'data')
tb_comid_to_country = None


def load_nature_suppl_file(infile, species):
    '''Loads sample name -> drug resistance dict, from
    mykrobe nature supplementary text file'''
    columns = []
    sample_to_res = {}
    all_drugs = set()
    first_drug_columns = {'tb': 4, 'staph': 6}
    sample_to_country = {}
    if species == 'tb' and tb_comid_to_country is None:
        country_file = os.path.join(publication_suppl_files_dir, 'ncomms_countries.tsv')
        comid_to_country = load_sample_to_country_file(country_file)

    with open(infile) as f:
        for line in f:
            if line.startswith('"Supplementary Data'):
                continue

            fields = line.rstrip().split('\t')
            if line.startswith('sample_set'):
                columns = fields
                all_drugs = set(fields[first_drug_columns[species]:])
                continue

            samples = fields[2].split(';')
            samples.sort()
            sample = '.'.join(samples)
            res_data = {}
            for i in range(4, len(fields), 1):
                if fields[i] in {'R', 'S'}:
                    res_data[columns[i]] =  fields[i]

            if species == 'tb':
                all_drugs.add('Quinolones')
                if res_data.get('Ciprofloxacin', None) == 'R' or res_data.get('Moxifloxacin', None) == 'R':
                    res_data['Quinolones'] = 'R'
                if res_data.get('Ciprofloxacin', None) == 'S' and res_data.get('Moxifloxacin', None) == 'S':
                    res_data['Quinolones'] = 'S'

                sample_to_country[sample] = comid_to_country[fields[1]]

            sample_to_res[sample] = res_data

    return all_drugs, sample_to_res, sample_to_country


def load_sample_to_country_file(infile):
    sample_to_country = {}
    with open(infile) as f:
        reader = csv.DictReader(f, delimiter='\t')
        for d in reader:
            assert d['comid'] not in sample_to_country
            sample_to_country[d['comid']] = d['country']

    return sample_to_country


def load_all_nature_suppl_files(species):
    sample_to_res = {}
    assert os.path.exists(publication_suppl_files_dir)
    files = {
        'staph': ['ncomms10063-s4.txt'],
        'tb': [
            'ncomms10063-s10.txt',
            'ncomms10063-s7.txt',
            'ncomms10063-s8.txt',
            'ncomms10063-s9.txt',
        ],
    }
    assert species in files
    all_drugs = set()
    sample_to_res = {}
    sample_to_country = {}

    for filename in files[species]:
        new_drugs, new_results, new_countries = load_nature_suppl_file(os.path.join(publication_suppl_files_dir, filename), species)
        sample_to_country.update(new_countries)
        all_drugs.update(new_drugs)
        for sample in new_results:
            # some samples are in >1 file. But some calls are
            # missing from some files. So sanity check agree when in both,
            # and use the new calls when we find them
            if sample in sample_to_res:
                for drug in new_results[sample]:
                    if drug in sample_to_res[sample][drug]:
                        assert new_results[sample][drug] == sample_to_res[sample][drug]
                    else:
                        sample_to_res[sample][drug] = new_results[sample][drug]
            else:
                sample_to_res[sample] = new_results[sample]

    return all_drugs, sample_to_res, sample_to_country

