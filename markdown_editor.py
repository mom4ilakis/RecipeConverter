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
    def __init__(self, title, path_to_template, use_template=True):
        self.markdown = ""
        self.title = title
        self.use_template = use_template

        with open(path_to_template) as template_file:
            self.template = template_file.read()

    def add_title(self, title: str):
        if self.use_template:
            self.template = self.template.replace('<!--title-->', title)
        else:
            self.markdown += f'# {title.capitalize()}\n'

    def add_tags(self, tags: list):
        if self.use_template:
            logging.warning(tags)
            text = ', '.join(tags)
            self.template = self.template.replace('<!--tags_list-->', text)
        else:
            self.markdown += f'''---\n\ttags: [{tags}]\n---\n'''

    def add_ingredients(self, ingredients: dict):
        text = ''

        for component, ingr_list in ingredients.items():
            text += f'#### {component}  \n'

            for amount, measurement, ingredient in ingr_list:
                text += f'* {amount} {measurement} {ingredient}\n'

        if self.use_template:
            self.template = self.template.replace('<!--ingredients_list-->', text)
        else:
            self.markdown += '## Ingredients\n'
            self.markdown += text
            self.insert_line()

    def add_instructions(self, instructions: dict):
        text = ''

        for step, instruction in instructions.items():
            text += f'**{step}**  \n{instruction}  \n'

        if self.use_template:
            self.template = self.template.replace('<!--instructions_list-->', text)
        else:
            self.markdown += text
            self.insert_line()

    def insert_line(self):
        self.markdown += '\n---\n'

    def add_nutrition(self, nutrition: dict):
        text = ''

        for nutrition_type, amount in nutrition.items():
            text += f'{nutrition_type}: {amount}  '

        if self.use_template:
            self.template = self.template.replace('<!--nutrition_list-->', text)
        else:
            self.markdown += '## Nutrition'
            self.markdown += text
            self.insert_line()

    def add_original_link(self, link: str):
        if self.use_template:
            self.template = self.template.replace('<!--original_recipe_link-->', link)
        else:
            self.markdown += link

    def save(self, path, is_safe=False):
        path = Path(path)
        full_path = path / (self.title + '.md')

        if full_path.exists() and is_safe:
            count = count_files(path, self.title)
            new_title = f'{self.title}_{count}'
            full_path = path / new_title
        else:
            os.makedirs(path, exist_ok=True)

        with open(full_path, 'w', encoding="utf-8") as md:
            if self.use_template:
                md.write(self.template)
            else:
                md.write(self.markdown)
