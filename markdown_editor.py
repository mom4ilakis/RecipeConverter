import logging
import os
from functools import reduce
from pathlib import Path


def count_files(path: Path, filename: str):
    if path.is_dir():
        count = 0
        for root, dirs, files in os.walk(path):
            count = reduce(lambda prev, f: prev + 1 if filename in f else prev, files, 0)
        return count or ''
    else:
        logging.warning(f'{path} is not a dir!')
        return 1 if filename in path else ''


class MarkdownEditor:
    def __init__(self, title):
        self.markdown = ""
        self.title = title

    def add_title(self, title: str):
        self.markdown += f'# {title.capitalize()}\n'

    def add_tags(self, tags):
        self.markdown += f'''---\n\ttags: [{tags}]\n---\n'''

    def add_ingredients(self, ingredients: dict):
        self.markdown += '## Ingredients\n'
        for component, ingr_list in ingredients:
            self.markdown += f'#### {component}'

            for amount, measurement, ingredient in ingr_list:
                self.markdown += f'* {amount}{measurement} {ingredient}\n'

        self.markdown += '---\n'

    def add_instructions(self, instructions: dict):
        self.markdown += instructions
        self.insert_line()

    def insert_line(self):
        self.markdown += '\n---\n'

    def add_nutrition(self, nutrition: dict):
        self.markdown += '## Nutrition'
        self.markdown += nutrition
        self.insert_line()

    def save(self, path):
        path = Path(path)
        full_path = path / self.title

        if full_path.exists():
            count = count_files(path, self.title)
            new_title = self.title + '_' + count
            full_path = path / new_title

        with open(full_path, 'w') as md:
            md.write(self.markdown)
