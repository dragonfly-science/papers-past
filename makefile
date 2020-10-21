DOCKER_REGISTRY := mathematiguy
IMAGE_NAME := $(shell basename `git rev-parse --show-toplevel` | tr '[:upper:]' '[:lower:]')
IMAGE := $(DOCKER_REGISTRY)/$(IMAGE_NAME)
RUN ?= docker run $(DOCKER_ARGS) --rm -v $$(pwd):/code -w $(WORK_DIR) -u $(UID):$(GID) $(IMAGE)
UID ?= $(shell id -u)
GID ?= $(shell id -g)
WORK_DIR ?= /code
DOCKER_ARGS ?=
GIT_TAG ?= $(shell git log --oneline | head -n1 | awk '{print $$1}')
LOG_LEVEL ?= INFO
NUM_CORES ?= $(shell expr `grep -Pc '^processor\t' /proc/cpuinfo` - 1)
DATA_DIR ?= data
PAPERS_DIR ?= data/papers

# Parameters
MIN_COUNT ?= 30  # Minimum number of occurrences to keep a word in the corpus

.PHONY: starmap wordmap crawl shiny r_session jupyter ipython clean docker \
	docker-push docker-pull enter enter-root

all: $(PAPERS_DIR)/starmap.json

crawl: $(PAPERS_DIR)/papers.json
$(PAPERS_DIR)/papers.json:
	$(RUN) bash -c "cd papers_past && scrapy crawl papers \
		-o $(PAPERS_DIR)/papers.json \
		-a old_output=$(PAPERS_DIR)/papers.json \
		-a start_urls=start_urls.json \
		-L $(LOG_LEVEL)"

notebooks: $(shell ls -d analysis/*.Rmd | sed 's/.Rmd/.pdf/g')

analysis/%.pdf: analysis/%.Rmd
	$(RUN) Rscript -e 'rmarkdown::render("$<")'

$(PAPERS_DIR)/papers.csv: embeddings/scripts/create_papers.py $(PAPERS_DIR)/papers.json
	$(RUN) python3 $< \
		--papers_json $(PAPERS_DIR)/papers.json \
		--papers_csv $@ \
		--log_level $(LOG_LEVEL)

$(PAPERS_DIR)/paragraphs.csv: embeddings/scripts/create_paragraphs.py $(PAPERS_DIR)/papers.csv
	$(RUN) python3 $< \
		--papers_csv $(PAPERS_DIR)/papers.csv \
		--paragraphs_csv $@ \
		--log_level $(LOG_LEVEL)

$(PAPERS_DIR)/sentences.csv: embeddings/scripts/create_sentences.py $(PAPERS_DIR)/paragraphs.csv
	$(RUN) python3 $< \
		--paragraphs_csv $(PAPERS_DIR)/paragraphs.csv \
		--sentences_csv $@ \
		--min_count $(MIN_COUNT) \
		--log_level $(LOG_LEVEL)

$(PAPERS_DIR)/corpus.txt: embeddings/scripts/create_corpus.py $(PAPERS_DIR)/sentences.csv
	$(RUN) python3 $< --sentence_csv $(PAPERS_DIR)/sentences.csv \
		--corpus_file $(PAPERS_DIR)/corpus.txt \
		--log_level $(LOG_LEVEL)

$(PAPERS_DIR)/corpus.shuf: $(PAPERS_DIR)/corpus.txt
	cat $< | shuf > $@

$(PAPERS_DIR)/corpus.train: $(PAPERS_DIR)/corpus.shuf
	head $< -n $(shell expr `wc -l $< | awk '{print $$1}'` \* 8 / 10) > $@

$(PAPERS_DIR)/corpus.test: $(PAPERS_DIR)/corpus.shuf
	tail $< -n +$(shell expr `wc -l $< | awk '{print $$1}'` \* 8 / 10 + 1) > $@

MAX_N ?= 6
AUTOTUNE_DURATION ?= 30
$(PAPERS_DIR)/fasttext_cbow.bin: $(PAPERS_DIR)/corpus.train $(PAPERS_DIR)/corpus.test
	$(RUN) fasttext cbow -input $< -output $(basename $@) -minCount $(MIN_COUNT) \
		-thread $(NUM_CORES) -autotune-duration $(AUTOTUNE_DURATION) -maxn $(MAX_N) \
		-autotune-validation $(PAPERS_DIR)/corpus.test

$(PAPERS_DIR)/word_counts.txt: $(PAPERS_DIR)/corpus.txt
	$(RUN) cat $< | grep -oE '[a-zāēīōū_]+' | sort | uniq -c | sort -nr | awk '($$1 >= $(MIN_COUNT))' > $@

N_NEIGHBOURS ?= 4
MIN_DIST ?= 0.8
METRIC ?= euclidean
$(PAPERS_DIR)/umap.csv: embeddings/scripts/create_umap.py $(PAPERS_DIR)/fasttext_cbow.bin $(PAPERS_DIR)/word_counts.txt
	$(RUN) python3 $< --word_vectors $(PAPERS_DIR)/fasttext_cbow.vec \
		--word_counts $(PAPERS_DIR)/word_counts.txt --umap_file $@ \
		--n_neighbours $(N_NEIGHBOURS) --min_dist $(MIN_DIST) --metric $(METRIC) \
		--log_level $(LOG_LEVEL)

starmap/starmap.json: embeddings/scripts/create_starmap.py $(PAPERS_DIR)/umap.csv
	$(RUN) python3 $< --umap_csv $(PAPERS_DIR)/umap.csv --umap_json $@ --log_level $(LOG_LEVEL)

starmap/dist/index.html: UID=root
starmap/dist/index.html: GID=root
starmap/dist/index.html: starmap/starmap.json
	$(RUN) bash -c 'cd starmap && npm i && npm run build'

starmap: DOCKER_ARGS=-p 8000:8000
starmap: starmap/dist/index.html
	$(RUN) bash -c 'cd starmap/dist && python3 -m http.server'

wordmap: DOCKER_ARGS=-p 8000:8000
wordmap: wordmap/newspapers/umap.csv
	$(RUN) python3 -m http.server

wordmap/newspapers/umap.csv: $(PAPERS_DIR)/umap.csv
	cp $< $@

wordmap/newspapers/umap.csv: $(PAPERS_DIR)/umap.csv
	cp $< $@

shiny: DOCKER_ARGS= -p 7727:7727
shiny:
	$(RUN) Rscript shiny/global.R

r_session: DOCKER_ARGS= -dit --rm -e DISPLAY=$$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix:ro --name="rdev"
r_session:
	$(RUN) R

JUPYTER_PASSWORD ?= jupyter
JUPYTER_PORT ?= 8888
jupyter: UID=root
jupyter: GID=root
jupyter: DOCKER_ARGS=-u $(UID):$(GID) --rm -it -p $(JUPYTER_PORT):$(JUPYTER_PORT) -e NB_USER=$$USER -e NB_UID=$(UID) -e NB_GID=$(GID)
jupyter:
	$(RUN) jupyter lab \
		--allow-root \
		--port $(JUPYTER_PORT) \
		--ip 0.0.0.0 \
		--NotebookApp.password=$(shell $(RUN) \
			python3 -c \
			"from IPython.lib import passwd; print(passwd('$(JUPYTER_PASSWORD)'))")

ipython: DOCKER_ARGS=-it
ipython:
	$(RUN) ipython --no-autoindent

clean:
	rm -rf data/papers/*

docker:
	docker build $(DOCKER_ARGS) --tag $(IMAGE):$(GIT_TAG) .
	docker tag $(IMAGE):$(GIT_TAG) $(IMAGE):latest

docker-push:
	docker push $(IMAGE):$(GIT_TAG)
	docker push $(IMAGE):latest

docker-pull:
	docker pull $(IMAGE):$(GIT_TAG)
	docker tag $(IMAGE):$(GIT_TAG) $(IMAGE):latest

enter: DOCKER_ARGS=-it
enter:
	$(RUN) bash

enter-root: DOCKER_ARGS=-it
enter-root: UID=root
enter-root: GID=root
enter-root:
	$(RUN) bash
