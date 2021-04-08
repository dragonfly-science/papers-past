import click
import logging
from nltk.tokenize import sent_tokenize


@click.command()
@click.option('--filepath', help='Path to xml files')
@click.option('--log_level', default='INFO', help='Log level (default: INFO)')
def main(filepath, log_level):

    # Set logger config
    logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    with open(filepath, 'r') as f:
        text = f.read()

    with open(filepath.replace('.txt', '_sentence_lines.txt'), 'w') as f:
        for sent in sent_tokenize(text):
            sent = sent.replace('\n', ' ').strip()
            f.write(sent + '\n')


if __name__ == '__main__':
    main()
