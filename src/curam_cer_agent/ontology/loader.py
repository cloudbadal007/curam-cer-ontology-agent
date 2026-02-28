"""
Ontology loader and caching.

Loads OWL/Turtle ontology files into an rdflib graph, with optional
caching for performance. Supports eligibility_core, snap_rules, and medicaid_rules.
"""

import logging
from pathlib import Path
from typing import Optional

from rdflib import Graph, Namespace

from curam_cer_agent.utils.config import get_ontology_path

logger = logging.getLogger(__name__)

# In-memory cache for loaded ontology graph
_cached_graph: Optional[Graph] = None
_cached_path: Optional[Path] = None

# Ontology namespaces
ELIG = Namespace("http://curam.cer.ontology/eligibility#")
SNAP = Namespace("http://curam.cer.ontology/snap#")
MEDICAID = Namespace("http://curam.cer.ontology/medicaid#")


class OntologyLoader:
    """
    Loads and caches the eligibility ontology as an RDF graph.

    Supports multiple ontology files: core + program-specific (SNAP, Medicaid).
    Uses rdflib for parsing; owlready2 is optional for advanced reasoning.
    """

    def __init__(self, ontology_path: Optional[Path] = None):
        """
        Initialize the loader.

        Args:
            ontology_path: Path to core ontology. Defaults to config/dotenv.
        """
        self._ontology_path = ontology_path or get_ontology_path()
        self._ontology_dir = self._ontology_path.parent

    def load(self, use_cache: bool = True) -> Graph:
        """
        Load the ontology into an rdflib Graph.

        Loads eligibility_core.ttl, snap_rules.ttl, and medicaid_rules.ttl
        from the ontology directory. Results are cached when use_cache=True.

        Returns:
            rdflib.Graph containing the merged ontology.

        Raises:
            FileNotFoundError: If ontology files are not found.
        """
        global _cached_graph, _cached_path

        if use_cache and _cached_graph is not None and _cached_path == self._ontology_path:
            logger.debug("Using cached ontology graph")
            return _cached_graph

        if not self._ontology_path.exists():
            raise FileNotFoundError(
                f"Ontology file not found: {self._ontology_path}"
            )

        g = Graph()
        g.bind("elig", ELIG)
        g.bind("snap", SNAP)
        g.bind("medicaid", MEDICAID)

        # Load core ontology
        g.parse(self._ontology_path, format="turtle")
        logger.info("Loaded ontology: %s", self._ontology_path.name)

        # Load snap_rules if present (it imports core via its own ontology URI)
        snap_path = self._ontology_dir / "snap_rules.ttl"
        if snap_path.exists():
            g.parse(snap_path, format="turtle")
            logger.info("Loaded ontology: snap_rules.ttl")

        # Load medicaid_rules stub if present
        medicaid_path = self._ontology_dir / "medicaid_rules.ttl"
        if medicaid_path.exists():
            g.parse(medicaid_path, format="turtle")
            logger.info("Loaded ontology: medicaid_rules.ttl")

        if use_cache:
            _cached_graph = g
            _cached_path = self._ontology_path

        return g

    def clear_cache(self) -> None:
        """Clear the ontology cache. Useful for testing."""
        global _cached_graph, _cached_path
        _cached_graph = None
        _cached_path = None
        logger.debug("Ontology cache cleared")
