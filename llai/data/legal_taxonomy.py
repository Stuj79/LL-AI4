from typing import Dict, List, Optional, Set

class LegalCategory:
    """Represents a legal category in the Canadian legal taxonomy."""
    
    def __init__(self, id: int, name: str, parent_id: Optional[int] = None, 
                 description: str = "", examples: List[str] = None):
        self.id = id
        self.name = name
        self.parent_id = parent_id
        self.description = description
        self.examples = examples or []
        self.subcategories: List[int] = []  # IDs of subcategories
        self.keywords: Set[str] = set()  # Key terms associated with this category

class LegalTaxonomy:
    """Manager for the Canadian legal taxonomy."""
    
    def __init__(self):
        self.categories: Dict[int, LegalCategory] = {}
        self.parent_categories: Dict[int, LegalCategory] = {}
        self.subcategory_map: Dict[int, List[int]] = {}  # parent_id -> list of subcategory ids
        self.name_to_id: Dict[str, int] = {}  # For lookups by name

    def add_category(self, category: LegalCategory) -> None:
        """Add a category to the taxonomy."""
        self.categories[category.id] = category
        self.name_to_id[category.name.lower()] = category.id
        
        # If it's a parent category
        if category.parent_id is None:
            self.parent_categories[category.id] = category
        # If it's a subcategory
        else:
            if category.parent_id not in self.subcategory_map:
                self.subcategory_map[category.parent_id] = []
            self.subcategory_map[category.parent_id].append(category.id)
            # Update the parent's subcategories list
            parent = self.categories.get(category.parent_id)
            if parent:
                parent.subcategories.append(category.id)

    def get_subcategories(self, parent_id: int) -> List[LegalCategory]:
        """Get all subcategories for a given parent category."""
        subcategory_ids = self.subcategory_map.get(parent_id, [])
        return [self.categories[id] for id in subcategory_ids]

    def get_category_by_name(self, name: str) -> Optional[LegalCategory]:
        """Look up a category by name (case-insensitive)."""
        category_id = self.name_to_id.get(name.lower())
        return self.categories.get(category_id)

    def get_all_parent_categories(self) -> List[LegalCategory]:
        """Get all parent categories."""
        return list(self.parent_categories.values())
