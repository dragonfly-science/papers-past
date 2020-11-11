import re
import json
import click
import numpy as np
import pandas as pd
from scipy.linalg import norm
from utils import initialise_logger, multicore_apply

from umap import UMAP


def create_vector_data(word_vectors):

    with open(word_vectors, 'r') as f:

        vector_data = f.read().strip().split('\n')
        rows, dims = vector_data[0].split()

        vector_data = [(word, np.array([float(v) for v in vec.split()]))
                       for word, vec in map(lambda s: s.split(' ', 1), vector_data[1:])]
        vector_data = pd.DataFrame(vector_data)

        vector_data.columns = ['word', 'vector']

        return vector_data


def create_word_counts(word_counts):

    result = []
    with open(word_counts, 'r') as f:
        for line in f.read().strip().split('\n'):
            count, word = line.strip().split()
            result.append({'word': word, 'count': int(count)})

    return pd.DataFrame.from_dict(result)


@click.command()
@click.option('--word_vectors', help='Path to fasttext.vec')
@click.option('--network_file', help='Path to save network.txt')
@click.option('--threshold', type=float, help='Percentile for building word network')
@click.option('--log_level', default='INFO', help='Log level (default: INFO)')
def main(word_vectors, network_file, threshold, log_level):

    global logger
    logger = initialise_logger(log_level, __file__)

    assert threshold >= 0 and threshold < 100

    logger.info('Creating vector_data..')
    vector_data = create_vector_data(word_vectors)
    vector_data = vector_data.loc[vector_data.word != "</s>", :]

    logger.info('Computing similarity matrix..')
    normalize = lambda x: x / norm(x)
    word_vectors = np.vstack(vector_data.vector.apply(normalize))
    similarity_matrix = np.dot(word_vectors, word_vectors.transpose())
    similarity_matrix -= np.identity(similarity_matrix.shape[0])

    threshold = np.percentile(similarity_matrix, threshold)
    logger.info("Using threshold={:.3f}".format(threshold))

    similarity_matrix[similarity_matrix < threshold] = 0

    with open(network_file, 'w') as f:
        xs, ys = np.where(similarity_matrix > 0)
        logger.info("Writing {} edges to {}".format(len(xs), network_file))
        for x, y in zip(xs, ys):
            f.write("{} {} {}\n".format(vector_data.loc[x, 'word'], vector_data.loc[y, 'word'], similarity_matrix[x,y]))

    logger.info('Done!')


if __name__ == '__main__':
    main()
