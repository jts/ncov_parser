'''
A parser for the qc metrics file generated by the COG-UK Nextflow pipeline.  The
generated file contains a header line and a data line with pre-defined columns.
'''

import re
import statistics
import glob


def get_qc_data(file):
    '''
    A function to parse the COG-UK QC file and returns a data structure with the
    QC results.

    Arguments:
        * file (str): a string containing the path and filename of the <sample>.qc.csv file

    Return Value:
        * dict: returns a dictionary with keys "sample_name", "pct_covered_bases", "qc_pass"
    '''
    with open(file) as file_p:
        for line in file_p:
            # skip the header
            if re.match("^sample_name", line):
                continue
            line = line.strip()
            data = line.split(",")
    file_p.close()
    return {'sample_name' : data[0], 'pct_n_bases' : data[1], 'pct_covered_bases' : data[2], 'qc_pass' : data[6]}


def get_total_variants(file, indel=False):
    '''
    A function that parses the iVar variants file and returns the total number
    of variants.

    Arguments:
        * file: a string containing the filename and path to the <sample>.variants.tsv file
        * indel: a boolean to determine whether to process indels

    Returns:
        Function returns a dictionary containing the following keys:
            * total_variants: total number of variants in the file
            * total_n: total number of variants classified as 'N'
            * total_iupac: total number of variants classified within IUPAC codes
    '''
    counter = 0
    counter_n = 0
    counter_iupac = 0
    counter_snv = 0
    counter_indel = 0
    with open(file) as file_p:
        for line in file_p:
            if re.match("^REGION\tPOS\tREF", line):
                # skip to the next line if header encountered
                continue
            # check if the variant is an indel and the option for counting
            # indels
            data = line.split("\t")
            if indel:
                if len(str(data[3])) > 1:
                    counter += 1
                    counter_indel += 1
                elif len(str(data[3])) == 1:
                    counter += 1
                    counter_snv += 1

            elif not indel:
                if len(str(data[3])) == 1:
                    counter += 1
                    counter_snv += 1
                else:
                    continue
            # count N and IUPAC codes seperately
            if is_variant_n(variant=str(data[3])):
                counter_n += 1
            elif is_variant_iupac(variant=str(data[3])):
                counter_iupac += 1
    file_p.close()
    return {'total_variants' : counter,
            'total_n' : counter_n,
            'total_iupac' : counter_iupac,
            'total_snv' : counter_snv,
            'total_indel' : counter_indel}


def import_ct_data(file):
    '''
    Obtain the name of the metadata YAML file and import the data.

    Arguments:
        * file: full path to the metadata YAML file

    Return Value:
        The function returns a dictionary with {"sample" : "ct"}
    '''
    with open(file) as file_p:
        tmp_data = []
        data = {}
        for line in file_p:
            # skip the header if exists
            if re.match("^sample\tct", line.lower()):
                continue
            line = line.strip()
            tmp_data = line.split("\t")
            data[tmp_data[0]] = tmp_data[1]
        file_p.close()
        return data


def is_variant_n(variant):
    '''
    A function to determine whether the mutation is N

    Arguments:
        * variant: a string representing the variant

    Return Value:
        Function returns a boolean
    '''
    variant = str(variant).upper()
    return re.search('[Nn]', variant)


def is_variant_iupac(variant):
    '''
    A function to determine whether a variant is an IUPAC code, note that we
    are treating N as a distinct value.

    Arguments:
        * variant: a string reprenting the variant

    Return Value:
        Function returns a boolean
    '''
    variant = str(variant).upper()
    iupac_codes = '[RYSWKMBDHV]'
    return re.search(iupac_codes, variant)


def is_indel(variant):
    '''
    Check whether the variant from the <sample>.variants.tsv file is an indel.
    Note that indels will have a +/- in the ALT column of the file.

    Arguments:
        * variant: a string reprenting the variant

    Return Value:
        Function returns a boolean
    '''
    return len(variant) > 1


def get_coverage_stats(file):
    '''
    A function to calculate the depth of coverage across the genome from the
    bedtools <sample>.per_base_coverage.bed file.

    Arguments:
        * file: a string containing the filename and path to the
                <sample>.per_sample_coverage.bed file

    Return Value:
        Function returns a dictionary with the following keys:
            * mean_depth
            * median_depth
    '''
    depth = []
    with open(file) as file_p:
        for line in file_p:
            if re.match("^reference_name\tstart\tend", line):
                # skip to the next line if header encountered
                continue
            line = line.strip()
            data = line.split("\t")
            depth.append(int(data[7]))
    file_p.close()
    mean_depth = statistics.mean(depth)
    median_depth = statistics.median(depth)
    return {"mean" : mean_depth, "median" : median_depth}


def create_qc_summary_line(var_file, qc_file, cov_file, meta_file, indel=True):
    '''
    A function that aggregates the different QC data into a single sample
    dictionary entry.

    Arguments:
        * var_file:     full path to the <sample>.variants.tsv file
        * qc_file:      full path to the <sample>.qc.csv file
        * cov_file:     full path to the <sample>.per_base_coverage.bed file
        * meta_file:    full path to the 'metadata.tsv' file
        * indel:        boolean to determine whether to use indels in variant
                        count (default: True)

    Return Value:
        Return an aggregate dictionary containing the following keys:
            * total_variants
            * total_snv
            * total_indel
            * total_n
            * total_iupac
            * sample_name
            * pct_n_bases
            * pct_covered_bases
            * qc_pass
            * mean
            * median
            * ct
    '''
    summary = {}
    summary.update(get_total_variants(file=var_file, indel=indel))
    summary.update(get_qc_data(file=qc_file))
    summary.update(get_coverage_stats(file=cov_file))

    # import the ct data from the metadata file and add the ct value to the summary dictionary
    meta_data = import_ct_data(file=meta_file)
    summary['ct'] = meta_data[summary['sample_name']]

    return summary


def write_qc_summary(summary):
    '''
    A function to write the QC data line to output in the order:
    * sample name
    # % n bases
    * % bases covered
    * total mutations
    * total snv
    * total indel
    * total N mutations
    * total IUPAC mutations
    * mean sequence depth
    * median sequence depth
    * iVar QC pass

    Arguments:
        * summary:  dictionary containing the keys sample_name, pct_n_bases,
                    pct_covered_bases, total_variants, total_snv, total_indel,
                    total_n, total_iupac, mean_depth, median_depth, ct, qc_pass

    Return Value:
        None
    '''
    summary_line = '\t'.join([
        summary['sample_name'],
        str(summary['pct_n_bases']),
        str(summary['pct_covered_bases']),
        str(summary['total_variants']),
        str(summary['total_snv']),
        str(summary['total_indel']),
        str(summary['total_n']),
        str(summary['total_iupac']),
        str(summary['mean']),
        str(summary['median']),
        str(summary['ct']),
        str(summary['qc_pass'])])
    print(summary_line)


def write_qc_summary_header(header=['sample_name',
                                    'pct_n_bases',
                                    'pct_covered_bases',
                                    'total_variants',
                                    'total_snv',
                                    'total_indel',
                                    'total_n',
                                    'total_iupac',
                                    'mean_depth',
                                    'median_depth',
                                    'ct',
                                    'qc_pass']):
    '''
    Write the header for the QC summary data

    Arguments:
        * header: a list containing the column header

    Return Value:
        None
    '''
    print('\t'.join(header))


def collect_qc_summary_data(path, pattern='.summary.qc.tsv'):
    '''
    An aggregation function to collect individual sample based QC summary data
    and create a single file with all samples.

    Arguments:
        * path:     full path to the <sample>.summary.qc.tsv files
        * pattern:  file pattern for the sample files (default: .summary.qc.tsv)

    Return Value:
        data: a list containing the summary line data
    '''
    files = glob.glob(path + "/*" + pattern)
    data = []
    for file in files:
        with open(file) as file_p:
            for line in file_p:
                # skip the header
                if re.match("^sample_name\tpct_n_bases\tpct_covered_bases", line):
                    continue
                data.append(line.rstrip())
    return data
