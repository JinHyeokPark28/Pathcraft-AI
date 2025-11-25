"""
Template-based Q&A Generator
Generates high-quality Q&A pairs from POE knowledge templates
"""

import json
import logging
from typing import List, Dict
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QATemplateGenerator:
    """Generate structured Q&A from knowledge templates"""

    def __init__(self):
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict:
        """Load Q&A templates"""
        return {
            'build_basics': [
                {
                    'q_template': 'What is a {build_archetype} build in Path of Exile?',
                    'a_template': 'A {build_archetype} build focuses on {description}. Key mechanics include {mechanics}. Common ascendancy choices are {ascendancies}. Budget requirement: {budget}.',
                    'params': {
                        'build_archetype': ['League Starter', 'Boss Killer', 'Fast Mapper', 'Tanky Juggernaut', 'Crit Assassin'],
                        'description': [
                            'high survivability and steady damage output',
                            'maximizing clear speed for efficient mapping',
                            'single target damage for endgame bosses',
                            'balancing offense and defense for all content'
                        ],
                        'mechanics': [
                            'layered defenses, life regeneration, and fortify',
                            'movement skills, projectile chains, and pack clearing',
                            'concentrated effect, boss mechanics, and burst damage'
                        ],
                        'ascendancies': [
                            'Juggernaut, Champion, Gladiator',
                            'Deadeye, Raider, Pathfinder',
                            'Assassin, Saboteur, Inquisitor'
                        ],
                        'budget': ['1-5 divines', '5-20 divines', '20+ divines']
                    }
                }
            ],
            'mechanics': [
                {
                    'q_template': 'How does {mechanic} work in POE?',
                    'a_template': '{mechanic} is {explanation}. To use it effectively, {usage}. Common mistakes: {mistakes}.',
                    'params': {
                        'mechanic': [
                            'Poison', 'Ignite', 'Freeze', 'Stun', 'Block', 'Evasion',
                            'Armour', 'Energy Shield', 'Leech', 'Regeneration'
                        ],
                        'explanation': [
                            'a damage over time effect that scales with chaos and physical damage',
                            'a defensive mechanic that prevents a percentage of incoming hits',
                            'a recovery mechanic that restores life/ES over time based on damage dealt'
                        ],
                        'usage': [
                            'stack relevant passive nodes and gear modifiers',
                            'use support gems that enhance the mechanic',
                            'combine with other synergistic mechanics'
                        ],
                        'mistakes': [
                            'not investing enough in scaling modifiers',
                            'mixing incompatible mechanics',
                            'ignoring defensive layers'
                        ]
                    }
                }
            ],
            'crafting': [
                {
                    'q_template': 'How do I craft {item_type} with {desired_mod}?',
                    'a_template': 'To craft {desired_mod} on {item_type}: {method}. Item level required: {ilvl}. Estimated cost: {cost}.',
                    'params': {
                        'item_type': ['weapon', 'body armour', 'helmet', 'gloves', 'boots', 'jewellery'],
                        'desired_mod': [
                            '+1 to level of socketed gems',
                            'increased spell/attack critical strike chance',
                            'adds # to # physical/elemental damage',
                            '% increased life/ES'
                        ],
                        'method': [
                            'Use Essence of X on the item until you hit desired mods',
                            'Alt-spam until you hit the prefix/suffix, then regal and craft',
                            'Use Harvest "Reforge with X modifiers more common"',
                            'Fossil crafting with specific combinations'
                        ],
                        'ilvl': ['50+', '75+', '83+', '86+'],
                        'cost': ['10-50 chaos', '1-5 divines', '5-20 divines', '20+ divines']
                    }
                }
            ],
            'atlas': [
                {
                    'q_template': 'What is the best Atlas strategy for {goal}?',
                    'a_template': 'For {goal}, spec into {tree_nodes} on your Atlas tree. Run {map_types} maps with {scarabs}. Expected profit: {profit}/hour.',
                    'params': {
                        'goal': [
                            'currency farming',
                            'experience farming',
                            'boss farming',
                            'map sustain',
                            'divination card farming'
                        ],
                        'tree_nodes': [
                            'Essence, Harbinger, and Strongbox nodes',
                            'Expedition and Ritual nodes',
                            'Delirium and Beyond nodes',
                            'Boss nodes (Shaper, Elder, Conqueror)'
                        ],
                        'map_types': [
                            'high density linear maps like Strand or Beach',
                            'maps with good div card drops like Tower or Cemetery',
                            'boss-focused maps like Guardian maps'
                        ],
                        'scarabs': [
                            'Rusted/Polished Essence + Harbinger scarabs',
                            'Expedition + Ambush scarabs',
                            'Delirium + Breach scarabs'
                        ],
                        'profit': ['50-100c', '100-200c', '200-500c', '1-2 divines']
                    }
                }
            ],
            'leveling': [
                {
                    'q_template': 'What is the fastest way to level to {level}?',
                    'a_template': 'To reach level {level}: {strategy}. Key items: {items}. Time required: {time}.',
                    'params': {
                        'level': ['70', '80', '90', '95'],
                        'strategy': [
                            'Rush through the campaign using Quicksilver flasks and movement skills',
                            'Run white/blue T1-T5 maps quickly without looting',
                            'Juice T16 maps with scarabs and sextants for maximum XP',
                            'Use 5-way Legion or Pure Breachstones for efficient leveling'
                        ],
                        'items': [
                            'Tabula Rasa, Goldrim, Wanderlust, Quicksilver flasks',
                            'Cheap 5-link, resistance gear, movement speed boots',
                            'Proper 6-link, end-game rare items, defensive layers'
                        ],
                        'time': ['4-6 hours', '8-12 hours', '20-40 hours', '50-100 hours']
                    }
                }
            ]
        }

    def generate(self, count: int = 5000) -> List[Dict]:
        """Generate Q&A pairs from templates"""
        logger.info(f"Generating {count} Q&A pairs from templates")

        qa_pairs = []

        for category, templates in self.templates.items():
            # Calculate how many to generate per category
            per_category = count // len(self.templates)

            for template in templates:
                per_template = per_category // len(templates)

                for _ in range(per_template):
                    qa = self._generate_from_template(template, category)
                    qa_pairs.append(qa)

        logger.info(f"Generated {len(qa_pairs)} Q&A pairs")
        return qa_pairs

    def _generate_from_template(self, template: Dict, category: str) -> Dict:
        """Generate a single Q&A from template"""
        # Randomly select parameter values
        params = {}
        for param_name, param_values in template['params'].items():
            params[param_name] = random.choice(param_values)

        # Fill in templates
        question = template['q_template'].format(**params)
        answer = template['a_template'].format(**params)

        return {
            'question': question,
            'answer': answer,
            'source': 'template',
            'category': category,
            'timestamp': '2025-01-01T00:00:00'
        }


if __name__ == '__main__':
    generator = QATemplateGenerator()
    qa_pairs = generator.generate(count=100)

    print(f"\nGenerated {len(qa_pairs)} Q&A pairs")
    print("\nSample:")
    for qa in qa_pairs[:3]:
        print(f"\nQ: {qa['question']}")
        print(f"A: {qa['answer'][:150]}...")
