import logging
from collections import namedtuple
from pathlib import Path

import bs4.element
import requests
from bs4 import BeautifulSoup

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

Ingredient = namedtuple('Ingredient', ['amount', 'measure', 'type'])


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
    return ''.join(soup.find(id='article-heading_2-0').stripped_strings)


def extract_ingredients(soup: BeautifulSoup):
    dish_components = {}
    ingredient_tag = soup.find(id='mntl-structured-ingredients_1-0')
    current_component = None

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
                ingredient = Ingredient._make(entry.p.stripped_strings)
                dish_components[current_component].add(ingredient)

    return dish_components


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
    url = 'https://www.allrecipes.com/recipe/270770/garlic-noodles/'
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    title = extract_title(soup)
    logging.info(f'Extracted {title} for title from {url}')
    ingredients = extract_ingredients(soup)
    logging.info(f'Extracted {ingredients} for ingredients from {url}')
    steps = extract_steps(soup)
    logging.info(f'Extracted {steps} for steps from {url}')
    nutrition = extract_nutrition(soup)
    logging.info(f'Extracted {nutrition} for nutrition from {url}')
    bookmarks_file = Path('bookmarks.html')
    url_list_from_firefox_extracted_html(bookmarks_file)
