#!/usr/bin/env python3
"""
This script is meant to generate workshop assignments based
on what is provided in softconf.

The logic is:
    - Select all papers who don't have an author in common (as determined
      by the all_author_emails information)
"""
import re
from typing import Generator, Tuple

from winlp_scripts.softconf import SoftconfConnection
from winlp_scripts.utils import load_yml
from argparse import ArgumentParser
from collections import defaultdict
from pandas import DataFrame

# igraph
from igraph import Graph, Matching, Edge

def build_graph(submissions: DataFrame) -> Graph:
    """
    Build a bipartite graph from the submissions

    """
    # Keep an index of what author emails are associated
    # with what submissions, and vice-versa
    subs_to_authors = defaultdict(set)

    # Initialize a graph, where the vertices are
    # all of the submission IDs.
    g = Graph()

    # print([sub_id[1] for sub_id in submission_info['Submission ID']])
    sub_ids = sorted(list(submissions['Submission ID']))

    # Shuffle the src/tgt just to get
    # more randomized pairings
    from random import Random
    r = Random()
    shuffled_src = sub_ids.copy()
    r.shuffle(shuffled_src)
    shuffled_tgt = sub_ids.copy()
    r.shuffle(shuffled_tgt)

    # Add all the sub_ids as vertices as both potential sources
    # and targets
    for sub_id in shuffled_src:
        g.add_vertex('src_{}'.format(sub_id), type=0)
    for sub_id in shuffled_tgt:
        g.add_vertex('tgt_{}'.format(sub_id), type=1)

    # Build the mappings of which submissions have which authors
    for row_id, row in submissions.iterrows():
        submission_id = row['Submission ID']
        main_email = row['Main Contact Email']
        other_emails = set(re.split('[;\s]+', row['All Author Emails']))
        all_emails = set([main_email]) | other_emails
        subs_to_authors[submission_id] |= all_emails

    print(sub_ids)



    for src_sub in shuffled_src:
        emails_i = subs_to_authors[src_sub]
        for tgt_sub in shuffled_tgt:
            emails_j = subs_to_authors[tgt_sub]
            # Two submissions should only be connected
            # if they have no overlapping authors.
            if not (emails_i & emails_j):
                g.add_edge('src_{}'.format(src_sub), 'tgt_{}'.format(tgt_sub))

    return g

def retrieve_pairs(graph: Graph, matching: Matching) -> Generator[Tuple[int, int], None, None]:
    """
    Given the graph matching, return a list
    of submission ID pairs that will be
    paired for workshopping.
    """
    vertices = graph.vs
    for edge in matching.edges(): # type: Edge
        source_vertex = vertices[edge.source]
        source_name = source_vertex['name'][4:]
        target_vertex = vertices[edge.target]
        target_name = target_vertex['name'][4:]


        if source_vertex['type'] == 0:
            yield(int(source_name), int(target_name))
        else:
            yield(int(target_name), int(source_name))



def do_assignments(conf):
    """
    Retrieve the submission information from Softconf,
    and determine which submissions should be sent
    to which other workshop participants.
    """
    scc = SoftconfConnection.from_conf(conf)
    submission_info = scc.submission_information()

    sub_id_to_authors = {row_data['Submission ID']:row_data for row_id, row_data in submission_info.iterrows()}

    # -- 1) Build a bipartite graph of submission pairings.
    graph = build_graph(submission_info)

    # -- 2) Find a maximal matching graph
    matching = graph.maximum_bipartite_matching()
    assert matching.is_maximal()

    # -- 3) Retrieve the pairings
    assignments = retrieve_pairs(graph, matching)

    # -- 4) Given these pairings,
    # Find the match for each source vertex...
    for source_id, tgt_id in assignments:
        source_sub = sub_id_to_authors[source_id]
        tgt_sub = sub_id_to_authors[tgt_id]

        print('{} will be assigned to read over the paper for {}'.format(source_sub['Main Contact Username'],
                                                                         tgt_sub['Main Contact Username']))






if __name__ == '__main__':
    p = ArgumentParser()
    p.add_argument('-c', '--conf', default='config.yml', type=load_yml)

    args = p.parse_args()

    do_assignments(args.conf)