# ncov_parser

[![Build Status](https://travis-ci.com/rdeborja/ncov_parser.svg?branch=master)](https://travis-ci.com/rdeborja/ncov_parser)

The `ncov_parser` package provides a suite of tools to parse the files generated
in the Nextflow workflow and provide a QC summary file.  The package requires
several files including:
* <sample>.variants.tsv
* <sample>.qc.csv

In addition, `bedtools` should be run to generate a
`<sample>.per_base_coverage.bed` file to generate mean and median depth of
coverage statistics.


## Installation
After downloading the repository, the package can be installed using `pip`:
```
git clone git@github.com:rdeborja/ncov_parser.git
cd ncov_parser
pip install .
```


## Usage
The library consists of several functions that can be imported.
```
from ncov.parser.qc import *
```

### Top levels scripts
In the `bin` directory, several wrapper scripts exist to assist in generating
QC metrics.

To create sample level summary qc files, use the `create_sample_qc_summary.py`
script:
```
create_sample_qc_summary.py --sample <sample name> --qc_dir <directory
containing sample.qc.csv files> --variants_dir <directory containing
sample.variants.tsv files> --coverage_dir <directory containing
sample.per_base_coverage.bed files> [--indel]
```
Note the `--indel` flag should only be present if indels will be used in the
calculation of variants.

Once this is complete, we can use the `collect_qc_summary.py` script to
aggregate the sample level summary files into a single run tab-separate file.
```
collect_qc_summary.py --path <path to sample.summary.qc.tsv files>
```


## License
MIT

