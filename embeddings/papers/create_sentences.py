import sys
sys.path.append("embeddings")

import re
import click
import pandas as pd
from reo_toolkit import is_maori
from gensim.models import Phrases
from nltk.tokenize import sent_tokenize, word_tokenize
from utils import initialise_logger, multicore_apply

pd.set_option('display.max_columns', None)


def extract_words(text):
    text = text.lower()
    results = []
    for word in word_tokenize(text):
        if re.search('[a-zāēīōū]', word):
            result = re.sub('\s{2,}', ' ',
                re.sub('[^a-zāēīōū]', ' ', word)
            )
            for res in result.split():
                results.append(res)
    return results


def phrase_model(lines, min_count, threshold, phrase_length):

    for _ in range(phrase_length):
        sentence_stream = [doc.split(" ") for doc in lines]
        bigram = Phrases(sentence_stream, min_count=min_count, threshold=threshold)
        lines = [' '.join(bigram[line.split()]) for line in lines]

    return lines


def count_maori_words(text):
    return sum(1 if is_maori(word, strict=True) else 0 for word in text)


def create_sentences(sentences, min_count, phrase_length, maori_min_percentage, sentence_min_length):

    logger.info('Split paragraphs into sentences..')
    sentences['sentence'] = multicore_apply(sentences.paragraph, sent_tokenize, front_num=3)
    sentences = sentences[[col for col in sentences.columns if not col == 'paragraph']].explode('sentence')
    sentences = sentences[sentences.sentence.str.len() > 0].drop_duplicates()

    group_vars = ['newspaper', 'issue', 'year', 'month', 'day', 'paragraph_id', 'sentence']
    sentences['sentence_id'] = sentences.groupby(group_vars).ngroup()
    sentences['sentence_id'] = sentences.sentence_id - \
        (sentences
             .groupby(['newspaper', 'issue', 'year', 'month', 'day', 'paragraph_id'],
                      group_keys = False)
             .transform(min)
             ['sentence_id'])

    sentences = (sentences
        .sort_values(['newspaper', 'issue', 'year', 'month', 'day', 'paragraph_id', 'sentence_id'])
        [['newspaper', 'issue', 'year', 'month', 'day', 'paragraph_id', 'sentence_id', 'sentence']]
    )

    logger.info('Split sentences into words..')
    sentences['words'] = multicore_apply(sentences.sentence, extract_words, front_num=3)
    sentences['maori_word_count'] = multicore_apply(sentences.words, count_maori_words)
    sentences['non_maori_word_count'] = sentences.words.apply(len) - sentences.maori_word_count
    sentences['maori_word_percentage'] = sentences.maori_word_count / sentences.words.apply(len)

    logger.info("Dropping sentences below {:.1f}% māori words and shorter than {} words".format(maori_min_percentage * 100, sentence_min_length))
    sentences = sentences.loc[(sentences.maori_word_percentage > maori_min_percentage) & (sentences.words.apply(len) >= sentence_min_length), :]

    maori_words  = set(word for word in
        sentences.loc[sentences.words.apply(len) > 0, 'words']
              .explode()
              .unique()
       if is_maori(word, strict=True)
    )
    non_maori_words  = set(word for word in
        sentences.loc[sentences.words.apply(len) > 0, 'words']
              .explode()
              .unique()
        if not is_maori(word, strict=True)
    )

    logger.info('Extract māori phrases')
    sentences['phrase'] = phrase_model(
        (sentences.words
            .apply(lambda x: ' '.join(
                [y for y in x if y in maori_words]
            ))),
        min_count = min_count,
        threshold = 10,
        phrase_length = phrase_length // 2
    )

    logger.info('Extract non-māori phrases')
    sentences['discarded'] = phrase_model(
        sentences.words
              .apply(lambda x: ' '.join(
                   [y for y in x if y in non_maori_words]
              )),
        min_count = min_count,
        threshold = 10,
        phrase_length = phrase_length // 2
    )

    sentences['words'] = sentences.words.apply(lambda x: ' '.join(x))

    return sentences


@click.command()
@click.option('--paragraphs_csv', help='Path to paragraphs.csv')
@click.option('--sentences_csv', help='Path to sentences.csv')
@click.option('--min_count', type=int, help='Path to sentences.csv')
@click.option('--phrase_length', type=int, help='Max phrase length')
@click.option('--maori_min_percentage', default=0.5, type=float, help='Minimum percentage of māori words in a given sentence')
@click.option('--sentence_min_length', default=3, type=int, help='Minimum sentence length')
@click.option('--log_level', default='INFO', help='Log level (default: INFO)')
def main(paragraphs_csv, sentences_csv, min_count, phrase_length, maori_min_percentage, sentence_min_length, log_level):

    global logger
    logger = initialise_logger(log_level, __file__)

    paragraphs = pd.read_csv(paragraphs_csv)
    sentences = create_sentences(paragraphs, min_count, phrase_length, maori_min_percentage, sentence_min_length)

    logger.info('Save sentences to {}'.format(sentences_csv))
    sentences.to_csv(sentences_csv, index = False)

    logger.info('Done!')


if __name__ == '__main__':
    main()
