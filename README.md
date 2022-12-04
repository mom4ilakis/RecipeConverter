# RecipeConverter
A script to convert my bookmarked recipes in firefox to `.md` files that are supposed to be open by [Obsidian](https://obsidian.md/)  
Currently it only supports recipes from allrecipes.com   
How to setup:
* Create venv `python -m venv venv` python version >= 3.10
* Activate the virtual environment: `source /venv/bin/activate`(Linux) or `source /vevn/scripts/activate`(Windows)
* Edit `main.py` to change save path and path to `bookmarks.html` file (generated from Fifefox)
* Run `python main.py`
