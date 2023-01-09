import datetime
import pprint

import PIL.ImageColor
from PIL import Image, ImageDraw
from .match import Game
from datetime import timedelta
import os
from munch import DefaultMunch

icon_size = (30, 30)
dirname = os.path.dirname(__file__)
assets_dir = os.path.join(dirname, 'assets/')
color_base_blue = Image.open(os.path.join(assets_dir, "summoners_rift.png")).getpixel((19, 492))
color_base_red = Image.open(os.path.join(assets_dir, "summoners_rift.png")).getpixel((492, 19))
map_size = (512, 512)

monstersSprites = {
    "blueCamp": Image.open(os.path.join(assets_dir, "blueCamp.png")).resize(icon_size),
    "gromp": Image.open(os.path.join(assets_dir, "gromp.png")).resize(icon_size),
    "krug": Image.open(os.path.join(assets_dir, "krug.png")).resize(icon_size),
    "raptor": Image.open(os.path.join(assets_dir, "raptor.png")).resize(icon_size),
    "redCamp": Image.open(os.path.join(assets_dir, "redCamp.png")).resize(icon_size),
    "scuttleCrab": Image.open(os.path.join(assets_dir, "scuttleCrab.png")).resize(icon_size),
    "wolf": Image.open(os.path.join(assets_dir, "wolf.png")).resize(icon_size),
}

color_set = [
    PIL.ImageColor.getrgb("#800000"),
    PIL.ImageColor.getrgb("#aaffc3"),
    PIL.ImageColor.getrgb("#469990"),
    PIL.ImageColor.getrgb("#f58231"),
    PIL.ImageColor.getrgb("#bfef45"),
    PIL.ImageColor.getrgb("#4363d8"),
    PIL.ImageColor.getrgb("#dcbeff"),
    PIL.ImageColor.getrgb("#ffffff"),
    PIL.ImageColor.getrgb("#fabed4"),
    PIL.ImageColor.getrgb("#f032e6"),
]

def draw_ward_map(game: Game, players, start_time, end_time):
    ward_events = []
    for player in players:
        w_e = list(
            filter(
                lambda e: start_time < e.gameTime < end_time and e.type == "PLACED_WARD", game.playerEvents[player.urn]
            )
        )
        ward_events += w_e

    summoners_rift = Image.open(os.path.join(assets_dir, "summoners_rift.png"))
    summoners_rift_draw = ImageDraw.Draw(summoners_rift)

    for event in ward_events:
        pos = (int(event.position.normalized.x * map_size[0]),
               int(map_size[1] - (event.position.normalized.y * map_size[1])))
        sq = (pos[0] - 5, pos[1] - 5, pos[0] + 5, pos[1] + 5)
        summoners_rift_draw.ellipse(sq, fill='red', outline='red')
    return summoners_rift


def draw_events_map(game: Game, player, start_time, end_time, eventsToDraw=["KILLED_ANCIENT", "KILL", "DIED"],
                    summoners_rift=Image.open(os.path.join(assets_dir, "summoners_rift.png"))):
    playerUrn = player.urn
    pid = list(game.players.keys()).index(playerUrn)
    summoners_rift_draw = ImageDraw.Draw(summoners_rift)

    events = game.playerEvents[playerUrn]
    events = list(filter(lambda e: start_time <= e.gameTime <= end_time and e.type in eventsToDraw, events))

    positions = game.positionHistory[playerUrn]
    positions = list(filter(lambda e: start_time <= e.gameTime <= end_time, positions))

    for index, position in enumerate(positions[:-2]):
        index_position = (positions[index + 1].normalized.x * map_size[0],
                          map_size[1] - (positions[index + 1].normalized.y * map_size[1]))
        next_position = (positions[index].normalized.x * map_size[0],
                         map_size[1] - (positions[index].normalized.y * map_size[1]))

        if summoners_rift.getpixel(
                index_position
        ) not in (color_base_blue, color_base_red) and summoners_rift.getpixel(
            next_position
        ) not in (color_base_blue, color_base_red):
            summoners_rift_draw.line((index_position, next_position), fill=color_set[pid], width=2)

    for event in events:
        timer = ':'.join(str(event.gameTime).split('.')[0].split(':')[1:3])
        if event.type == 'KILLED_ANCIENT':
            pos = (int(event.position.normalized.x * map_size[0]),
                   int(map_size[1] - (event.position.normalized.y * map_size[1])))
            summoners_rift.paste(monstersSprites[event.monsterType], pos)
            summoners_rift_draw.text(pos, timer)

        elif event.type == "KILL":
            pos = (int(event.position.normalized.x * map_size[0]),
                   int(map_size[1] - (event.position.normalized.y * map_size[1])))
            sprite = game.statsHistory[event.victim.urn][0].champion.icon()
            summoners_rift.paste(sprite, pos)
            summoners_rift_draw.text(pos, timer)

        elif event.type == "DIED":
            pos = (int(event.position.normalized.x * map_size[0]),
                   int(map_size[1] - (event.position.normalized.y * map_size[1])))
            summoners_rift_draw.text(pos, "D.")

    return summoners_rift


def first_base_timestamps(game, player):
    start_time = timedelta(milliseconds=90000)
    current_timestamp = start_time
    summoners_rift = Image.open(os.path.join(assets_dir, "summoners_rift.png"))
    for position in game.positionHistory[player.urn]:
        if position.gameTime > start_time:
            index_position = (position.normalized.x * map_size[0],
                              map_size[1] - (position.normalized.y * map_size[1]))
            if summoners_rift.getpixel(index_position) not in (color_base_blue, color_base_red):
                current_timestamp = position.gameTime
            else:
                return start_time, current_timestamp
    return start_time, current_timestamp


def get_bases_timestamps(game, player, base_index, start_time):

    current_timestamp = start_time
    summoners_rift = Image.open(os.path.join(assets_dir, "summoners_rift.png"))
    is_in_base = False
    base_timings = []

    for position in game.positionHistory[player.urn]:
        if position.gameTime > start_time:
            index_position = (position.normalized.x * map_size[0], map_size[1] - (position.normalized.y * map_size[1]))

            if summoners_rift.getpixel(index_position) in (color_base_blue, color_base_red) and not is_in_base:
                base_timings.append(position.gameTime)
                is_in_base = True
                if len(base_timings) == base_index:
                    return position.gameTime
            else:
                is_in_base = False
    raise Exception("Player didn't base",base_index,"times")


def find_event_timestamp(event_type, game, player=None):
    eventTypes = ["Game start", "Camps spawn", "First base", "Second base", "Third base", "First drake", "Second drake",
                  "Third drake", "Fourth drake", "First Baron",
                  "First gank", "Second gank", "Third gank", "First herald", "Second herald", "First turret",
                  "Second turret"]
    match event_type:
        case "Game start":
            return datetime.timedelta(seconds=0)
        case "Camps spawn":
            return datetime.timedelta(seconds=90)
        case "First base":
            if player is None:
                raise AssertionError("If event type is", event_type, "then player must be defined")
            else:
                return get_bases_timestamps(game, player, 1, datetime.timedelta(seconds=90))
        case "Second base":
            if player is None:
                raise AssertionError("If event type is", event_type, "then player must be defined")
            else:
                return get_bases_timestamps(game, player, 2, datetime.timedelta(seconds=90))
        case "Third base":
            if player is None:
                raise AssertionError("If event type is", event_type, "then player must be defined")
            else:
                return get_bases_timestamps(game, player, 3, datetime.timedelta(seconds=90))
        case "First drake":
            for event in game.events:

                if event.type == "KILLED_ANCIENT" and (event.monsterType=="dragon" or event.monsterType=="dragon"):
                    return event.gameTime
        case "Second drake":
            drakes = 0
            for event in game.events:

                if event.type == "KILLED_ANCIENT" and (event.monsterType == "dragon") and drakes == 1:
                    return event.gameTime
                elif event.type == "KILLED_ANCIENT" and (event.monsterType == "dragon"):
                    drakes += 1
