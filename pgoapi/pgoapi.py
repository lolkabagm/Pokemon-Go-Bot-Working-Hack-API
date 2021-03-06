# coding=latin-1
# Credits to Tejado and the devs over at the subreddit /r/PokemonGoDev -TomTheBotter

from __future__ import absolute_import

import logging
import re
from itertools import chain, imap

import requests
from .utilities import f2i, h2f, countmatching
from pgoapi.rpc_api import RpcApi
from pgoapi.auth_ptc import AuthPtc
from pgoapi.auth_google import AuthGoogle
from pgoapi.exceptions import AuthException, NotLoggedInException, ServerBusyOrOfflineException
from . import protos
from pgoapi.protos.POGOProtos.Networking.Requests_pb2 import RequestType
from pgoapi.protos.POGOProtos import Inventory_pb2 as Inventory
from sets import Set

import pickle
import random
import json
from pgoapi.location import *
import pgoapi.protos.POGOProtos.Enums_pb2 as RpcEnum
from pgoapi.poke_utils import *
from time import sleep
from collections import defaultdict
import os.path
from termcolor import colored

logger = logging.getLogger(__name__)
BAD_ITEM_IDS = [1,2,3,101,102,103,201,701,702,703] #Potion, Super Potion, RazzBerry, BlukBerry, Revive

# Minimum amount of the bad items that you should have ... Modify based on your needs ... like if you need to battle a gym?
MIN_BAD_ITEM_COUNTS = {Inventory.ITEM_POKE_BALL: 10,
                       Inventory.ITEM_GREAT_BALL: 50,
                       Inventory.ITEM_ULTRA_BALL: 100,
                       Inventory.ITEM_POTION: 0,
                       Inventory.ITEM_SUPER_POTION: 0,
                       Inventory.ITEM_HYPER_POTION: 50,
                       Inventory.ITEM_RAZZ_BERRY: 10,
                       Inventory.ITEM_BLUK_BERRY: 10,
                       Inventory.ITEM_NANAB_BERRY: 10,
                       Inventory.ITEM_REVIVE: 10}
MIN_SIMILAR_POKEMON = 2
IGNORE_POKEMON = Set([
    # 0, # MISSINGNO
    # 1, # BULBASAUR
    # 2, # IVYSAUR
    # 3, # VENUSAUR
    # 4, # CHARMANDER
    # 5, # CHARMELEON
    # 6, # CHARIZARD
    # 7, # SQUIRTLE
    # 8, # WARTORTLE
    # 9, # BLASTOISE
    10, # CATERPIE
    11, # METAPOD
    12, # BUTTERFREE
    13, # WEEDLE
    14, # KAKUNA
    # 15, # BEEDRILL
    # 16, # PIDGEY
    17, # PIDGEOTTO
    18, # PIDGEOT
    19, # RATTATA
    20, # RATICATE
    21, # SPEAROW
    22, # FEAROW
    23, # EKANS
    24, # ARBOK
    # 25, # PIKACHU
    # 26, # RAICHU
    # 27, # SANDSHREW
    # 28, # SANDLASH
    # 29, # NIDORAN_FEMALE
    # 30, # NIDORINA
    # 31, # NIDOQUEEN
    # 32, # NIDORAN_MALE
    # 33, # NIDORINO
    # 34, # NIDOKING
    # 35, # CLEFARY
    # 36, # CLEFABLE
    # 37, # VULPIX
    # 38, # NINETALES
    # 39, # JIGGLYPUFF
    # 40, # WIGGLYTUFF
    41, # ZUBAT
    42, # GOLBAT
    # 43, # ODDISH
    # 44, # GLOOM
    # 45, # VILEPLUME
    46, # PARAS
    47, # PARASECT
    48, # VENONAT
    49, # VENOMOTH
    # 50, # DIGLETT
    # 51, # DUGTRIO
    52, # MEOWTH
    53, # PERSIAN
    54, # PSYDUCK
    55, # GOLDUCK
    56, # MANKEY
    # 57, # PRIMEAPE
    # 58, # GROWLITHE
    # 59, # ARCANINE
    60, # POLIWAG
    61, # POLIWHIRL
    # 62, # POLIWRATH
    # 63, # ABRA
    # 64, # KADABRA
    # 65, # ALAKHAZAM
    # 66, # MACHOP
    # 67, # MACHOKE
    # 68, # MACHAMP
    # 69, # BELLSPROUT
    # 70, # WEEPINBELL
    # 71, # VICTREEBELL
    # 72, # TENTACOOL
    # 73, # TENTACRUEL
    # 74, # GEODUGE
    # 75, # GRAVELER
    # 76, # GOLEM
    # 77, # PONYTA
    # 78, # RAPIDASH
    # 79, # SLOWPOKE
    # 80, # SLOWBRO
    # 81, # MAGNEMITE
    # 82, # MAGNETON
    # 83, # FARFETCHD
    84, # DODUO
    85, # DODRIO
    # 86, # SEEL
    # 87, # DEWGONG
    # 88, # GRIMER
    # 89, # MUK
    # 90, # SHELLDER
    # 91, # CLOYSTER
    # 92, # GASTLY
    # 93, # HAUNTER
    # 94, # GENGAR
    # 95, # ONIX
    # 96, # DROWZEE
    # 97, # HYPNO
    98, # KRABBY
    # 99, # KINGLER
    # 100, # VOLTORB
    # 101, # ELECTRODE
    # 102, # EXEGGCUTE
    # 103, # EXEGGUTOR
    # 104, # CUBONE
    # 105, # MAROWAK
    # 106, # HITMONLEE
    # 107, # HITMONCHAN
    # 108, # LICKITUNG
    # 109, # KOFFING
    # 110, # WEEZING
    # 111, # RHYHORN
    # 112, # RHYDON
    # 113, # CHANSEY
    # 114, # TANGELA
    # 115, # KANGASKHAN
    # 116, # HORSEA
    # 117, # SEADRA
    # 118, # GOLDEEN
    # 119, # SEAKING
    # 120, # STARYU
    # 121, # STARMIE
    # 122, # MR_MIME
    # 123, # SCYTHER
    # 124, # JYNX
    # 125, # ELECTABUZZ
    # 126, # MAGMAR
    # 127, # PINSIR
    # 128, # TAUROS
    # 129, # MAGIKARP
    # 130, # GYARADOS
    # 131, # LAPRAS
    # 132, # DITTO
    # 133, # EEVEE
    # 134, # VAPOREON
    # 135, # JOLTEON
    # 136, # FLAREON
    # 137, # PORYGON
    # 138, # OMANYTE
    # 139, # OMASTAR
    # 140, # KABUTO
    # 141, # KABUTOPS
    # 142, # AERODACTYL
    # 143, # SNORLAX
    # 144, # ARTICUNO
    # 145, # ZAPDOS
    # 146, # MOLTRES
    # 147, # DRATINI
    # 148, # DRAGONAIR
    # 149, # DRAGONITE
    # 150, # MEWTWO
    # 151, # MEW
])


class PGoApi:

    API_ENTRY = 'https://pgorelease.nianticlabs.com/plfe/rpc'

    def __init__(self, config, pokemon_data, start_pos, print_info):

        self.log = logging.getLogger(__name__)
        self._start_pos = start_pos
        self._walk_count = 1
        self._auth_provider = None
        self._api_endpoint = None
        self.config = config
        self.set_position(*start_pos)
        self.RELEASE_DUPLICATES = config.get("RELEASE_DUPLICATE", 0)
        self._req_method_list = []
        self._heartbeat_number = 8
        self.pokemon_data = pokemon_data
        self.do_catch_pokemon = config.get("CATCH_POKEMON", True)
        self.min_probability_throw = config.get("MIN_PROBABILITY_THROW", 0.5)
        self.print_info = print_info
        self.MIN_KEEP_CP = config.get("MIN_KEEP_CP", 1000)

    def call(self):
        if not self._req_method_list:
            return False

        if self._auth_provider is None or not self._auth_provider.is_login():
            self.log.info('Not logged in')
            return False

        player_position = self.get_position()

        request = RpcApi(self._auth_provider)

        if self._api_endpoint:
            api_endpoint = self._api_endpoint
        else:
            api_endpoint = self.API_ENTRY

        self.log.debug('Execution of RPC')
        response = None
        try:
            response = request.request(api_endpoint, self._req_method_list, player_position)
        except ServerBusyOrOfflineException as e:
            self.log.info(colored('Server seems to be busy or offline - try again!', 'red'))

        # cleanup after call execution
        self.log.debug('Cleanup of request!')
        self._req_method_list = []

        return response

    def list_curr_methods(self):
        for i in self._req_method_list:
            print("{} ({})".format(RequestType.Name(i),i))

    def set_logger(self, logger):
        self._ = logger or logging.getLogger(__name__)

    def get_position(self):
        return (self._position_lat, self._position_lng, self._position_alt)

    def set_position(self, lat, lng, alt):
        self.log.debug('Set Position - Lat: %s Long: %s Alt: %s', lat, lng, alt)
        self._posf = (lat, lng, alt)
        self._position_lat = f2i(lat)
        self._position_lng = f2i(lng)
        self._position_alt = f2i(alt)

    def __getattr__(self, func):
        def function(**kwargs):

            if not self._req_method_list:
                self.log.debug('Create new request...')

            name = func.upper()
            if kwargs:
                self._req_method_list.append( { RequestType.Value(name): kwargs } )
                self.log.debug("Adding '%s' to RPC request including arguments", name)
                self.log.debug("Arguments of '%s': \n\r%s", name, kwargs)
            else:
                self._req_method_list.append( RequestType.Value(name) )
                self.log.debug("Adding '%s' to RPC request", name)

            return self

        if func.upper() in RequestType.keys():
            return function
        else:
            raise AttributeError

    def heartbeat(self):
        self.get_player()
        if self._heartbeat_number % 10 == 0:
            self.check_awarded_badges()
            self.get_inventory()

        res = self.call()

        if res.get("direction",-1) == 102:
            self.log.error("There were a problem responses for api call: %s. Restarting!!!", res)
            raise AuthException("Token probably expired?")

        self.log.debug('Heartbeat dictionary: \n\r{}'.format(json.dumps(res, indent=2)))

        if 'GET_PLAYER' in res['responses']:
            player_data = res['responses'].get('GET_PLAYER', {}).get('player_data', {})
            currencies = player_data.get('currencies', [])
            currency_data = ",".join(map(lambda x: "{0}: {1}".format(x.get('name', 'NA'), x.get('amount', 'NA')), currencies))
#            self.log.info("Username: %s, Currencies: %s", player_data.get('username', 'NA'), currency_data)

        if 'GET_INVENTORY' in res['responses']:
            with open("accounts/%s.json" % self.config['username'], "w") as f:
                res['responses']['lat'] = self._posf[0]
                res['responses']['lng'] = self._posf[1]
                res['responses']['alt'] = self._posf[2]
                f.write(json.dumps(res['responses'], indent=2))

            if self.print_info:
                self.log.info(get_inventory_data(res, self.pokemon_data))
                self.print_info = False

            self.log.debug(self.cleanup_inventory(res['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']))

        self._heartbeat_number += 1
        return res

    def walk_to(self,loc):
        self._walk_count += 1
        steps = get_route(self._posf, loc, self.config.get("USE_GOOGLE", False), self.config.get("GMAPS_API_KEY", ""))
        for step in steps:
            for i, next_point in enumerate(get_increments(self._posf, step, self.config.get("STEP_SIZE", 200))):
                self.set_position(*next_point)
                self.heartbeat()
#                self.log.info("Sleeping before next heartbeat")
                sleep(2) # If you want to make it faster, delete this line... would not recommend though
                while self.catch_near_pokemon():
                    sleep(1) # If you want to make it faster, delete this line... would not recommend though



    def spin_near_fort(self):
        map_cells = self.nearby_map_objects()['responses']['GET_MAP_OBJECTS']['map_cells']
        forts = PGoApi.flatmap(lambda c: c.get('forts', []), map_cells)
        if self._start_pos and self._walk_count % self.config.get("RETURN_START_INTERVAL") == 0:
            sleep_time = self.config.get("RETURN_START_INTERVAL") / self.config.get("STEP_SIZE", 200) * 100
            self.log.info(colored("Returning home and sleeping for %d seconds", "cyan"), sleep_time)
            sleep(sleep_time)
            destinations = filtered_forts(self._start_pos, forts)
        else:
            destinations = filtered_forts(self._posf,forts)

        if destinations:
            destinationNum = random.randint(0, min(5, len(destinations) - 1))
            fort = destinations[destinationNum]
            self.log.info("Walking to Pokestop at %s,%s", fort['latitude'], fort['longitude'])
            self.walk_to((fort['latitude'], fort['longitude']))
            position = self._posf # FIXME ?
            res = self.fort_search(fort_id = fort['id'], fort_latitude=fort['latitude'],fort_longitude=fort['longitude'],player_latitude=position[0],player_longitude=position[1]).call()['responses']['FORT_SEARCH']
            # self.log.info("Fort spinned: %s", res)
            if 'lure_info' in fort:
                encounter_id = fort['lure_info']['encounter_id']
                fort_id = fort['lure_info']['fort_id']
                position = self._posf
                resp = self.disk_encounter(encounter_id=encounter_id, fort_id=fort_id, player_latitude=position[0], player_longitude=position[1]).call()['responses']['DISK_ENCOUNTER']
                self.disk_encounter_pokemon(fort['lure_info'])
            return True
        else:
            self.log.error("No Pokestop to walk to!")
            return False

    def catch_near_pokemon(self):
        map_cells = self.nearby_map_objects()['responses']['GET_MAP_OBJECTS']['map_cells']
        pokemons = PGoApi.flatmap(lambda c: c.get('catchable_pokemons', []), map_cells)
        pokemons = [pokemon for pokemon in pokemons if pokemon['pokemon_id'] not in IGNORE_POKEMON]

        # catch first pokemon:
        origin = (self._posf[0], self._posf[1])
        pokemon_distances = [(pokemon, distance_in_meters(origin,(pokemon['latitude'], pokemon['longitude']))) for pokemon in pokemons]
        self.log.debug("Nearby pokemon: : %s", pokemon_distances)
        for pokemon_distance in pokemon_distances:
            target = pokemon_distance
            return self.encounter_pokemon(target[0])
        return False

    def nearby_map_objects(self):
        position = self.get_position()
        neighbors = getNeighbors(self._posf)
        data = self.get_map_objects(latitude=position[0], longitude=position[1], since_timestamp_ms=[0]*len(neighbors), cell_id=neighbors).call()
        return data

    def count_pokeballs(self):
        pokeballs = [0] * 4
        inventory_items = self.get_inventory().call()['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']
        for inventory_item in inventory_items:
            if 'inventory_item_data' in inventory_item:
                item = inventory_item['inventory_item_data']
                if 'item' in item:
                    item_id = item['item']['item_id']
                    if item_id < 5:
                        pokeballs[item_id-1] += item['item'].get('count') or 1

        return pokeballs

    def attempt_catch(self,encounter_id, spawn_point_guid, encounter):
        inventory_items = self.get_inventory().call()['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']
        pokeballs = self.count_pokeballs()
        probabilities = encounter['capture_probability']['capture_probability']
        # Throw up to 5 pokeballs at any given pokemon, then give up (our % is pretty damn high)
        for i in range(1,5):
            sleep(2)
            ball_type = 1;
            while (
                (pokeballs[ball_type - 1] == 0) or
                ((ball_type <= 4) and pokeballs[ball_type] and (probabilities[ball_type - 1] < self.min_probability_throw))
            ):
                ball_type += 1

            if pokeballs[ball_type - 1] == 0:
                self.log.info(colored("No pokeballs to throw, abandoning catch attempt!", "red"))
                return {'status': 2}

            pokeballs[ball_type - 1] -= 1
            self.log.info('Throwing %s', ['PokeBall', 'GreatBall', 'UltraBall', 'MasterBall'][ball_type - 1])
            r = self.catch_pokemon(
                normalized_reticle_size= 1.950,
                pokeball = ball_type,
                spin_modifier= 0.850,
                hit_pokemon=True,
                normalized_hit_position=1,
                encounter_id=encounter_id,
                spawn_point_guid=spawn_point_guid,
            ).call()['responses']

            if 'CATCH_POKEMON' in r:
                r = r['CATCH_POKEMON']
            else:
                self.log.info(colored("Error catching pokemon: %s", "red"), r)
                sleep(3)
                continue

            if "status" in r:
                return r

        # failed to catch
        return {'status': 3}

    def cleanup_inventory(self, inventory_items=None):
        if not inventory_items:
            inventory_items = self.get_inventory().call()['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']
        caught_pokemon = defaultdict(list)
        for inventory_item in inventory_items:
            if "pokemon_data" in inventory_item['inventory_item_data']:
                # is a pokemon:
                pokemon = inventory_item['inventory_item_data']['pokemon_data']
                if 'cp' in pokemon and "favorite" not in pokemon:
                    caught_pokemon[pokemon["pokemon_id"]].append(pokemon)
            elif "item" in inventory_item['inventory_item_data']:
                item = inventory_item['inventory_item_data']['item']
                if item['item_id'] in MIN_BAD_ITEM_COUNTS and "count" in item and item['count'] > MIN_BAD_ITEM_COUNTS[item['item_id']]:
                    recycle_count = item['count'] - MIN_BAD_ITEM_COUNTS[item['item_id']]
                    self.log.info("Recycling Item_ID {0}, item count {1}".format(item['item_id'], recycle_count))
                    self.recycle_inventory_item(item_id=item['item_id'], count=recycle_count)

        # evolve the strongest pokemon if possible
        for pokemons in caught_pokemon.values():
            if len(pokemons) > MIN_SIMILAR_POKEMON:
                pokemons = sorted(
                    pokemons,
                    lambda x,y: cmp(pokemonIVPercentage(x), pokemonIVPercentage(y)) or cmp(x['cp'], y['cp']),
                    reverse=True,
                )
                for pokemon in pokemons[:len(pokemons) - MIN_SIMILAR_POKEMON]:
                    poke_info = self.pokemon_data[str(pokemon['pokemon_id'])]
                    for inventory_item in inventory_items:
                        if ("pokemon_family" in inventory_item['inventory_item_data'] and
                          "evolves_to" in poke_info and
                          inventory_item['inventory_item_data']['pokemon_family']['family_id'] == poke_info['candy_id'] and
                          inventory_item['inventory_item_data']['pokemon_family']['candy'] > ((poke_info.get('max_evolve_candies') or poke_info.get('candies') or 0) + self.config.get("KEEP_CANDIES", 0))
                        ):
                          self.log.info(colored("Evolving pokemon:", "cyan") + " %s", self.pokemon_data[str(pokemon['pokemon_id'])]['name'])
                          self.evolve_pokemon(pokemon_id = pokemon['id'])
                          caught_pokemon[pokemon["pokemon_id"]].remove(pokemon)

        # sort and release all weaker pokemon
        if self.RELEASE_DUPLICATES:
            for pokemons in caught_pokemon.values():
                if len(pokemons) > MIN_SIMILAR_POKEMON:
                    pokemons = sorted(
                        pokemons,
                        lambda x,y: cmp(pokemonIVPercentage(x), pokemonIVPercentage(y)) or cmp(x['cp'], y['cp']),
                        reverse=True,
                    )
                    for pokemon in pokemons[MIN_SIMILAR_POKEMON:]:
                        if pokemon['cp'] < self.MIN_KEEP_CP:
                            self.log.debug("Releasing pokemon: %s", pokemon)
                            self.log.info(colored("Releasing pokemon:", "cyan") + " %s CP: %s, IV: %s", self.pokemon_data[str(pokemon['pokemon_id'])]['name'], str(pokemon['cp']), pokemonIVPercentage(pokemon))
                            self.release_pokemon(pokemon_id = pokemon["id"])

        return self.call()

    def disk_encounter_pokemon(self, lureinfo):
        if lureinfo['active_pokemon_id'] in IGNORE_POKEMON:
            return False
        try:
             encounter_id = lureinfo['encounter_id']
             fort_id = lureinfo['fort_id']
             position = self._posf
             resp = self.disk_encounter(encounter_id=encounter_id, fort_id=fort_id, player_latitude=position[0], player_longitude=position[1]).call()['responses']['DISK_ENCOUNTER']
             if resp['result'] == 1:
                 capture_status = -1
                 while capture_status != 0 and capture_status != 3:
                     catch_attempt = self.attempt_catch(encounter_id, fort_id, resp)
                     capture_status = catch_attempt['status']
                     if capture_status == 1:
                         pokemon = resp['pokemon_data']
                         self.log.debug("Caught Pokemon: : %s", catch_attempt)
                         self.log.info(resp)
                         self.log.info(colored("Caught pokemon:", "green") + " %s CP: %s, IV: %s", self.pokemon_data[str(pokemon['pokemon_id'])]['name'], str(pokemon['cp']), pokemonIVPercentage(pokemon))
                         sleep(2) # If you want to make it faster, delete this line... would not recommend though
                         return catch_attempt
                     elif capture_status != 2:
                         self.log.debug("Failed Catch: : %s", catch_attempt)
                         self.log.info(colored("Failed to catch Pokemon:", "red") + " %s", self.pokemon_data[str(resp['pokemon_data']['pokemon_id'])]['name'])
                         return False
                     sleep(2) # If you want to make it faster, delete this line... would not recommend though
        except Exception as e:
            self.log.error("Error in disk encounter %s", e)
            return False


    def encounter_pokemon(self,pokemon):
        encounter_id = pokemon['encounter_id']
        spawn_point_id = pokemon['spawn_point_id']
        position = self._posf
        encounter = self.encounter(encounter_id=encounter_id,spawn_point_id=spawn_point_id,player_latitude=position[0],player_longitude=position[1]).call()['responses']['ENCOUNTER']
        pokemon = encounter['wild_pokemon']['pokemon_data']
        if encounter['status'] == 1:
            capture_status = -1
            while capture_status != 0 and capture_status != 3:
                catch_attempt = self.attempt_catch(encounter_id, spawn_point_id, encounter)

                capture_status = catch_attempt['status']
                if capture_status == 1:
                    self.log.debug("Caught Pokemon: : %s", catch_attempt)
                    self.log.info(colored("Caught pokemon:", "green") + " %s CP: %s, IV: %s", self.pokemon_data[str(pokemon['pokemon_id'])]['name'], str(pokemon['cp']), pokemonIVPercentage(pokemon))
                    sleep(2) # If you want to make it faster, delete this line... would not recommend though
                    return catch_attempt
                elif capture_status != 2:
                    self.log.debug("Failed Catch: : %s", catch_attempt)
                    self.log.info(colored("Failed to Catch Pokemon:", "red") + " %s", self.pokemon_data[str(pokemon['pokemon_id'])]['name'])
                return False
                sleep(2) # If you want to make it faster, delete this line... would not recommend though
        return False

    def login(self, provider, username, password, cached=False):
        if not isinstance(username, basestring) or not isinstance(password, basestring):
            raise AuthException("Username/password not correctly specified")

        if provider == 'ptc':
            self._auth_provider = AuthPtc()
        elif provider == 'google':
            self._auth_provider = AuthGoogle()
        else:
            raise AuthException("Invalid authentication provider - only ptc/google available.")

        self.log.debug('Auth provider: %s', provider)

        if not self._auth_provider.login(username, password):
            self.log.info('Login process failed')
            return False

        self.log.info('Starting RPC login sequence (app simulation)')
        self.get_player()
        self.get_hatched_eggs()
        self.get_inventory()
        self.check_awarded_badges()
        self.download_settings(hash="05daf51635c82611d1aac95c0b051d3ec088a930")

        response = self.call()

        if not response:
            self.log.info('Login failed!')

        if os.path.isfile("auth_cache") and cached:
            response = pickle.load(open("auth_cache"))

        fname = "auth_cache_%s" % username

        if os.path.isfile(fname) and cached:
            response = pickle.load(open(fname))
        else:
            response = self.heartbeat()
            f = open(fname, "w")
            pickle.dump(response, f)

        if not response:
            self.log.info('Login failed!')
            return False

        if 'api_url' in response:
            self._api_endpoint = ('https://{}/rpc'.format(response['api_url']))
            self.log.debug('Setting API endpoint to: %s', self._api_endpoint)
        else:
            self.log.error('Login failed - unexpected server response!')
            return False

        if 'auth_ticket' in response:
            self._auth_provider.set_ticket(response['auth_ticket'].values())

        if cached and os.path.isfile("accounts/%s.json" % username):
            with open("accounts/%s.json" % username, 'r') as file_contents:
                jsonstr = file_contents.read()
            account_json = json.loads(jsonstr)
            self.log.info('restoring location to %f, %f', account_json['lat'], account_json['lng'])
            self.set_position(account_json['lat'], account_json['lng'], account_json['alt'])

        self.log.info('Finished RPC login sequence (app simulation)')
        self.log.info('Login process completed')

        return True

    def main_loop(self):
        self.heartbeat()
        while True:
            self.heartbeat()
            sleep(1) # If you want to make it faster, delete this line... would not recommend though
            self.spin_near_fort()
            while self.catch_near_pokemon():
                sleep(4) # If you want to make it faster, delete this line... would not recommend though
                pass

    @staticmethod
    def flatmap(f, items):
        return chain.from_iterable(imap(f, items))
