# Import libraries
import glob
from utils import get_wildcards

# Useful variables
run='' # 'docker run --rm -it -v $(pwd):/code -w /code -u $(id -u):$(id -g) mathematiguy/papers-past'

# These targets don't work
is_exception = re.compile('|'.join(['ODT_1898', 'LT_1890', 'LT_1891']))

archives = [f for f in glob.glob('data/raw/*.tar.gz') if not is_exception.search(f)]

# Parameters
log_level='INFO'

rule all:
    input:
        expand('data/sentences/{newspaper}/{year}', zip, **get_wildcards(archives))

rule unzip:
    input:
        'data/raw/{newspaper}_{year}.tar.gz'
    output:
        directory('data/unzipped/{newspaper}/{year}/')
    wildcard_constraints:
        year='\d+'
    priority: 1
    shell:
        'tar -xf {input} -C data/unzipped/'

rule convert_xml:
    input:
        'data/unzipped/{newspaper}/{year}/'
    output:
        directory('data/documents/{newspaper}/{year}/')
    wildcard_constraints:
        year='\d+',
        article='\d+'
    priority: 2
    shell:
        '{run} python3 papers_past/convert_xml.py --xml_dir {input} --out_dir {output} --log_level {log_level}'

rule sent_tokenize:
    input:
        'data/documents/{newspaper}/{year}/'
    output:
        directory('data/sentences/{newspaper}/{year}/')
    wildcard_constraints:
        newspaper='[A-Z]+',
        year='\d+',
        article='\d+'
    priority: 3
    shell:
        '{run} python3 papers_past/sentence_tokenize.py --doc_dir {input} --out_dir {output} --log_level {log_level}'

rule compile_corpus:
    input:
        expand('data/sentences/{newspaper}/{year}', zip, **get_wildcards(archives))
    output:
        'data/sentence_corpus.txt'
    threads: 1
    shell:
        '\n'.join([f'find data/sentences/{newspaper}/{year} -type f | xargs cat >> data/sentence_corpus.txt'
                   for newspaper, year in zip(*get_wildcards(archives).values())])

rule sentence_piece:
    input:
        ''
    output:
        ''
    shell:
        'spm_train --input={input} --model_prefix=test.unigram --vocab_size=8000 --character_coverage=1.0 --model_type=unigram'
