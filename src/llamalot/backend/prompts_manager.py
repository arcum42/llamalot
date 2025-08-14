"""
Prompts manager for handling prompt templates and modifications.

Manages loading, saving, and manipulation of base prompts and extra prompt modifiers.
"""

import os
from typing import Optional, List, Dict, Any
from logging import getLogger

from llamalot.models.prompts import PromptsConfig, BasePrompt, ExtraPrompt

logger = getLogger(__name__)


class PromptsManager:
    """Manages prompt templates and configuration."""
    
    def __init__(self, config_dir: str):
        """Initialize the prompts manager.
        
        Args:
            config_dir: Directory where the prompts configuration will be stored
        """
        self.config_dir = config_dir
        self.prompts_file = os.path.join(config_dir, 'prompts.json')
        self.config = PromptsConfig()
        
        # Ensure config directory exists
        os.makedirs(config_dir, exist_ok=True)
        
        # Load existing configuration
        self.load_config()
    
    def load_config(self) -> bool:
        """Load prompts configuration from file."""
        try:
            # Try to load from the user config first
            if os.path.exists(self.prompts_file):
                self.config = PromptsConfig.from_json_file(self.prompts_file)
                logger.info(f"Loaded prompts configuration from {self.prompts_file}")
                return True
            else:
                # Try to load from the default llm_prompts.json in project root
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                default_prompts_file = os.path.join(project_root, 'llm_prompts.json')
                
                if os.path.exists(default_prompts_file):
                    self.config = PromptsConfig.from_json_file(default_prompts_file)
                    # Save it to user config location
                    self.save_config()
                    logger.info(f"Loaded default prompts from {default_prompts_file}")
                    return True
                else:
                    logger.warning("No prompts configuration found, using empty config")
                    self.config = PromptsConfig()
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to load prompts configuration: {e}")
            self.config = PromptsConfig()
            return False
    
    def save_config(self) -> bool:
        """Save current prompts configuration to file."""
        try:
            success = self.config.to_json_file(self.prompts_file)
            if success:
                logger.info(f"Saved prompts configuration to {self.prompts_file}")
            return success
        except Exception as e:
            logger.error(f"Failed to save prompts configuration: {e}")
            return False
    
    def get_base_prompts(self) -> Dict[str, BasePrompt]:
        """Get all base prompts."""
        return self.config.base_prompts.copy()
    
    def get_extra_prompts(self) -> Dict[str, ExtraPrompt]:
        """Get all extra prompts."""
        return self.config.extra_prompts.copy()
    
    def get_categories(self) -> List[str]:
        """Get all available categories."""
        return self.config.categories.copy()
    
    def get_base_prompts_by_category(self, category: str) -> List[BasePrompt]:
        """Get base prompts filtered by category."""
        return self.config.get_base_prompts_by_category(category)
    
    def get_extra_prompts_by_category(self, category: str) -> List[ExtraPrompt]:
        """Get extra prompts filtered by category."""
        return self.config.get_extra_prompts_by_category(category)
    
    def add_base_prompt(self, name: str, category: str, input_type: str, prompt: str) -> bool:
        """Add a new base prompt."""
        try:
            new_prompt = BasePrompt(
                name=name,
                category=category,
                input_type=input_type,
                prompt=prompt
            )
            
            if self.config.add_base_prompt(new_prompt):
                self.save_config()
                logger.info(f"Added base prompt: {name}")
                return True
            else:
                logger.warning(f"Base prompt already exists: {name}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to add base prompt: {e}")
            return False
    
    def update_base_prompt(self, prompt_id: str, name: str, category: str, input_type: str, prompt: str) -> bool:
        """Update an existing base prompt."""
        try:
            updated_prompt = BasePrompt(
                id=prompt_id,
                name=name,
                category=category,
                input_type=input_type,
                prompt=prompt
            )
            
            if self.config.update_base_prompt(updated_prompt):
                self.save_config()
                logger.info(f"Updated base prompt: {name}")
                return True
            else:
                logger.warning(f"Base prompt not found: {prompt_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update base prompt: {e}")
            return False
    
    def remove_base_prompt(self, prompt_id: str) -> bool:
        """Remove a base prompt."""
        try:
            if self.config.remove_base_prompt(prompt_id):
                self.save_config()
                logger.info(f"Removed base prompt: {prompt_id}")
                return True
            else:
                logger.warning(f"Base prompt not found: {prompt_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to remove base prompt: {e}")
            return False
    
    def add_extra_prompt(self, name: str, category: str, type: str, prompt: str, default: Optional[bool] = None) -> bool:
        """Add a new extra prompt."""
        try:
            new_prompt = ExtraPrompt(
                name=name,
                category=category,
                type=type,
                prompt=prompt,
                default=default
            )
            
            if self.config.add_extra_prompt(new_prompt):
                self.save_config()
                logger.info(f"Added extra prompt: {name}")
                return True
            else:
                logger.warning(f"Extra prompt already exists: {name}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to add extra prompt: {e}")
            return False
    
    def update_extra_prompt(self, prompt_id: str, name: str, category: str, type: str, prompt: str, default: Optional[bool] = None) -> bool:
        """Update an existing extra prompt."""
        try:
            updated_prompt = ExtraPrompt(
                id=prompt_id,
                name=name,
                category=category,
                type=type,
                prompt=prompt,
                default=default
            )
            
            if self.config.update_extra_prompt(updated_prompt):
                self.save_config()
                logger.info(f"Updated extra prompt: {name}")
                return True
            else:
                logger.warning(f"Extra prompt not found: {prompt_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update extra prompt: {e}")
            return False
    
    def remove_extra_prompt(self, prompt_id: str) -> bool:
        """Remove an extra prompt."""
        try:
            if self.config.remove_extra_prompt(prompt_id):
                self.save_config()
                logger.info(f"Removed extra prompt: {prompt_id}")
                return True
            else:
                logger.warning(f"Extra prompt not found: {prompt_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to remove extra prompt: {e}")
            return False
    
    def build_final_prompt(self, base_prompt_id: str, selected_extras: List[str], 
                          wildcard_values: Optional[Dict[str, str]] = None) -> str:
        """Build a final prompt from base prompt and selected extras.
        
        Args:
            base_prompt_id: ID of the base prompt to use
            selected_extras: List of extra prompt IDs to include
            wildcard_values: Dictionary of wildcard replacements {extra_id: value}
            
        Returns:
            The combined prompt text
        """
        if wildcard_values is None:
            wildcard_values = {}
            
        # Get base prompt
        if base_prompt_id not in self.config.base_prompts:
            return ""
        
        base_prompt = self.config.base_prompts[base_prompt_id]
        prompt_parts = [base_prompt.prompt]
        
        # Add selected extra prompts
        for extra_id in selected_extras:
            if extra_id in self.config.extra_prompts:
                extra_prompt = self.config.extra_prompts[extra_id]
                extra_text = extra_prompt.prompt
                
                # Handle wildcard replacement
                if extra_prompt.type == 'wildcard' and extra_id in wildcard_values:
                    extra_text = extra_text.replace('{string}', wildcard_values[extra_id])
                
                prompt_parts.append(extra_text)
        
        # Combine all parts
        return ' '.join(prompt_parts).strip()
    
    def get_prompt_statistics(self) -> Dict[str, Any]:
        """Get statistics about the prompts configuration."""
        return {
            'total_base_prompts': len(self.config.base_prompts),
            'total_extra_prompts': len(self.config.extra_prompts),
            'categories': len(self.config.categories),
            'category_breakdown': {
                category: {
                    'base': len(self.get_base_prompts_by_category(category)),
                    'extra': len(self.get_extra_prompts_by_category(category))
                }
                for category in self.config.categories
            }
        }
    
    def sync_from_defaults(self) -> Dict[str, int]:
        """Sync prompts from the default llm_prompts.json file.
        
        Adds any prompts that exist in the default file but not in the current config.
        Does not overwrite existing prompts.
        
        Returns:
            Dictionary with counts of added prompts: {'base': count, 'extra': count}
        """
        added_counts = {'base': 0, 'extra': 0}
        
        try:
            # Find the default prompts file
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            default_prompts_file = os.path.join(project_root, 'llm_prompts.json')
            
            if not os.path.exists(default_prompts_file):
                logger.warning(f"Default prompts file not found at {default_prompts_file}")
                return added_counts
            
            # Load default configuration
            default_config = PromptsConfig.from_json_file(default_prompts_file)
            
            # Add missing base prompts
            for prompt_id, base_prompt in default_config.base_prompts.items():
                if prompt_id not in self.config.base_prompts:
                    self.config.base_prompts[prompt_id] = base_prompt
                    added_counts['base'] += 1
                    logger.info(f"Added base prompt: {base_prompt.name}")
            
            # Add missing extra prompts  
            for prompt_id, extra_prompt in default_config.extra_prompts.items():
                if prompt_id not in self.config.extra_prompts:
                    self.config.extra_prompts[prompt_id] = extra_prompt
                    added_counts['extra'] += 1
                    logger.info(f"Added extra prompt: {extra_prompt.name}")
            
            # Update categories
            categories = set()
            for prompt in self.config.base_prompts.values():
                categories.add(prompt.category)
            for prompt in self.config.extra_prompts.values():
                categories.add(prompt.category)
            self.config.categories = sorted(list(categories))
            
            # Save the updated configuration
            if added_counts['base'] > 0 or added_counts['extra'] > 0:
                self.save_config()
                logger.info(f"Synced {added_counts['base']} base prompts and {added_counts['extra']} extra prompts from defaults")
            else:
                logger.info("No new prompts found in defaults")
                
        except Exception as e:
            logger.error(f"Failed to sync from defaults: {e}")
            
        return added_counts
