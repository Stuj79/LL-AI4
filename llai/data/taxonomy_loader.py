import os
import re
from typing import Dict, List, Optional

from .legal_taxonomy import LegalCategory, LegalTaxonomy

def load_taxonomy(resource_dir: str) -> LegalTaxonomy:
    """Load the legal taxonomy from resource files."""
    taxonomy = LegalTaxonomy()
    
    # Load parent categories
    parent_file = os.path.join(resource_dir, "law_categories/parent_categories.txt")
    with open(parent_file, "r", encoding='utf-8') as f:
        content = f.read()
    
    # Parse parent categories using regex
    parent_matches = re.finditer(r'\|\s*(\d+)\s*\|\s*([^|]+)\s*\|', content)
    parent_categories = {}
    
    for match in parent_matches:
        id_str, name = match.groups()
        try:
            id_num = int(id_str)
            parent_categories[id_num] = name.strip()
            
            # Extract description if present (text after parent category heading)
            category_header = f"## {id_num}. {name.strip()}"
            if category_header in content:
                section_start = content.find(category_header) + len(category_header)
                next_section = content.find("## ", section_start)
                if next_section == -1:
                    next_section = len(content)
                description = content[section_start:next_section].strip()
                
                # Create parent category
                category = LegalCategory(
                    id=id_num,
                    name=name.strip(),
                    description=description
                )
                taxonomy.add_category(category)
        except ValueError:
            continue
    
    # Load subcategories for each parent
    subcategory_dir = os.path.join(resource_dir, "law_categories/sub_categories")
    for file in os.listdir(subcategory_dir):
        if file.startswith("sub-categories-") and file.endswith(".txt"):
            parent_name = file[len("sub-categories-"):-4].replace("-", " ")
            parent_id = None
            
            # Find the parent ID
            for id_num, name in parent_categories.items():
                if name.lower() == parent_name.lower():
                    parent_id = id_num
                    break
            
            if parent_id is None:
                continue
                
            # Load subcategories
            with open(os.path.join(subcategory_dir, file), "r", encoding='utf-8') as f:
                subcontent = f.read()
            
            # Parse subcategories
            sub_matches = re.finditer(r'\|\s*(\d+)\s*\|\s*[^|]+\s*\|\s*([^|]+)\s*\|', subcontent)
            for sub_match in sub_matches:
                sub_id_str, sub_name = sub_match.groups()
                try:
                    sub_id = int(sub_id_str)
                    
                    # Extract description if present
                    sub_header = f"## {sub_id}. {sub_name.strip()}"
                    if sub_header in subcontent:
                        sub_section_start = subcontent.find(sub_header) + len(sub_header)
                        sub_next_section = subcontent.find("## ", sub_section_start)
                        if sub_next_section == -1:
                            sub_next_section = len(subcontent)
                        sub_description = subcontent[sub_section_start:sub_next_section].strip()
                        
                        # Create subcategory with globally unique ID (parent_id * 100 + sub_id)
                        global_id = parent_id * 100 + sub_id
                        subcategory = LegalCategory(
                            id=global_id,
                            name=sub_name.strip(),
                            parent_id=parent_id,
                            description=sub_description
                        )
                        taxonomy.add_category(subcategory)
                except ValueError:
                    continue
    
    return taxonomy
