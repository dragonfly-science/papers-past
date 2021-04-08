docker_registry := "mathematiguy"
git_tag := `git log --oneline | head -n1 | awk '{print $1}'`
repo_name:= `basename $(git rev-parse --show-toplevel) | tr '[:upper:]' '[:lower:]'`
image := docker_registry + "/" + repo_name
profile := "default"
run := "docker run --rm -v $(pwd):/code -w /code"


see:
    snakemake -j 1 -n -p --verbose

try:
    snakemake -j 15 -k -p --verbose

do:
    snakemake -j 15 -p

dag:
    snakemake --dag | dot -Tpdf > dag.pdf

rules:
    snakemake --rulegraph | dot -Tpdf > dag.pdf

clean:
    rm -rf data/unzipped/*

jupyter_password := "jupyter"
jupyter:
    {{run}} -u root:root -p 8888:8888 {{image}} jupyter lab \
        --allow-root \
        --port 8888 \
        --ip 0.0.0.0 \
        --NotebookApp.password=$({{run}} {{image}} \
        python3 -c "from IPython.lib import passwd; print(passwd('{{jupyter_password}}'))")

num_cores := `expr $(grep -c ^processor /proc/cpuinfo) - 1`
docker:
    docker build --tag {{docker_registry}}/{{repo_name}}:{{git_tag}} --build-arg NUM_CORES={{num_cores}} .
    docker tag {{image}} {{image}}/{{git_tag}} && docker push {{image}}:{{git_tag}}
    docker tag {{image}} {{image}}:latest && docker push {{image}}:latest
    docker push {{image}}
