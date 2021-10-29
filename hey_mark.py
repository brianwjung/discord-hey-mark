import discord
import json
import os
import requests
import pytz

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
    print(f"Team Name {team_name} not found.")
    return False

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

class HeyMark(discord.Client):
    async def on_ready(self):
        print(f"Logged on as {self.user}!")

    async def on_message(self, message):
        print(f"Message from {message.author}: {message.content}")
        if message.author != self.user:
            if message.content.startswith('!heymark'):
                parsed_message = message.content.split(' ')
                team_name = normalize(parsed_message[1])
                cmd = normalize(parsed_message[2])
                team_name, team_id = get_team_name_id(team_name)
                if team_id is False:
                    await message.channel.send(f"Unable to find team that has the name: {team_name}")
                if cmd == "schedule":
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
                elif cmd == "standings":
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
                    response = f"""**Unrecognized command**:\n**Format**: *!heymark <team name> <command>*\n**Valid Commands**: *<schedule|standings|~~stats~~>*\n\n**Example**: *!heymark canucks schedule*"""
                    await message.channel.send(response)

client = HeyMark()
client.run(DISCORD_TOKEN)