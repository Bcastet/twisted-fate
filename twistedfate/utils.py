from PIL import Image, ImageDraw
from .match import Game
from datetime import timedelta
import os

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


def draw_events_map(game: Game, player, start_time, end_time):
    playerUrn = player.urn
    summoners_rift = Image.open(os.path.join(assets_dir, "summoners_rift.png"))
    summoners_rift_draw = ImageDraw.Draw(summoners_rift)

    events = game.playerEvents[playerUrn]
    events = list(filter(lambda e: start_time < e.gameTime < end_time, events))

    positions = game.positionHistory[playerUrn]
    positions = list(filter(lambda e: start_time < e.gameTime < end_time, positions))

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
            summoners_rift_draw.line((index_position, next_position), fill=(255, 255, 255), width=2)

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
