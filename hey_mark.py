import discord
import json
import os
import pytz
import requests
import subprocess

from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_HEY_MARK_CLIENT_SECRET')
TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

def load_team_data(file_path):
    input_file = open(file_path)
    file_contents = json.loads(input_file.read())
    return file_contents

def get_team_name_id(team_name):
    team_list = load_team_data('./data/teams.json')['teams']
    for team in team_list:
        if team_name in team['name'].lower():
            print(f"Team found: {team['name']}")
            print(f"Team ID is: {team['id']}")
            return team['name'], team['id']
    return False, None

def get_current_week_range():
    current_date = datetime.now()
    current_date_string = current_date.strftime("%Y-%m-%d")
    start = (current_date - timedelta(days=current_date.weekday()))
    end = (start + timedelta(days=6)).strftime("%Y-%m-%d")
    return current_date_string, end

def get_team_schedule(team_id):
    game_times = []
    home_teams = []
    away_teams = []
    start_date, end_date = get_current_week_range()
    schedule_url = f"https://statsapi.web.nhl.com/api/v1/schedule?teamId={team_id}&startDate={start_date}&endDate={end_date}"
    schedule_response = json.loads(requests.get(schedule_url).content)
    dates_list = schedule_response['dates']
    for date in dates_list:
        for game in date['games']:
            formatted_date_time = datetime.strptime(game['gameDate'], TIME_FORMAT)
            pacific_timezone = pytz.timezone("US/Pacific")
            eastern_timezone = pytz.timezone("US/Eastern")
            game_time_msg = f"""- **Normal Time**: {formatted_date_time.astimezone(eastern_timezone)}\n- **Canada Time**: {formatted_date_time.astimezone(pacific_timezone)}"""
            home_team_msg = f"{game['teams']['home']['team']['name']}"
            away_team_msg = f"{game['teams']['away']['team']['name']}"
            game_times.append(game_time_msg)
            home_teams.append(home_team_msg)
            away_teams.append(away_team_msg)
    return game_times, home_teams, away_teams

def get_team_standings(team_id):
    standings_url = f"https://statsapi.web.nhl.com/api/v1/teams/{team_id}/stats"
    standings_response = json.loads(requests.get(standings_url).content)['stats'][0]['splits'][0]
    games_played = standings_response['stat']['gamesPlayed']
    games_won = standings_response['stat']['wins']
    games_lost = standings_response['stat']['losses']
    ot = standings_response['stat']['ot']
    return games_played, games_won, games_lost, ot

def normalize(word):
    lowercased = word.lower()
    return lowercased

def write_thing(thing, cmd_string):
    try:
        with open(f"./private/{cmd_string}_list.txt", 'a') as write_list:
            write_list.write(f"{thing}\n")
            print(f"Successfully added: {thing}")
        write_list.close()
    except Exception as e:
        print(f"I failed to remember: {thing} in {cmd_string}_list because: {e}")
        return False
    return True

def read_thing(cmd_string):
    try:
        with open(f"./private/{cmd_string}_list.txt", 'r') as read_list:
            string_list = read_list.read()
            return string_list
    except Exception as e:
        print(f"Error when reading {cmd_string}_list becaue {e}")
        return False

def remove_thing(thing, cmd_string):
    list_name = ""
    if "watch" in cmd_string.lower():
        list_name = "watch"
    elif "remember" in cmd_string.lower():
        list_name = "remember"
    else:
        return False
    try:
        # sed -i '/pattern to match/d' ./infile
        expression_string = f"/{thing}/d"
        file_path = f"./private/{list_name}_list.txt"
        sed_result = subprocess.call(["sed", "-i", expression_string, file_path])
        if sed_result == 0:
            return True
    except Exception as e:
        print(f"I broke when trying to remove {thing} from {list_name}_list.txt because {e}")
        return False

class HeyMark(discord.Client):
    async def on_ready(self):
        print(f"Logged on as {self.user}!")

    async def on_message(self, message):
        print(f"Message from {message.author}: {message.content}")
        if message.author != self.user:
            if message.content.startswith('!heymark'):
                parsed_message = message.content.split(' ')
                subject = normalize(parsed_message[1])
                joined_action = ' '.join(parsed_message[2:])
                action = normalize(joined_action)
                team_name, team_id = get_team_name_id(subject)
                if team_name is False or team_name is None:
                    if (subject == "watch" or subject == "remember") and action != "list":
                        watch_result = write_thing(action, subject)
                        if watch_result:
                            await message.channel.send(f"Successfully added {action} to {subject} list!")
                        else:
                            await message.channel.send(f"Failed to add {action} to {subject} list. Shit's broke!")
                    elif (subject == "watch" or subject == "remember") and action == "list":
                        read_result = read_thing(subject)
                        message_embed = discord.Embed(title=f"Success!", color=0x008080)
                        message_embed.set_author(name="HeyMark")
                        message_embed.set_thumbnail(url="https://i.imgur.com/6NVLtGF.png")
                        message_embed.add_field(name=f"{subject.capitalize()} List", value=read_result, inline=False)
                        await message.channel.send(embed=message_embed)
                    elif (subject == "watched" or subject == "remembered"):
                        remove_result = remove_thing(action, subject)
                        if remove_result:
                            await message.channel.send(f"> Successfully removed {action} from list!")
                        else:
                            await message.channel.send(f"Failed to remove {action} because I'm broken.")
                    else:
                        response = f"""**Unrecognized command**:\n**Format**:\n  *!heymark <team name> <schedule|standings>*\n  *!heymark <watch|remember> <thing>*\n *!heymark <watch|remember> list*\n *!heymark <watched|remembered> <thing>*"""
                        await message.channel.send(response)
                else:
                    if action == "schedule":
                        game_times, home_teams, away_teams = get_team_schedule(team_id)
                        for time, home, away in zip(game_times, home_teams, away_teams):
                            message_embed = discord.Embed(title=f"{team_name} Schedule", color=0x008080)
                            message_embed.set_author(name="HeyMark")
                            message_embed.set_thumbnail(url="https://i.imgur.com/6NVLtGF.png")
                            message_embed.add_field(name="Dates", value=time, inline=False)
                            message_embed.add_field(name="Home Team", value=home, inline=False)
                            message_embed.add_field(name="Away Team", value=away, inline=False)
                            message_embed.set_footer(text="Plan accordingly!")
                            await message.channel.send(embed=message_embed)
                    elif action == "standings":
                        games_played, games_won, games_lost, ot = get_team_standings(team_id)
                        message_embed = discord.Embed(title=f"{team_name} Standings", color=0x008080)
                        message_embed.set_author(name="HeyMark")
                        message_embed.set_thumbnail(url="https://i.imgur.com/6NVLtGF.png")
                        message_embed.add_field(name="Games Played", value=games_played, inline=False)
                        message_embed.add_field(name="Games Won", value=games_won, inline=False)
                        message_embed.add_field(name="Games Lost", value=games_lost, inline=False)
                        message_embed.add_field(name="Overtime", value=ot, inline=False)
                        message_embed.set_footer(text="GG!")
                        await message.channel.send(embed=message_embed)
                    else:
                        response = f"""**Unrecognized command**:\n**Format**:\n  *!heymark <team name> <schedule|standings>*\n  *!heymark <watch|remember> <thing>*\n *!heymark <watch|remember> list*\n *!heymark <watched|remembered> <thing>"""
                        await message.channel.send(response)

client = HeyMark()
client.run(DISCORD_TOKEN)