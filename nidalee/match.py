import pprint

from munch import DefaultMunch
from datetime import datetime, timedelta
from kayle.ddragon.factory import ddragon_factory
from kayle.ddragon.maps import maps
from pympler.asizeof import asizeof
import pickle


class Match:
    def __init__(self, matchSummary):
        self.version = ddragon_factory.versions()[0]
        self.patch = ""
        self.id = matchSummary['id']
        self.startTime = datetime.fromisoformat(matchSummary['startTime'].replace('T', ' ').replace('Z', ''))
        self.bestOf = matchSummary['bestOf']
        self.teams = [DefaultMunch.fromDict(team) for team in matchSummary['teams']]
        self.games = [Game(game, self) for game in matchSummary['games']]


class Game:
    def __init__(self, bayesGameSummary, match):
        # pprint.pp(match)
        try:
            self.id = bayesGameSummary['id']
        except KeyError:
            self.id = match['id']

        self.gameName = ""
        try:
            self.gameNumber = bayesGameSummary['gameNumber']
        except:
            self.gameNumber = 1

        try:
            if bayesGameSummary['winnerTeamId'] == match.teams[0].id:
                self.winnerTeam = match.teams[0]
            else:
                self.winnerTeam = match.teams[1]
        except KeyError:
            self.winnerTeam = None

        try:
            self.startTime = datetime.fromisoformat(bayesGameSummary['startTime'].replace('T', ' ').replace('Z', ''))
        except KeyError:
            self.startTime = datetime.fromisoformat(match['createdAt'].replace('T', ' ').replace('Z', ''))
        try:
            self.endTime = datetime.fromisoformat(bayesGameSummary['endTime'].replace('T', ' ').replace('Z', ''))
        except KeyError:
            self.endTime = None

        try:
            self.numberOfMessages = bayesGameSummary['numberOfMessages']
        except KeyError:
            self.numberOfMessages = len(bayesGameSummary["events"])

        self.pickOrder = []
        self.players = {}
        self.bans = []
        self._bans = {}
        self.draft_order = []
        self.positionHistory = {}
        self.eventHistory = {}
        self.statsHistory = {}
        self.events = []
        self.playerEvents = {}

        try:
            self.scrimTeams = None
            if len(match["teams"]) == 2:
                self.scrimTeams = match["teams"]
        except:
            pass

        try:
            data = bayesGameSummary["gameData"]["events"]
        except KeyError:
            data = bayesGameSummary["events"]
        try:
            match = DefaultMunch.fromDict({"version": ddragon_factory.versions()[0], "teams": match["teams"]})
        except:
            pass
        # print(match.version)
        # print(len(data))
        # pprint.pp(data[0])
        game_started = False
        for payload in data:
            try:
                p_data = payload["payload"]["payload"]
                e_data = p_data['payload']
                if 'gameVersion' in e_data:
                    match.version = '.'.join(e_data['gameVersion'].split('.')[:2]) + ".1"
                    match.patch = '.'.join(e_data['gameVersion'].split('.')[:2])
                    if match.version == "13.1.1" and match.version not in ddragon_factory.versions():
                        match.version = "12.23.1"
                        match.patch = "13.1"
                if 'name' in e_data:
                    self.gameName = e_data['name']

                match p_data["type"], p_data['action']:
                    case 'INFO', 'ANNOUNCE':
                        if p_data["subject"] == 'MATCH':
                            #pprint.pp(e_data)
                            for index, team in enumerate(e_data['teams']):
                                self._bans[team["urn"]] = []

                                for participant in team['participants']:
                                    p = Player(participant)
                                    self.players[participant['urn']] = p
                                    self.positionHistory[p.urn] = []
                                    self.eventHistory[p.urn] = []
                                    self.statsHistory[p.urn] = []
                                    self.playerEvents[p.urn] = []
                                    try:
                                        if len(match["teams"]) == 1 and match["teams"][0][
                                            "code"] in p.summonerName and self.scrimTeams is None:
                                            tmp = match["teams"][0]
                                            match["teams"].insert(
                                                (index + 1) % 2, {'id': 0, 'code': 'Unknown', 'name': 'Unknown'}
                                                )
                                            self.scrimTeams = match["teams"]


                                    except Exception as e:
                                        pass

                            self.team1urn = list(self._bans.keys())[0]
                            self.team2urn = list(self._bans.keys())[1]

                    case 'INFO', 'UPDATE':
                        if not game_started:
                            pass

                    case 'GAME_EVENT', 'BANNED_HERO':
                        if len(self.bans) < 10:
                            champion_banned = ddragon_factory.championFromId(
                                e_data['championId'], match.version
                            ).id
                            self._bans[e_data["teamUrn"]].append(champion_banned)
                        # pprint.pp(e_data)

                    case 'GAME_EVENT', 'SELECTED_HERO':
                        if len(self.draft_order) < 10:
                            champion_picked = ddragon_factory.championFromId(
                                e_data['championId'], match.version
                            ).id
                            self.draft_order.append(champion_picked)
                    case 'GAME_EVENT', 'END_PAUSE':
                        pass

                    case 'GAME_EVENT', 'START_PAUSE':
                        pass

                    case 'GAME_EVENT', 'EXPIRED_OBJECTIVE':
                        pass

                    case 'GAME_EVENT', 'ANNOUNCED_ANCIENT':
                        e = Event('ANNOUNCED_ANCIENT', e_data, self, match.version)
                        self.events.append(e)

                    case 'GAME_EVENT', 'END_MAP':
                        e = Event('END_MAP', e_data, self, match.version)
                        self.events.append(e)
                        if e.winningTeamUrn == self.team1urn:
                            self.winnerTeam = 0
                        else:
                            self.winnerTeam = 1

                    case 'GAME_EVENT', 'UPDATE_SCORE':
                        pass

                    case 'GAME_EVENT', 'START_MAP':
                        game_started = True
                        if len(self.bans) == 9:
                            self.bans.append("")

                    case 'GAME_EVENT', 'PURCHASED_ITEM':
                        e = Event('PURCHASED_ITEM', e_data, self, match.version)
                        self.playerEvents[e.player.urn].append(e)
                        self.events.append(e)

                    case 'GAME_EVENT', 'PICKED_UP_ITEM':
                        e = Event('PICKED_UP_ITEM', e_data, self, match.version)
                        self.playerEvents[e.player.urn].append(e)
                        self.events.append(e)

                    case 'GAME_EVENT', 'CONSUMED_ITEM':
                        e = Event('CONSUMED_ITEM', e_data, self, match.version)
                        self.playerEvents[e.player.urn].append(e)
                        self.events.append(e)

                    case 'GAME_EVENT', 'SOLD_ITEM':
                        e = Event('SOLD_ITEM', e_data, self, match.version)
                        self.playerEvents[e.player.urn].append(e)
                        self.events.append(e)

                    case 'GAME_EVENT', 'UNDO_ITEM':
                        e = Event('UNDO_ITEM', e_data, self, match.version)
                        self.playerEvents[e.player.urn].append(e)
                        self.events.append(e)

                    case 'GAME_EVENT', 'PLACED_WARD':
                        e = Event('PLACED_WARD', e_data, self, match.version)
                        if e.player is not None:
                            self.playerEvents[e.player.urn].append(e)
                        self.events.append(e)

                    case 'GAME_EVENT', 'KILLED_WARD':
                        e = Event('KILLED_WARD', e_data, self, match.version)
                        self.playerEvents[e.player.urn].append(e)
                        self.events.append(e)

                    case 'GAME_EVENT', 'KILLED_ANCIENT':
                        e = Event('KILLED_ANCIENT', e_data, self, match.version)
                        for p in e.implicatedParticipants:
                            self.playerEvents[p.urn].append(e)
                        self.events.append(e)

                    case 'GAME_EVENT', 'LEVEL_UP':
                        e = Event('LEVEL_UP', e_data, self, match.version)
                        self.playerEvents[e.player.urn].append(e)
                        self.events.append(e)

                    case 'GAME_EVENT', 'KILL':
                        e = Event('KILL', e_data, self, match.version)
                        for p in e.implicatedParticipants:
                            self.playerEvents[p.urn].append(e)
                        self.events.append(e)

                    case 'GAME_EVENT', 'DIED':
                        e = Event('DIED', e_data, self, match.version)
                        self.playerEvents[e.player.urn].append(e)
                        self.events.append(e)

                    case 'GAME_EVENT', 'SPECIAL_KILL':
                        e = Event('SPECIAL_KILL', e_data, self, match.version)
                        self.playerEvents[e.killer.urn].append(e)
                        self.events.append(e)

                    case 'GAME_EVENT', 'SPAWNED_ANCIENT':
                        e = Event('SPAWNED_ANCIENT', e_data, self, match.version)
                        self.events.append(e)

                    case 'GAME_EVENT', 'SPAWNED':
                        e = Event('SPAWNED', e_data, self, match.version)
                        self.playerEvents[e.player.urn].append(e)
                        self.events.append(e)

                    case 'GAME_EVENT', 'EXPIRED_ITEM':
                        e = Event('EXPIRED_ITEM', e_data, self, match.version)
                        if e.player is not None:
                            self.playerEvents[e.player.urn].append(e)
                        self.events.append(e)

                    case 'GAME_EVENT', 'TOOK_OBJECTIVE':
                        e = Event('TOOK_OBJECTIVE', e_data, self, match.version)
                        for p in e.implicatedParticipants:
                            self.playerEvents[p.urn].append(e)
                        self.events.append(e)

                    case 'GAME_EVENT', 'SKILL_LEVEL_UP':
                        e = Event('SKILL_LEVEL_UP', e_data, self, match.version)
                        for p in e.implicatedParticipants:
                            self.playerEvents[p.urn].append(e)
                        self.events.append(e)

                    case 'INFO', 'ROLLBACK':
                        e = Event('ROLLBACK', e_data, self, match.version)
                        self.events.append(e)

                    case 'SNAPSHOT', 'UPDATE':
                        if game_started:
                            for teamData in [e_data['teamOne'], e_data['teamTwo']]:
                                for statData in teamData['players']:
                                    p = PlayerSnapshotStatEvent(statData, match.version, e_data['gameTime'])
                                    self.statsHistory[statData['liveDataPlayerUrn']].append(p)
                            if e_data["winningTeam"] == 100:
                                self.winnerTeam = 0
                            elif e_data["winningTeam"] == 200:
                                self.winnerTeam = 1

                    case 'SNAPSHOT', 'UPDATE_POSITIONS':
                        for positionData in e_data['positions']:
                            p = Position(positionData, e_data['gameTime'])
                            self.positionHistory[p.playerUrn].append(p)

                    case _, _:
                        raise NotImplementedError(
                            "Event of type {} was not implemented".format(payload["payload"]["payload"]["type"])
                        )
            except Exception as e:
                pprint.pp(payload)
                raise e

        while len(self._bans[self.team1urn]) < 5:
            self._bans[self.team1urn].append("")
        while len(self._bans[self.team2urn]) < 5:
            self._bans[self.team2urn].append("")

        self.bans = [self._bans[self.team1urn][0], self._bans[self.team2urn][0], self._bans[self.team1urn][1],
                     self._bans[self.team2urn][1], self._bans[self.team1urn][2],
                     self._bans[self.team2urn][2], self._bans[self.team1urn][3], self._bans[self.team2urn][3],
                     self._bans[self.team1urn][4], self._bans[self.team2urn][4]]
        self.version = match.version
        self.patch = match.patch

        #print(self.scrimTeams[0]["code"])
        #print(self.players[list(self.players.keys())[6]].name)
        try:
            if self.scrimTeams[0]["code"] in self.players[list(self.players.keys())[6]].name and self.scrimTeams[0]["code"] != "Unknown":
                # print("Team names are inversed, thanks Bayes!")
                self.scrimTeams.reverse()
        except:
            pass


        if self.winnerTeam is None and len(self.statsHistory[self.players[list(self.players.keys())[0]].urn]) > 500:
            # print("Nb of updates : ", len(self.statsHistory[self.players[list(self.players.keys())[0]].urn]))
            playerUrns = list(self.players.keys())
            team1golds = 0
            team2golds = 0
            for playerUrn in playerUrns[:5]:
                team1golds += self.statsHistory[playerUrn][-1].totalGold
            for playerUrn in playerUrns[5:10]:
                team2golds += self.statsHistory[playerUrn][-1].totalGold
            if team1golds > team2golds:
                self.winnerTeam = 0
            else:
                self.winnerTeam = 1
        elif len(self.statsHistory[self.players[list(self.players.keys())[0]].urn]) < 500:
            # print("This game was remaked")
            self.winnerTeam = "Remake"


class Event:
    def __init__(self, type, data, game: Game, version):
        self.type = type
        match type:
            case 'PURCHASED_ITEM':
                self.gameTime = timedelta(milliseconds=data['gameTime'])
                self.item = ddragon_factory.itemFromId(data['item'], version)
                self.player = game.players[data['playerUrn']]
                self.implicatedParticipants = [self.player]
            case 'PICKED_UP_ITEM':
                self.gameTime = timedelta(milliseconds=data['gameTime'])
                self.item = ddragon_factory.itemFromId(data['item'], version)
                self.player = game.players[data['playerUrn']]
                self.implicatedParticipants = [self.player]
            case 'CONSUMED_ITEM':
                self.gameTime = timedelta(milliseconds=data['gameTime'])
                self.item = ddragon_factory.itemFromId(data['item'], version)
                self.player = game.players[data['playerUrn']]
                self.implicatedParticipants = [self.player]
            case 'UNDO_ITEM':
                self.gameTime = timedelta(milliseconds=data['gameTime'])
                self.item = ddragon_factory.itemFromId(data['item'], version)
                self.player = game.players[data['playerUrn']]
                self.implicatedParticipants = [self.player]
            case 'SOLD_ITEM':
                self.gameTime = timedelta(milliseconds=data['gameTime'])
                self.item = ddragon_factory.itemFromId(data['item'], version)
                self.player = game.players[data['playerUrn']]
                self.implicatedParticipants = [self.player]
            case 'PLACED_WARD':
                self.gameTime = timedelta(milliseconds=data['gameTime'])
                if data['placerUrn'] is not None:
                    self.player = game.players[data['placerUrn']]
                else:
                    self.player = None
                self.position = EventPosition(data['position'])
                self.wardType = data['wardType']
                self.implicatedParticipants = [self.player]
            case 'KILLED_ANCIENT':
                self.gameTime = timedelta(milliseconds=data['gameTime'])
                self.assistants = [game.players[p] for p in data['assistants']]
                try:
                    self.player = game.players[data['killerUrn']]
                    self.implicatedParticipants = [self.player] + self.assistants
                except:
                    self.player = None
                    self.implicatedParticipants = self.assistants
                self.position = EventPosition(data['position'])
                self.monsterType = data['monsterType']
                self.dragonType = data['dragonType']

            case 'LEVEL_UP':
                self.gameTime = timedelta(milliseconds=data['gameTime'])
                self.player = game.players[data['playerUrn']]
                self.newValue = data['newValue']
                self.implicatedParticipants = [self.player]

            case 'SKILL_LEVEL_UP':  # Not in competitive, only in scrims
                self.gameTime = timedelta(milliseconds=data['gameTime'])
                self.player = game.players[data['playerUrn']]
                self.slot = data['slot']
                self.level = data['level']
                self.implicatedParticipants = [self.player]

            case 'KILLED_WARD':
                self.gameTime = timedelta(milliseconds=data['gameTime'])
                try:
                    self.placedBy = game.players[data['placerUrn']]
                except:
                    self.placedBy = None
                self.position = EventPosition(data['position'])
                self.wardType = data['wardType']
                self.player = game.players[data['killerUrn']]
                self.implicatedParticipants = [self.player]
            case 'KILL':
                self.gameTime = timedelta(milliseconds=data['gameTime'])
                self.victim = game.players[data['victimUrn']]
                self.position = EventPosition(data['position'])
                self.assistants = [game.players[a] for a in data['assistants']]
                if data['killerUrn'] is not None:
                    self.killer = game.players[data['killerUrn']]
                    self.implicatedParticipants = [self.killer] + self.assistants
                else:
                    self.killer = None
                    self.implicatedParticipants = self.assistants

            case 'DIED':
                self.gameTime = timedelta(milliseconds=data['gameTime'])
                self.player = game.players[data['playerUrn']]
                self.position = EventPosition(data['position'])
                self.totalDeaths = data['totalDeaths']
                self.respawnTime = timedelta(milliseconds=data['respawnTime'])
                self.implicatedParticipants = [self.player]
            case 'SPAWNED':
                self.gameTime = timedelta(milliseconds=data['gameTime'])
                self.player = game.players[data['playerUrn']]
                self.position = EventPosition(data['position'])
                self.implicatedParticipants = [self.player]
            case 'SPECIAL_KILL':
                self.gameTime = timedelta(milliseconds=data['gameTime'])
                self.killer = game.players[data['killerUrn']]
                self.position = EventPosition(data['position'])
                self.killType = data['killType']
                self.killStreak = data['killStreak']
                self.implicatedParticipants = [self.killer]
            case 'SPAWNED_ANCIENT':
                self.gameTime = timedelta(milliseconds=data['gameTime'])
                self.monsterType = data['monsterType']
                self.dragonType = data['dragonType']
            case 'ANNOUNCED_ANCIENT':
                self.gameTime = timedelta(milliseconds=data['gameTime'])
                self.monsterType = data['monsterType']
                self.dragonType = data['dragonType']
                self.spawnGameTime = data['spawnGameTime']
            case 'EXPIRED_ITEM':
                self.gameTime = timedelta(milliseconds=data['gameTime'])
                self.item = ddragon_factory.itemFromId(data['item'], version)
                if data['playerUrn'] is not None:
                    self.player = game.players[data['playerUrn']]
                else:
                    self.player = None
            case 'TOOK_OBJECTIVE':
                self.gameTime = timedelta(milliseconds=data['gameTime'])
                self.position = EventPosition(data['position'])
                self.assistants = [game.players[a] for a in data['assistants']]
                if data['killerUrn'] is not None:
                    self.killer = game.players[data['killerUrn']]
                    self.implicatedParticipants = [self.killer] + self.assistants
                else:
                    self.killer = None
                    self.implicatedParticipants = self.assistants

                self.buildingType = data['buildingType']
                self.lane = data['lane']
                self.turretTier = data['turretTier']
            case 'END_MAP':
                self.gameTime = timedelta(milliseconds=data['gameTime'])
                self.winningTeamUrn = data['winningTeamUrn']
            case 'ROLLBACK':
                self.gameTime = timedelta(milliseconds=data['gameTime'])

            case _:
                pprint.pp(data)
                raise Exception("Event not handled")


class Player:
    def __init__(self, playerData):
        self.urn = playerData['urn']
        self.references = playerData['references']
        self.name = playerData['name']
        self.esportsId = playerData['esportsId']
        self.summonerName = playerData['summonerName']


class Position:
    def __init__(self, positionData, gameTime):
        self.x = positionData['position'][0]
        self.y = positionData['position'][1]
        self.gameTime = timedelta(milliseconds=gameTime)
        self.playerUrn = positionData['playerUrn']

        self.normalized = DefaultMunch.fromDict(
            {'x': (self.x - maps[11].min_x) / (maps[11].max_x - maps[11].min_x),
             'y': (self.y - maps[11].min_y) / (maps[11].max_y - maps[11].min_y)
             }
        )


class EventPosition:
    def __init__(self, position):
        self.x, self.y = position
        self.normalized = DefaultMunch.fromDict(
            {'x': (self.x - maps[11].min_x) / (maps[11].max_x - maps[11].min_x),
             'y': (self.y - maps[11].min_y) / (maps[11].max_y - maps[11].min_y)
             }
        )


class PlayerSnapshotStatEvent:
    def __init__(self, statData, version, gameTime):
        self.statData = statData
        self.timestamp = timedelta(milliseconds=gameTime)
        self.participantId = statData['participantID']
        self.teamId = statData['teamID']
        self.keystone = ddragon_factory.runeFromId(statData['keystoneID'], version)
        self.champion = ddragon_factory.championFromId(statData['championID'], version)
        self.summonerName = statData['summonerName']
        self.level = statData['level']
        self.experience = statData['experience']

        self.battleStats = DefaultMunch.fromDict(
            {
                'attackDamage': statData['attackDamage'],
                'attackSpeed': statData['attackSpeed'],
                'healthMax': statData['healthMax'],
                'healthRegen': statData['healthRegen'],
                'magicResist': statData['magicResist'],
                'magicPenetration': statData['magicPenetration'],
                'magicPenetrationPercent': statData['magicPenetrationPercent'],
                'armor': statData['armor'],
                'armorPenetration': statData['armorPenetration'],
                'armorPenetrationPercent': statData['armorPenetrationPercent'],
                'armorPenetrationPercentBonus': statData['armorPenetrationPercentBonus'],
                'abilityPower': statData['abilityPower'],
                'primaryAbilityResource': statData['primaryAbilityResource'],
                'primaryAbilityResourceRegen': statData['primaryAbilityResourceRegen'],
                'primaryAbilityResourceMax': statData['primaryAbilityResourceMax'],
                'ccReduction': statData['ccReduction'],
                'cooldownReduction': statData['cooldownReduction'],
                'lifeSteal': statData['lifeSteal'],
                'spellVamp': statData['spellVamp'],
            }
        )
        self.alive = statData['alive']
        self.respawnTimer = statData['respawnTimer']
        self.health = statData['health']
        self.currentGold = statData['currentGold']
        self.totalGold = statData['totalGold']
        self.goldPerSecond = statData['goldPerSecond']
        self.position = statData['position']
        self.items = [ddragon_factory.itemFromId(item['itemID'], version) for item in statData['items']]
        for i in range(len(self.items)):
            self.items[i].stackSize = statData['items'][i]['stackSize']
            self.items[i].purchaseGameTime = timedelta(milliseconds=statData['items'][i]['purchaseGameTime'])
            self.items[i].cooldownRemaining = timedelta(milliseconds=statData['items'][i]['cooldownRemaining'])

        self.itemsUndo = [ddragon_factory.itemFromId(item['itemID'], version) for item in statData['itemsUndo']]
        self.itemsSold = [ddragon_factory.itemFromId(item['itemID'], version) for item in statData['itemsSold']]
        self.minionsKilled = statData['stats']['minionsKilled']
        self.neutralMinionsKilled = statData['stats']['neutralMinionsKilled']
        self.neutralMinionsKilledYourJungle = statData['stats']['neutralMinionsKilledYourJungle']
        self.neutralMinionsKilledEnemyJungle = statData['stats']['neutralMinionsKilledEnemyJungle']
        self.championsKilled = statData['stats']['championsKilled']
        self.numDeaths = statData['stats']['numDeaths']
        self.assists = statData['stats']['assists']
        
        self.runes = [ddragon_factory.runeFromId(p['value'], version) for p in statData['stats']['perks']]
        self.runeStats = [{'var1': p['var1'], 'var2': p['var2'], 'var3': p['var3']} for p in statData['stats']['perks']]
        self.wardPlaced = statData['stats']['wardPlaced']
        self.wardKilled = statData['stats']['wardKilled']
        self.visionScore = statData['stats']['visionScore']
        self.totalDamageDealt = statData['stats']['totalDamageDealt']
        self.physicalDamageDealtPlayer = statData['stats']['physicalDamageDealtPlayer']
        self.magicDamageDealtPlayer = statData['stats']['magicDamageDealtPlayer']
        self.trueDamageDealtPlayer = statData['stats']['trueDamageDealtPlayer']
        self.totalDamageDealtChampions = statData['stats']['totalDamageDealtChampions']
        self.physicalDamageDealtChampions = statData['stats']['physicalDamageDealtChampions']
        self.magicDamageDealtChampions = statData['stats']['magicDamageDealtChampions']
        self.trueDamageDealtChampions = statData['stats']['trueDamageDealtChampions']
        self.totalDamageTaken = statData['stats']['totalDamageTaken']
        self.physicalDamageTaken = statData['stats']['physicalDamageTaken']
        self.magicDamageTaken = statData['stats']['magicDamageTaken']
        self.trueDamageTaken = statData['stats']['trueDamageTaken']
        self.totalDamageSelfMitigated = statData['stats']['totalDamageSelfMitigated']
        self.totalDamageShieldedOnTeammates = statData['stats']['totalDamageShieldedOnTeammates']
        self.totalDamageDealtToBuildings = statData['stats']['totalDamageDealtToBuildings']
        self.totalDamageDealtToTurrets = statData['stats']['totalDamageDealtToTurrets']
        self.totalDamageDealtToObjectives = statData['stats']['totalDamageDealtToObjectives']
        self.totalTimeCrowdControlDealt = statData['stats']['totalTimeCrowdControlDealt']
        self.totalTimeCCOthers = statData['stats']['totalTimeCCOthers']
        self.summoner_spell_1 = DefaultMunch.fromDict(statData['spell1'])
        self.summoner_spell_2 = DefaultMunch.fromDict(statData['spell2'])
        self.ultimate = DefaultMunch.fromDict(statData['ultimate'])
        try:
            self.skills = DefaultMunch.fromDict(statData["skills"])
        except:
            self.skills = None
