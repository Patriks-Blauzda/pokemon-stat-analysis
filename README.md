# pokemon-stat-analysis
A web scraper that collects Pokemon information from https://bulbapedia.bulbagarden.net/
The script gathers every Pokemon's Pokedex number, name, types, abilities, hidden ability, generation and stats. Data is stored in the generated file "pokemon_list.csv". Tables with rankings for each Pokemon regarding overall stats or type advantages against every other pokemon are also created in the files "pkmn_stat_scores.csv" and "pkmn_type_scores.csv".

# Libraries used
- Beautiful Soup 4
- Pandas
- Requests
