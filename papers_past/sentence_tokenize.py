import os
import click
import logging
from nltk.tokenize import sent_tokenize


@click.command()
@click.option('--doc_dir', help='Path to documents directory')
@click.option('--out_dir', help='Path to save output')
@click.option('--log_level', default='INFO', help='Log level (default: INFO)')
def main(doc_dir, out_dir, log_level):

    # Set logger config
    logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logging.info("Creating directory: {}".format(out_dir))
    if not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    for root, dirs, files in os.walk(doc_dir):
        for f in files:
            if f.endswith('.txt'):

                fp = os.path.join(root, f)
                out = os.path.join(out_dir, f)

                with open(fp, 'r') as f:
                    text = f.read()

                logging.debug('Splitting {} into sentences {}'.format(fp, out))
                with open(out, 'w') as f:
                    for sent in sent_tokenize(text):
                        sent = sent.replace('\n', ' ').strip()
                        f.write(sent + '\n')


if __name__ == '__main__':
    main()
