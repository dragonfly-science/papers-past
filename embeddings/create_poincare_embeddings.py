
import click
import numpy as np
import pandas as pd
from multiprocessing import cpu_count
from utils import initialise_logger, multicore_apply

from gensim.test.utils import datapath
from gensim.models.poincare import PoincareModel, PoincareRelations


def load_network(network_tsv):
    with open(network_tsv, 'r') as f:
        output = []
        for line in f.read().strip().split("\n"):
            x, y, w = line.split()
            x = int(x)
            y = int(y)
            output.append(tuple([x, y]))
            output.append(tuple([y, x]))
        return output


def load_word_counts(word_counts_file):
    word_counts = []
    with open(word_counts_file, 'r') as f:
        for line in f.read().strip().split('\n'):
            count, word = line.strip().split()
            count = int(count)
            word_counts.append({
                'word': word,
                'count': count
            })
    return word_counts


@click.command()
@click.option('--network_tsv', help='Path to network.tsv')
@click.option('--word_counts', help='Path to word_counts.txt')
@click.option('--output', help='Path to save trained word vectors')
@click.option('--epochs', default=50, type=int, help='Path to network.tsv')
@click.option('--log_level', default='INFO', help='Log level (default: INFO)')
def main(network_tsv, word_counts, output, epochs, log_level):

    global logger
    logger = initialise_logger(log_level, __file__)

    logger.info('Loading network from {}'.format(network_tsv))
    network = load_network(network_tsv)
    logger.info('First 5 relations: {}'.format(network[:5]))

    logger.info('Getting word counts from {}'.format(word_counts))
    word_counts = load_word_counts(word_counts)

    relations = [
        (word_counts[x]['word'], word_counts[y]['word']) \
        for x, y in network
    ]
    
    model = PoincareModel(relations, size=2, negative=2)

    logger.info("Training poincaré model...")
    model.train(epochs=epochs)

    logger.info("Saving trained model to {}".format(output))
    model.save(output)

    logger.info('Done!')


if __name__ == '__main__':
    main()
