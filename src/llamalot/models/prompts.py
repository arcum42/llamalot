"""
Data models for the prompts system.

Handles base prompts, extra prompts, and prompt configuration.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
import json
import os


@dataclass
class BasePrompt:
    """Represents a base prompt."""
    name: str
    category: str
    input_type: str
    prompt: str
    id: str = ""
    
    def __post_init__(self):
        if not self.id:
            self.id = self.name.lower().replace(' ', '_')


@dataclass 
class ExtraPrompt:
    """Represents an extra/additional prompt modifier."""
    name: str
    category: str
    type: str  # boolean, wildcard, etc.
    prompt: str
    id: str = ""
    default: Optional[bool] = None
    
    def __post_init__(self):
        if not self.id:
            self.id = self.name.lower().replace(' ', '_')


@dataclass
class PromptsConfig:
    """Configuration for the prompts system."""
    base_prompts: Dict[str, BasePrompt] = field(default_factory=dict)
    extra_prompts: Dict[str, ExtraPrompt] = field(default_factory=dict)
    categories: List[str] = field(default_factory=list)
    length_options: List[str] = field(default_factory=list)
    
    @classmethod
    def from_json_file(cls, file_path: str) -> 'PromptsConfig':
        """Load prompts configuration from JSON file."""
        if not os.path.exists(file_path):
            return cls()
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Parse base prompts
            base_prompts = {}
            if 'base' in data:
                for prompt_id, prompt_data in data['base'].items():
                    base_prompts[prompt_id] = BasePrompt(
                        id=prompt_id,
                        name=prompt_data.get('name', prompt_id),
                        category=prompt_data.get('category', 'general'),
                        input_type=prompt_data.get('input_type', 'text'),
                        prompt=prompt_data.get('prompt', '')
                    )
            
            # Parse extra prompts
            extra_prompts = {}
            if 'extra' in data:
                for prompt_id, prompt_data in data['extra'].items():
                    extra_prompts[prompt_id] = ExtraPrompt(
                        id=prompt_id,
                        name=prompt_data.get('name', prompt_id),
                        category=prompt_data.get('category', 'general'),
                        type=prompt_data.get('type', 'boolean'),
                        prompt=prompt_data.get('prompt', ''),
                        default=prompt_data.get('default')
                    )
            
            # Get categories from prompts
            categories = set()
            for prompt in base_prompts.values():
                categories.add(prompt.category)
            for prompt in extra_prompts.values():
                categories.add(prompt.category)
            
            # Get length options
            length_options = data.get('length', [])
            
            return cls(
                base_prompts=base_prompts,
                extra_prompts=extra_prompts,
                categories=sorted(list(categories)),
                length_options=length_options
            )
            
        except Exception as e:
            logger.error(f"Failed to load prompts from {file_path}: {e}")
            return cls()
    
    def to_json_file(self, file_path: str) -> bool:
        """Save prompts configuration to JSON file."""
        try:
            # Convert to JSON format
            data = {
                'base': {},
                'extra': {},
                'length': self.length_options
            }
            
            # Convert base prompts
            for prompt_id, prompt in self.base_prompts.items():
                data['base'][prompt_id] = {
                    'name': prompt.name,
                    'category': prompt.category,
                    'input_type': prompt.input_type,
                    'prompt': prompt.prompt
                }
            
            # Convert extra prompts
            for prompt_id, prompt in self.extra_prompts.items():
                extra_data = {
                    'name': prompt.name,
                    'category': prompt.category,
                    'type': prompt.type,
                    'prompt': prompt.prompt
                }
                if prompt.default is not None:
                    extra_data['default'] = prompt.default
                data['extra'][prompt_id] = extra_data
            
            # Write to file
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save prompts to {file_path}: {e}")
            return False
    
    def add_base_prompt(self, prompt: BasePrompt) -> bool:
        """Add a new base prompt."""
        if prompt.id in self.base_prompts:
            return False
        
        self.base_prompts[prompt.id] = prompt
        if prompt.category not in self.categories:
            self.categories.append(prompt.category)
            self.categories.sort()
        return True
    
    def update_base_prompt(self, prompt: BasePrompt) -> bool:
        """Update an existing base prompt."""
        if prompt.id not in self.base_prompts:
            return False
        
        old_category = self.base_prompts[prompt.id].category
        self.base_prompts[prompt.id] = prompt
        
        # Update categories if needed
        if prompt.category not in self.categories:
            self.categories.append(prompt.category)
            self.categories.sort()
        
        # Remove old category if no longer used
        if old_category != prompt.category and old_category in self.categories:
            if not any(p.category == old_category for p in self.base_prompts.values()):
                if not any(p.category == old_category for p in self.extra_prompts.values()):
                    self.categories.remove(old_category)
        
        return True
    
    def remove_base_prompt(self, prompt_id: str) -> bool:
        """Remove a base prompt."""
        if prompt_id not in self.base_prompts:
            return False
        
        old_category = self.base_prompts[prompt_id].category
        del self.base_prompts[prompt_id]
        
        # Remove category if no longer used
        if old_category in self.categories:
            if not any(p.category == old_category for p in self.base_prompts.values()):
                if not any(p.category == old_category for p in self.extra_prompts.values()):
                    self.categories.remove(old_category)
        
        return True
    
    def add_extra_prompt(self, prompt: ExtraPrompt) -> bool:
        """Add a new extra prompt."""
        if prompt.id in self.extra_prompts:
            return False
        
        self.extra_prompts[prompt.id] = prompt
        if prompt.category not in self.categories:
            self.categories.append(prompt.category)
            self.categories.sort()
        return True
    
    def update_extra_prompt(self, prompt: ExtraPrompt) -> bool:
        """Update an existing extra prompt."""
        if prompt.id not in self.extra_prompts:
            return False
        
        old_category = self.extra_prompts[prompt.id].category
        self.extra_prompts[prompt.id] = prompt
        
        # Update categories if needed
        if prompt.category not in self.categories:
            self.categories.append(prompt.category)
            self.categories.sort()
        
        # Remove old category if no longer used
        if old_category != prompt.category and old_category in self.categories:
            if not any(p.category == old_category for p in self.base_prompts.values()):
                if not any(p.category == old_category for p in self.extra_prompts.values()):
                    self.categories.remove(old_category)
        
        return True
    
    def remove_extra_prompt(self, prompt_id: str) -> bool:
        """Remove an extra prompt."""
        if prompt_id not in self.extra_prompts:
            return False
        
        old_category = self.extra_prompts[prompt_id].category
        del self.extra_prompts[prompt_id]
        
        # Remove category if no longer used
        if old_category in self.categories:
            if not any(p.category == old_category for p in self.base_prompts.values()):
                if not any(p.category == old_category for p in self.extra_prompts.values()):
                    self.categories.remove(old_category)
        
        return True
    
    def get_base_prompts_by_category(self, category: str) -> List[BasePrompt]:
        """Get all base prompts in a specific category."""
        return [p for p in self.base_prompts.values() if p.category == category]
    
    def get_extra_prompts_by_category(self, category: str) -> List[ExtraPrompt]:
        """Get all extra prompts in a specific category."""
        return [p for p in self.extra_prompts.values() if p.category == category]


# Import logger after defining the models to avoid circular imports
from llamalot.utils.logging_config import get_logger
logger = get_logger(__name__)
