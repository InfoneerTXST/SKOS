#!/usr/local/bin/python
import rdflib
import skos as pyskos
import logging
import json
from requests.auth import HTTPBasicAuth
from collections import OrderedDict
from constants import *

logging.basicConfig(level=logging.INFO)     # use logging during the parsing process
AUTH = HTTPBasicAuth('ppuser', 'infoneer')
CORPUS_URL = "http://infoneer.poolparty.biz/PoolParty/api/corpusmanagement/" \
          "1DBC67E1-7669-0001-8A4A-F4B06F409540/results/" \
          "concepts?corpusId=corpus:7183eaa9-ddac-4a8f-82b6-1e62a31610fa&startIndex="


# TODO sort method
class SkosTool(object):

    """
     TODO doc
    """
    def __init__(self, rdf_path=None):
        self.rdf_file = rdf_path
        self.__g = rdflib.Graph()

        self.__g.parse(location=rdf_path, format='application/rdf+xml')
        self.__loader = pyskos.RDFLoader(self.__g, max_depth=1, flat=True)
        self.__sorted = False
        self.concepts = self.__loader.getConcepts()  # composition of the 'collections.MutableSet'

        # setup separate dict (with same keys) with a skeleton to house our calculated metrics
        self.metrics = {uri: {PREF_LABEL: '',
                              IMPORTANCE_SCORE: 0,
                              NUM_RELATIONS: 0,
                              NUM_EXTERNAL: 0,
                              FREQUENCY: 0} for uri in self.concepts}

    def parse(self):
        """
        TODO write docs
        """

        for uri in self.concepts:
            concept = self.concepts[uri]

            # set prefLabel in metrics dict
            if self.metrics[uri][PREF_LABEL] is '':
                self.metrics[uri][PREF_LABEL] = concept.prefLabel

            # gather and increment relation data in metric table
            if concept.related:
                for r in concept.related:
                    self.metrics[r][NUM_RELATIONS] += 1
                    self.metrics[r][IMPORTANCE_SCORE] += REL_SCORE_FACTOR

            if concept.synonyms:
                self.metrics[concept.uri][IMPORTANCE_SCORE] += EXTERNAL_LINK_FACTOR
                self.metrics[concept.uri][NUM_EXTERNAL] = len(concept.synonyms)


    def __normalize_on_max(self, max_score=None):
        """
        using the highest-scoring concept in the metrics dict, normalize all importance scores to keep them all
        below 1.00
        :param max_score: highest importance score
        """

        if max_score is None:
            max_score = max(float(d[IMPORTANCE_SCORE]) for d in self.metrics.values())
            for concept in self.metrics:
                previous = self.metrics[concept][IMPORTANCE_SCORE]
                self.metrics[concept][IMPORTANCE_SCORE] = round(previous / max_score, 4)
        else:
            for concept in self.metrics:
                previous = self.metrics[concept][IMPORTANCE_SCORE]
                self.metrics[concept][IMPORTANCE_SCORE] = round(previous / max_score, 4)

    def __normalize_on_sum(self, total=None):
        """
        using the sum of the set of importance scores, normalize so each score is a percentage out of 100
        :param total: total importance of the set
        """
        if total is not None:
            for concept in self.metrics:
                previous = self.metrics[concept][IMPORTANCE_SCORE]
                self.metrics[concept][IMPORTANCE_SCORE] = round(previous / total, 4)


    def get_metrics(self):
        """
        return metrics dict
        :return: dict of metrics
        """
        return self.metrics


    def sort(self):
        """
        sort based on highest importance score (descending order)
        """
        # TODO determine normalization better, you lazy ass
        self.__normalize_on_max()
        self.metrics = OrderedDict(sorted(self.metrics.items(), key=lambda t: t[1][IMPORTANCE_SCORE], reverse=True))
        self.__sorted = True


    # TODO remove before prod
    def is_sorted(self):
        return self.__sorted


    def get_frequencies(self, filename='corpus_data/frequencies.json'):
        """
        Get the term frequency value for each concept in the metrics dict from the locally-stored corpus data
        :param filename: path to term frequency data (JSON)
        :return:
        """
        # TODO handle both JSON and txt file possibilities


        with open(filename) as json_file:
            json_data = json.load(json_file)
            for uri in json_data:
                if uri in self.metrics:
                    self.metrics[uri][FREQUENCY] = json_data[uri]

        for uri in self.metrics:
            self.metrics[uri][IMPORTANCE_SCORE] = self.metrics[uri][IMPORTANCE_SCORE] + self.metrics[uri][FREQUENCY] + FREQ_SCORE_FACTOR






