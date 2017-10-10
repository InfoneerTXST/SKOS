#!/usr/local/bin/python

REL_SCORE_FACTOR = 0.300
FREQ_SCORE_FACTOR = 0.500
EXTERNAL_LINK_FACTOR = 0.200

IMPORTANCE_SCORE = 'importance'     # overall importance metric we calculate
PREF_LABEL = 'prefLabel'            # human-readable label for the concept
RELATEDS = 'relateds'               # actual list of concepts defined as related
NUM_RELATIONS = 'num_relations'     # number of times 'this' concept has been linked to as related from other concepts
NUM_EXTERNAL = 'num_external'       # number of instances of an externally matched concept
FREQUENCY = 'frequency'             # term frequency in corpus documents

# externally-linked concept properties
EXACT_MATCH = 'exactMatch'
CLOSE_MATCH = 'closeMatch'
BROADER_MATCH = 'broaderMatch'
NARROWER_MATCH = 'narrowerMatch'
RELATED_MATCH = 'relatedMatch'

EXTERNAL_PROPERTIES = [EXACT_MATCH,
                       CLOSE_MATCH,
                       BROADER_MATCH,
                       NARROWER_MATCH,
                       RELATED_MATCH]
