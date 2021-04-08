# Import libraries
import glob
from utils import list_articles, get_wildcards

# Useful variables
run='docker run --rm -v $(pwd):/code -w /code -u $(id -u):$(id -g) mathematiguy/papers-past'

# These targets don't work
exceptions=['ODT_1898', 'LT_1890', 'LT_1891']
is_exception = re.compile('|'.join(exceptions))

archives = [f for f in glob.glob('data/raw/*.tar.gz') if not is_exception.search(f)]
articles = list_articles(archives, data_path = 'data/unzipped')

# Parameters
log_level='INFO'

rule all:
    input:
        [article.replace('.xml', '_sentence_lines.txt') for article in articles]

rule unzip:
    input:
        'data/raw/{newspaper}_{year}.tar.gz'
    output:
        'data/unzipped/{newspaper}/{year}/.done'
    wildcard_constraints:
        year='\d+'
    priority: 1
    shell:
        'tar -xf {input} -C data/unzipped/ && touch {output}'

rule convert_xml:
    input:
        'data/unzipped/{newspaper}/{year}/.done'
    output:
        'data/unzipped/{newspaper}/{year}/{newspaper_date}/MM_01/{article}.txt'
    wildcard_constraints:
        year='\d+',
        article='\d+'
    priority: 2
    shell:
        '{run} python3 papers_past/convert_xml.py --xml_file data/unzipped/{wildcards.newspaper}/{wildcards.year}/{wildcards.newspaper_date}/MM_01/{wildcards.article}.xml --log_level {log_level}'

rule sent_tokenize:
    input:
        'data/unzipped/{newspaper}/{year}/{newspaper_date}/MM_01/{article}.txt'
    output:
        'data/unzipped/{newspaper}/{year}/{newspaper_date}/MM_01/{article}_sentence_lines.txt'
    wildcard_constraints:
        newspaper='[A-Z]+',
        year='\d+',
        article='\d+'
    priority: 3
    shell:
        '{run} python3 papers_past/sentence_tokenize.py --filepath {input} --log_level {log_level}'
