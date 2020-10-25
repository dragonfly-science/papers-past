#/bin/bash
set -ex

export RUN=
export AUTOTUNE_DURATION=600

# Hyperparameters
export MIN_COUNT=30
export PHRASE_LENGTH=4
export MAX_N=6
export N_NEIGHBOURS=5
export MIN_DIST=0.8
export RADIUS=1000
export PRECISION=4

cd ..

cp /input/papers-past-crawler/papers.json data/papers

make all

# Show file sizes for output
du -sh data/papers/*

mv data/papers/corpus.txt data/papers/corpus.train \
   data/papers/corpus.test data/papers/word_counts.txt \
   data/papers/fasttext_cbow.bin data/papers/fasttext_cbow.vec \
   data/papers/*.csv starmap/starmap.json /output
