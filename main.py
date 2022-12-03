import datetime
import itertools
import logging
import re
import time
from collections import defaultdict, namedtuple
from functools import reduce
from pathlib import Path

import bs4.element
import requests
from bs4 import BeautifulSoup

from markdown_editor import MarkdownEditor

LOG_FILENAME = 'log_%s.txt' % datetime.datetime.now().strftime('%m%d-%H%M%S')
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)  # ,filename=LOG_FILENAME)

Ingredient = namedtuple('Ingredient', ['amount', 'measure', 'type'], defaults=['', '', ''])


def is_pasta(tag):
    return 'spaghetti' in tag or 'bucatini' in tag  # extend with more pasta types when encountered


def url_list_from_firefox_extracted_html(path: Path, matcher=lambda a: 'allrecipes' in a.attrs['href']):
    with open(path, 'r', encoding='utf-8') as html_file:
        content = html_file.read()
        soup = BeautifulSoup(content, 'html.parser')

        href_tags = [a.extract() for a in soup('a')]
        extracted_links = [a.attrs['href'] for a in href_tags if matcher(a)]

        return set(extracted_links)


def get_children_no_navs(elements) -> [bs4.element.Tag]:
    return filter(lambda e: isinstance(e, bs4.element.Tag), elements.children)


def extract_title(soup: BeautifulSoup):
    title = ''.join(soup.find(id='article-heading_2-0').stripped_strings)

    return title.lower().replace("chef john's ", '').capitalize()


def extract_ingredients(soup: BeautifulSoup):
    dish_components = defaultdict(set)
    ingredient_tag = soup.find(id='mntl-structured-ingredients_1-0')
    current_component = ''

    for child in get_children_no_navs(ingredient_tag):
        if child.name == 'div':
            continue
        if child.name == 'p':
            component = child.string

            if component not in dish_components:
                dish_components[component] = set()

            current_component = component

            continue
        if child.name == 'ul':
            for entry in get_children_no_navs(child):
                raw = list(entry.p.stripped_strings)
                amount = raw[0]
                measure = raw[1] if len(raw) == 3 else ''
                type = raw[-1]
                ingredient = Ingredient(amount, measure, type)  # convert to metric?
                dish_components[current_component].add(ingredient)

    return dish_components


def simplify_tag(complex_tag: str):
    # TODO a better way to do this
    if 'butter' in complex_tag:
        return 'butter'
    if 'bacon' in complex_tag and 'cooking' not in complex_tag:
        return 'bacon'
    if 'cheese' in complex_tag:
        cheesy_regex = re.compile(r'(([a-z]|-)+)\s(?=cheese)', re.I)
        match = re.search(cheesy_regex, complex_tag)
        return f'cheese, {match.groups()[0]}'
    if is_pasta(complex_tag):
        return 'pasta'
    if 'garlic' in complex_tag:
        return 'garlic'
    if 'green onion' in complex_tag:
        return 'green-onion'
    if 'salt' in complex_tag and 'pepper' not in complex_tag:
        return 'salt'
    if 'eggs' in complex_tag or 'egg' in complex_tag:
        return 'eggs'
    if 'shrimp' in complex_tag:
        return 'shrimp'
    if 'chicken' in complex_tag:
        return 'chicken'
    if 'pork' in complex_tag:
        return 'pork'
    if 'beef' in complex_tag:
        return 'beef'
    if 'water' in complex_tag:
        return ''
    if 'black pepper' in complex_tag:
        return 'black-pepper'
    if 'nutmeg' in complex_tag:
        return 'nutmeg'
    if 'corn' in complex_tag:
        return 'corn'
    if 'ginger' in complex_tag:
        return 'ginger'

    noise = ['or to taste', 'finely', 'minced', 'divided', 'or more as needed', 'or as needed', 'or more to taste',
             'diced', 'coarsely', 'and', 'beaten', 'juiced', 'at room temperature', 'chopped', 'peeled', 'sliced',
             'thawed', 'zested', '(Optional)', 'boneless', 'cold', 'cooked', 'fresh', 'freshly', 'and deveined',
             'boiling hot', 'casing removed', 'coarsely chopped', 'cored and very thinly sliced', 'crumbled', 'crushed',
             'cubed', 'cut in half', 'cut into', 'cut into 2 inch pieces',
             'each cut into 8 thick streak fry size wedges', 'peeled and cut into', 'for garnish', 'halved crosswise',
             'heated', 'mashed', 'melted', 'or as desired', 'or more if needed',
             'or soaked in 1 tablespoon vinegar for 5 minutes',
             'orange parts of peel removed and sliced in thin strips', 'peeled and cut into', 'peeled and deveined',
             'peeled and sliced', 'pitted', 'plus more for greasing', 'seeded and chopped', 'shell on', 'skin removed',
             'soaked for at least 1 hour', 'torn in half', 'trimmed', 'for dusting']

    complex_tag = reduce(lambda tag, n: tag.replace(n, ''), noise, complex_tag)
    logging.info(f'After reduction: {complex_tag}')

    return complex_tag.replace(', ', '').strip().replace(' ', '-')


def extract_tags_from_ingredients(ingredients: dict) -> list:
    tags = set([i.type for i in itertools.chain(*ingredients.values())])
    # since the results from filter and map are generators, we won't do a double iteration
    return list(filter(lambda tag: tag, map(simplify_tag, tags)))


def extract_steps(soup: BeautifulSoup):
    steps = {}
    steps_tag = soup.find(id='recipe__steps-content_1-0').ol

    for index, step in enumerate(get_children_no_navs(steps_tag), start=1):
        steps[f'Step {index}'] = step.p.text.replace('\n', '')

    return steps


def extract_nutrition(soup: BeautifulSoup):
    nutrients = {}
    nutrition = soup.find(id='mntl-nutrition-facts-summary_1-0')
    table = nutrition.table

    for entry in table.tbody.find_all('tr'):
        [value, key] = entry.stripped_strings
        nutrients[key] = value

    return nutrients


if __name__ == '__main__':
    bookmarks_file = Path('bookmarks.html')
    url = 'https://www.allrecipes.com/recipe/270770/garlic-noodles/'
    urls = url_list_from_firefox_extracted_html(bookmarks_file)

    folder = r'D:\Notes\Recepies\Generated'

    for url in urls:
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')
        try:
            title = extract_title(soup)
            ingredients = extract_ingredients(soup)
            steps = extract_steps(soup)
            nutrition = extract_nutrition(soup)
            tags = extract_tags_from_ingredients(ingredients)

            md_editor = MarkdownEditor(title, 'recipe_template.md')

            md_editor.add_original_link(url)
            md_editor.add_ingredients(ingredients)
            md_editor.add_instructions(steps)
            md_editor.add_nutrition(nutrition)
            md_editor.add_tags(tags)
            md_editor.save(folder)

            logging.info(f'Extracted tags:\n{tags}\n from {url}')
            logging.info(f'Extracted ingredients:\n{ingredients}\n from {url}')
            logging.info(f'Extracted steps:\n{steps}\n from {url}')
            logging.info(f'Extracted nutrition:\n{nutrition}\n from {url}')
        except Exception as e:
            logging.error(f'{e} for {url}')
