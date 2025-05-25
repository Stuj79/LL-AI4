from .legal_taxonomy import LegalTaxonomy
from .taxonomy_loader import load_taxonomy
from .taxonomy_enricher import enrich_taxonomy
import os

# Singleton pattern - initialize once
_TAXONOMY = None

def get_taxonomy() -> LegalTaxonomy:
    """Get the initialized legal taxonomy."""
    global _TAXONOMY
    if _TAXONOMY is None:
        # Get the path to the resources directory
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        resources_dir = os.path.join(os.path.dirname(base_dir), "llai", "resources")
        
        # Load and enrich the taxonomy
        _TAXONOMY = load_taxonomy(resources_dir)
        _TAXONOMY = enrich_taxonomy(_TAXONOMY)
    
    return _TAXONOMY
