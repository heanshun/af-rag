# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import Iterable
import networkx as nx


class NetworkxMixin:
    def _init_networkx_mixin(self):
        self.entity_neighbor_layer: int = self._retriever_config.get("entity_neighbor_layer", 1)

    def _get_subgraph_by_entity(self, graph: nx.Graph, entities: Iterable, neighbor_layer: int=None) -> nx.Graph:
        """Using the given `entities` to extract the sub-graph from the given `graph`. Entity nodes within
        `neighbor_layer` hops will be included.

        Returns:
            nx.Graph: the sub-graph filtered by entities.
        """
        if neighbor_layer is None:
            neighbor_layer = self.entity_neighbor_layer

        entity_set = set(entities)
        newly_added: set = entity_set.copy()
        for _ in range(neighbor_layer):
            tmp_set = set()
            for entity in newly_added:
                for neighbor in graph.neighbors(entity):
                    if neighbor not in entity_set:
                        tmp_set.add(neighbor)

            newly_added = tmp_set
            for entity in newly_added:
                entity_set.add(newly_added)

        return graph.subgraph(nodes=entity_set)
