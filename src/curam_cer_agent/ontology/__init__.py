"""
Ontology loading, reasoning, and validation.

Provides the semantic layer for eligibility determination using
OWL ontology and SPARQL queries. No direct LLM inference here —
pure rule-based evaluation against the ontology.
"""

from curam_cer_agent.ontology.loader import OntologyLoader
from curam_cer_agent.ontology.reasoner import OntologyReasoner
from curam_cer_agent.ontology.validator import OntologyValidator

__all__ = ["OntologyLoader", "OntologyReasoner", "OntologyValidator"]
