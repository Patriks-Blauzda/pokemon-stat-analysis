import requests
import pandas
import bs4

pokemon_list = []

base_url = 'https://bulbapedia.bulbagarden.net/'
pokedex_url = 'wiki/List_of_Pok%C3%A9mon_by_National_Pok%C3%A9dex_number'


def get_soup(url):
    response = requests.get(base_url + url)
    return bs4.BeautifulSoup(response.text, 'html.parser')


pokedex_soup = get_soup(pokedex_url)
generations = pokedex_soup.find_all('table', {'class': 'roundy'})

print("Getting Pokemon list...")
for generation in range(len(generations)):
    data = generations[generation].find_all('a')
    for pkmn in data:
        if '(Pokémon)' in pkmn.get('title'):
            pokemon_list.append({'name': pkmn.text, 'gen': generation + 1})


# Gathers data from individual Pokemon wiki pages
def scrape_pkmn(name: str, gen: int, soup: bs4.BeautifulSoup):
    # Gets infobox from the Pokemon's wiki page containing index, types and abilities
    infobox = soup.find('table', {'class': 'roundy infobox'})

    # Pokedex entry number
    ndex = int(
        infobox.find('a', {'title': 'List of Pokémon by National Pokédex number'}).span.text[1:]
    )

    # Gets only the third and fourth tables from the infobox containing types, abilities and hidden abilities
    infobox_tables = infobox.find_all('table', {'class': 'roundy'}, limit=4)[2:]

    # types
    type_table = infobox_tables[0].find('table').find_all('td', style=lambda x: x and 'display: none' not in x)
    types = [ptype.a.span.text for ptype in type_table]

    if len(types) < 2:
        types.append(None)

    # abilities
    abilities_row = infobox_tables[1].tr.find_all('td', style=None)

    # accounts for Pokemon pages that change styling because of missing hidden ability
    if len(abilities_row) < 1:
        abilities_row = [infobox_tables[1].tr.find('td')]

    abilities = [ability.text for ability in abilities_row[0].find_all('span', limit=2)]
    if len(abilities) < 2:
        abilities.append(None)

    # hidden ability
    hidden = None
    if len(abilities_row) > 1:
        hidden = abilities_row[1].find('span').text
    elif len(infobox_tables[1].find_all('tr')) > 1:
        # accounts for unique formatting for Pokemon missing a hidden ability
        hidden_container = infobox_tables[1].find_all('tr')[1].find('td', style=None)
        if hidden_container:
            hidden = hidden_container.find('span').text

    # hp, atk, def, spatk, spdef, spd, total
    stats = []
    stat_table = soup.find('table', style=lambda x: x and 'white-space: nowrap' in x)
    for stat in stat_table.find_all('tr', limit=9)[2:]:
        stats.append(int(stat.div.next_sibling.text))

    output = {
        'ndex': ndex, 'name': name, 'type1': types[0], 'type2': types[1], 'ability1': abilities[0],
        'ability2': abilities[1], 'hidden': hidden, 'gen': gen, 'hp': stats[0], 'atk': stats[1],
        'def': stats[2], 'spatk': stats[3], 'spdef': stats[4], 'spd': stats[5], 'total': stats[6]
    }

    return output


# Iterates through the list of all Pokemon names to scrape individual wiki pages
def create_dataset(input_data: list):
    session = requests.Session()
    output = []

    for i in range(len(input_data)):
        if input_data[i]['name'] == input_data[i-1]['name']:
            print("Duplicate skipped")
            continue

        pkmn_response = session.get(base_url + 'wiki/' + input_data[i]['name'].replace(' ', '_') + '_(Pokémon)')
        pkmn_soup = bs4.BeautifulSoup(pkmn_response.text, 'html.parser')

        print("Getting Pokemon #%s: " % str(i+1) + input_data[i]['name'])
        pokemon = scrape_pkmn(input_data[i]['name'], input_data[i]['gen'], pkmn_soup)
        output.append(pokemon)

    return output


# Damage multipliers for attacking types against defending types. If unspecified, defaults to 1
type_weaknesses = {
    'Normal': {'Rock': 0.5, 'Ghost': 0, 'Steel': 0.5},
    'Fire': {'Fire': 0.5, 'Water': 0.5, 'Grass': 2, 'Ice': 2, 'Bug': 2, 'Rock': 0.5, 'Dragon': 0.5, 'Steel': 2},
    'Water': {'Fire': 2, 'Water': 0.5, 'Grass': 0.5, 'Ground': 2, 'Rock': 2, 'Dragon': 0.5},
    'Electric': {'Water': 2, 'Electric': 0.5, 'Grass': 0.5, 'Ground': 0, 'Flying': 2, 'Dragon': 0.5},
    'Grass': {'Fire': 0.5, 'Water': 2, 'Grass': 0.5, 'Poison': 0.5, 'Ground': 2, 'Flying': 0.5, 'Bug': 0.5,
              'Rock': 2, 'Dragon': 0.5, 'Steel': 0.5},
    'Ice': {'Fire': 0.5, 'Water': 0.5, 'Grass': 2, 'Ice': 0.5, 'Ground': 2, 'Flying': 2, 'Dragon': 2, 'Steel': 0.5},
    'Fighting': {'Normal': 2, 'Ice': 2, 'Poison': 0.5, 'Flying': 0.5, 'Psychic': 0.5, 'Bug': 0.5, 'Rock': 2,
                 'Ghost': 0, 'Dark': 2, 'Steel': 2, 'Fairy': 0.5},
    'Poison': {'Grass': 2, 'Poison': 0.5, 'Ground': 0.5, 'Rock': 0.5, 'Ghost': 0.5, 'Steel': 0, 'Fairy': 2},
    'Ground': {'Fire': 2, 'Electric': 2, 'Grass': 0.5, 'Poison': 2, 'Flying': 0, 'Bug': 0.5, 'Rock': 2, 'Steel': 2},
    'Flying': {'Electric': 0.5, 'Grass': 2, 'Fighter': 2, 'Bug': 2, 'Rock': 0.5, 'Steel': 0.5},
    'Psychic': {'Fighting': 2, 'Poison': 2, 'Psychic': 0.5, 'Dark': 0, 'Steel': 0.5},
    'Bug': {'Fire': 0.5, 'Grass': 2, 'Fighter': 0.5, 'Poison': 0.5, 'Flying': 0.5, 'Psychic': 2, 'Ghost': 0.5,
            'Dark': 2, 'Steel': 0.5, 'Fairy': 0.5},
    'Rock': {'Fire': 2, 'Ice': 2, 'Fighter': 0.5, 'Ground': 0.5, 'Flying': 2, 'Bug': 2, 'Steel': 0.5},
    'Ghost': {'Normal': 0, 'Psychic': 2, 'Ghost': 2, 'Dark': 0.5},
    'Dragon': {'Dragon': 2, 'Steel': 0.5, 'Fairy': 0},
    'Dark': {'Fighter': 0.5, 'Psychic': 2, 'Ghost': 2, 'Dark': 0.5, 'Fairy': 0.5},
    'Steel': {'Fire': 0.5, 'Water': 0.5, 'Electric': 0.5, 'Ice': 2, 'Rock': 2, 'Steel': 0.5, 'Fairy': 2},
    'Fairy': {'Fire': 0.5, 'Fighter': 2, 'Poison': 0.5, 'Dragon': 2, 'Dark': 2, 'Steel': 0.5}
}


# Creates a cartesian product to compare each Pokemon's stats and score their performance
def get_best_pkmn_stats(pokedex: pandas.DataFrame):
    attackers = pokedex[['ndex', 'name', 'atk', 'spatk']].copy()
    defenders = pokedex[['name', 'def', 'spdef']].copy()

    scoring = attackers.merge(defenders, 'cross')
    scoring = scoring[scoring['name_x'] != scoring['name_y']]

    scoring['points'] = ((scoring['atk'] - scoring['def']) * 0.8) + ((scoring['spatk'] - scoring['spdef']) * 0.2)

    output = scoring.groupby(['ndex', 'name_x'], as_index=False)['points'].mean().sort_values('points', ascending=False)
    output = output.rename({'name_x': 'name'}, axis=1)
    output = output.reset_index(drop=True)
    return output


# Same as above function but for Pokemon types
def get_best_pkmn_type(pokedex: pandas.DataFrame):
    attackers = pokedex[['ndex', 'name', 'type1', 'type2']].copy()
    defenders = pokedex[['name', 'type1', 'type2']].copy()

    scoring = attackers.merge(defenders, 'cross')

    # Get a Pokemon's total type advantage against other Pokemon
    def get_mult(row):
        attacker_types = [row[2], row[3]]
        defender_types = [row[5], row[6]]

        mult = 0
        for def_type in defender_types:
            for atk_type in attacker_types:
                if type(atk_type) is str:
                    mult += type_weaknesses.get(atk_type).get(def_type, 1)

        return mult

    scoring['points'] = scoring.apply(get_mult, axis=1, raw=True)

    output = scoring.groupby(['ndex', 'name_x'], as_index=False)['points'].mean().sort_values('points', ascending=False)
    output = output.rename({'name_x': 'name'}, axis=1)
    output = output.reset_index(drop=True)
    return output


print("Scraping Pokemon data...")
pkmn_dataframe = create_dataset(pokemon_list)
pkmn_dataframe = pandas.DataFrame(pkmn_dataframe)

print("Ranking Pokemon by stats...")
pkmn_stat_ranking = get_best_pkmn_stats(pkmn_dataframe.copy())

print("Ranking Pokemon by type advantage...")
pkmn_type_ranking = get_best_pkmn_type(pkmn_dataframe.copy())

print("Creating/updating .csv files")
pkmn_dataframe.to_csv("pokemon_list.csv")
pkmn_stat_ranking.to_csv("pkmn_stat_scores.csv")
pkmn_type_ranking.to_csv("pkmn_type_scores.csv")

print('Finished executing, files generated')
