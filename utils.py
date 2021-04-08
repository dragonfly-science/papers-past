import os
import re
import tarfile
from tqdm import tqdm
import itertools as it
from functools import partial
from multiprocessing import cpu_count
from concurrent.futures import ProcessPoolExecutor, as_completed

# Detect if filepath corresponds to a newspaper article
is_newspaper_xml = re.compile('[0-9]+.xml')


def multicore_apply(array, func, n_jobs=cpu_count()-1, use_kwargs=False,
                    front_num=0):
    """
        A parallel version of the map func with a progress bar.

        Args:
            array (array-like): An array to iterate over.
            func (func): A python func to apply to the elements of array
            n_jobs (int, default=16): The number of cores to use
            use_kwargs (boolean, default=False): Whether to consider the
            elements of array as dictionaries of keyword arguments to func
            front_num (int, default=3): The number of iterations to run
            serially before kicking off the parallel job.
                Useful for catching bugs
        Returns:
            [func(array[0]), func(array[1]), ...]
    """

    array = list(array)

    # We run the first few iterations serially to catch bugs
    front = []
    if front_num > 0:
        front = [func(**a) if use_kwargs else func(a)
                 for a in array[:front_num]]
    # If we set n_jobs to 1, just run a list comprehension. This is useful for
    # benchmarking and debugging.
    if n_jobs == 1:
        return front + [func(**a) if use_kwargs else func(a)
                        for a in tqdm(array[front_num:])]
    # Assemble the workers
    with ProcessPoolExecutor(max_workers=n_jobs) as pool:
        # Pass the elements of array into func
        if use_kwargs:
            futures = [pool.submit(func, **a) for a in array[front_num:]]
        else:
            futures = [pool.submit(func, a) for a in array[front_num:]]
        kwargs = {
            'total': len(futures),
            'unit': 'it',
            'unit_scale': True,
            'leave': True
        }
        # Print out the progress as tasks complete
        for f in tqdm(as_completed(futures), **kwargs):
            pass
    out = []
    # Get the results from the futures.
    for i, future in tqdm(enumerate(futures)):
        try:
            out.append(future.result())
        except Exception as e:
            out.append(e)
    return front + out


# Extract the archive name from the tar.gz filename
def get_basename(fp):
    return os.path.basename(fp).split('.')[0]


def list_tar(tar, data_path):
    '''
    Returns a list of all articles under the given `tar`,
    which is a tar.gz file
    '''
    members = []
    for member in tarfile.open(tar, 'r:gz').getnames():
        if is_newspaper_xml.search(member):
            members.append(os.path.join(data_path, member))
    return members


def list_articles(tar_files, data_path):
    '''
    Returns a list of all the articles under each tar.gz
    file in the `tar_dir` directory
    '''
    return list(it.chain.from_iterable(
        multicore_apply(tar_files, partial(list_tar, data_path=data_path)))
        )


def get_wildcards(articles):

    newspapers = []
    years = []
    newspaper_dates = []
    articles = []
    pattern = re.compile(r'([A-Z]+)/([0-9]+)/([A-Z]+_[0-9]+)/MM_01/([0-9]+)\.xml')

    for article in articles:
        newspaper, year, newspaper_date, article = pattern.findall(path)[0]
        newspapers.append(newspaper)
        years.append(year)
        newspaper_dates.append(newspaper_date)
        articles.append(article)

    return dict(
        newspaper = newspapers,
        year = years,
        newspaper_date = newspaper_dates,
        article = articles
    )


def get_newspaper_date(path):
    p = re.compile(r'([A-Z]+_[0-9]+)/MM_01')
    newspaper_date = p.findall(path)[0]
    return newspaper_date


def get_article(path):
    p = re.compile(r'MM_01/([0-9]+)\.xml')
    article = p.findall(path)[0]
    return article
