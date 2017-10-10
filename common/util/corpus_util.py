#!/usr/local/bin/python
import json
import requests
from requests.auth import HTTPBasicAuth
from constants import *
from skos_tool import AUTH
import os.path

CORPUS_URL = "http://infoneer.poolparty.biz/PoolParty/api/corpusmanagement/" \
          "1DBC67E1-7669-0001-8A4A-F4B06F409540/results/" \
          "concepts?corpusId=corpus:7183eaa9-ddac-4a8f-82b6-1e62a31610fa&startIndex="



def __parse_corpus_response(response):
    """
    parse json response into dict with concept uri as key, and term-frequency as value
    :param response: api response
    :return: dict of concepts and their frequencies
    """
    concepts = {}
    for con in response.json():
        name = con['concept']['uri'].encode('utf-8')
        freq = con['frequency']
        concepts[name] = freq

        # concepts[name.lower()] = freq
    return concepts


def __query_corpus(idx=0):
    """
    Query PP API for extracted concepts and their term frequencies. Only 20 concepts per request allowed.
    :param idx: index from which to retrieve extracted concepts from api
    :return: json representation of concept and its corpus data
    """
    url = CORPUS_URL + str(idx)

    result = requests.get(url, auth=AUTH)

    if result.text == '[]' or result.text == '[ ]':
        return None
    else:
        return result



def get_corpus_data(corpus_file='corpus_data/frequencies.json', corpus_id='0', project_id='0'):
    """
    Using the PP API, query the corpus with the current thesaurus to extract term frequency to save locally. Call this
    method when you want to sync to the PP API data.
    :param corpus_file: path to local term frequency data
    """
    idx = 0

    if (os.path.exists(corpus_file)):
        return

    global CORPUS_URL
    CORPUS_URL = "http://infoneer.poolparty.biz/PoolParty/api/corpusmanagement/" + project_id + "/results/" \
                 "concepts?corpusId=corpus:" + corpus_id + "&startIndex="

    response = __query_corpus(idx)
    extracted_concepts = {}
    while response is not None:

        extracted_concepts.update(__parse_corpus_response(response))    # append dict of frequencies
        idx += 20
        response = __query_corpus(idx)

    with open(corpus_file, 'w') as outfile:
        json.dump(extracted_concepts, outfile)

