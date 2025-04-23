# src/search/services/prompt_manager.py

import yaml
from pathlib import Path

class PromptManager:
    
    def __init__(self, template_file="andrew_prompts.yaml"):
        self._template_file = template_file
        self.templates = self._load_prompt_templates(template_file)
    
    def _load_prompt_templates(self, file_path):
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Prompt template file not found: {file_path}")
        
        try:
            with open(path, "r") as f:
                templates = yaml.safe_load(f)
            return templates
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in prompt template file: {e}")
    
    def get_prompt(self, prompt_name, **kwargs):
        if prompt_name not in self.templates:
            raise KeyError(f"Prompt template not found: {prompt_name}")
        
        try:
            return self.templates[prompt_name].format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required format variable in template {prompt_name}: {e}")
    
    def reload_templates(self):
        self.templates = self._load_prompt_templates(self._template_file)
