from discord.ext import commands
import discord
import random
import re
import time
import asyncio
import os
import json
import requests
from groq import Groq

# Fetch API key and Discord token from environment variables
API_KEY = os.getenv("GROQ_API_KEY")
TOKEN = os.getenv('DISCORD_TOKEN')

if not API_KEY or not TOKEN:
    raise ValueError("API key or Discord token is not set in environment variables.")

client = Groq(api_key=API_KEY)
intents = discord.Intents.default()
intents.message_content = True
discord_bot = commands.Bot(command_prefix='.', intents=intents)

# Function to fetch random words
def generate_words():
    response = requests.get("https://random-word-api.herokuapp.com/word?number=2")
    return response.json()

# Function to get Unamon info from Groq API
def get_unamon_info(client, words):
    prompt = (
        f"Come up with a unique Unamon (a Fakemon of my universe), along with a creative name for it, its typing(s) and a detailed design, "
        f"that combines the concepts of '{words[0]}' and '{words[1]}'. Please make sure that the name of the Unamon "
        f"MUST be the very first word of the text. Do not generate any stats yet, only the name, type(s) and design (Biology including physical description, Behaviour)"
    )
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        temperature=1,
        max_tokens=800,
        top_p=1,
        stream=False
    )
    unamon_desc = response.choices[0].message.content
    unamon_name = re.sub(r"[^a-zA-Z]", "", unamon_desc.split()[0])
    return unamon_name, unamon_desc

# Function to generate Unamon stats from Groq API
def generate_stats(client, unamon_name):
    prompt = (
        f"Come up with the appropriate following stats/info for {unamon_name}:\n"
        "Signature Move (with a short description), its PP, Attack DMG, Accuracy %, the move's type, the effectiveness percentage, and the level it's learned\n"
        "The Category of the Unamon\n"
        "Its height and weight in imperial units\n"
        "Its cry in onomatopoeia\n"
        "Its stats (HP, ATK, DEF, SpA, SpD, and Speed).\n"
        "Evolves from/into (if any)\n"
        "An interesting, unique, and creative PokéDex entry.\n"
        "3 existing abilities that it can learn (with a short description of what it does), last of them being a Hidden Ability"
    )
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        temperature=1,
        max_tokens=800,
        top_p=1,
        stream=False
    )
    return response.choices[0].message.content

# Function to handle file operations safely
def safe_file_read(file_path):
    try:
        with open(file_path, "r") as f:
            return [line.strip() for line in f.readlines()]  # Return a list of strings
    except FileNotFoundError:
        return []

def safe_file_write(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f)

# Function to get Unamon by name for a specific user
def get_unamon_by_name(user_id, name):
    caught_unamon = safe_file_read("caught_unamon.txt")
    return next((unamon for unamon in caught_unamon.get(str(user_id), []) if unamon["name"] == name), None)

# Function to get training Unamon by user
def get_training_unamon_by_user(user_id):
    lines = safe_file_read("unamon_training.txt")
    for line in lines:
        parts = line.strip().split(",")
        if parts[0] == str(user_id):
            return int(parts[0]), parts[1], int(parts[2]), int(parts[3])
    return None

# Function to update training Unamon
def update_training_unamon(user_id, unamon_name, level, current_xp):
    new_lines = []
    lines = safe_file_read("unamon_training.txt")
    for line in lines:
        line_parts = line.strip().split(",")
        if line_parts[0] == str(user_id) and line_parts[1] == unamon_name:
            new_lines.append(f"{user_id},{unamon_name},{level},{current_xp}")
        else:
            new_lines.append(line.strip())
    safe_file_write("unamon_training.txt", "\n".join(new_lines))

@discord_bot.event
async def on_ready():
    print('Bot is readyyyyyy')
    embed = discord.Embed(title="Hello!", description="I'm ready to discover some new Unamon!", color=discord.Color.blue())
    embed.set_author(name="Unamon Generator", icon_url="https://i.imgur.com/6EkzZWy.png")
    await discord_bot.get_channel(1095804559198273648).send(embed=embed)

@discord_bot.command()
async def gen(ctx, *words):
    if not words:
        while True:
            words = generate_words()
            embed = discord.Embed(title="Random words:", description=f"**{words[0]}**\n**{words[1]}**\n\nProceed?", color=discord.Color.blue())
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
            message = await ctx.send(embed=embed)
            await message.add_reaction('👍')
            await message.add_reaction('👎')
            await message.add_reaction('❌')

            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ['👍', '👎', '❌'] and reaction.message == message

            try:
                reaction, user = await discord_bot.wait_for('reaction_add', timeout=60.0, check=check)
            except asyncio.TimeoutError:
                embed = discord.Embed(description=f"Messaged timed out for {ctx.author.mention}. Try again later.", color=discord.Color.red())
                await ctx.send(embed=embed)
                return
            if str(reaction.emoji) == '👍':
                break
            elif str(reaction.emoji) == '❌':
                embed = discord.Embed(description="Cancelled Unamon generation.", color=discord.Color.red())
                embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
                await ctx.send(embed=embed)
                return
            else:
                words = []
                continue
            words = generate_words()
            embed.description = f"**{words[0]}**\n**{words[1]}**"
            await message.edit(embed=embed)

    elif len(words) != 2:
        embed = discord.Embed(description="Please provide either 2 words, or no words to generate an Unamon.", color=discord.Color.red())
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
        return

    embed = discord.Embed(description="Generating Unamon...", color=discord.Color.blue())
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
    msg = await ctx.send(embed=embed)
    try:
        unamon_name, unamon_desc = get_unamon_info(client, words)
    except Exception as e:
        embed = discord.Embed(description=f"Error: {str(e)}", color=discord.Color.red())
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
        return
    color = discord.Color.random()
    embed = discord.Embed(title=f"{unamon_name.upper()}", description=unamon_desc, color=color)
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
    await msg.edit(embed=embed)
    await asyncio.sleep(1)

    embed = discord.Embed(description=f"Generate stats for **{unamon_name}**?", color=discord.Color.blue())
    message = await ctx.send(embed=embed)
    await message.add_reaction("👍")
    await message.add_reaction("👎")

    try:
        reaction, user = await discord_bot.wait_for('reaction_add', check=lambda reaction, user: user == ctx.author and reaction.emoji in ['👍', '👎'], timeout=600.0)
    except asyncio.TimeoutError:
        embed = discord.Embed(description=f"Messaged timed out for {ctx.author.mention}. Try again later.", color=discord.Color.red())
        await ctx.send(embed=embed)
        return

    if reaction.emoji == "👍":
        embed = discord.Embed(description=f"Generating stats for **{unamon_name}**...", color=discord.Color.blue())
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        msg = await ctx.send(embed=embed)
        unamon_stats = generate_stats(client, unamon_name)
        embed = discord.Embed(title=f"{unamon_name.upper()} STATS", description=unamon_stats, color=color)
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        await msg.edit(embed=embed)

        await msg.add_reaction('🎣')

        def check(reaction, user):
            return str(reaction.emoji) == '🎣' and user == ctx.author and reaction.message.id == msg.id

        try:
            reaction, user = await discord_bot.wait_for('reaction_add', timeout=600.0, check=check)
        except asyncio.TimeoutError:
            embed = discord.Embed(description=f"You didn't catch the {unamon_name} in time, {ctx.author.mention}!", color=discord.Color.red())
            await ctx.send(embed=embed)
        else:
            caught_data = safe_file_read("caught_unamon.txt")
            caught_data.setdefault(str(ctx.author.id), []).append({
                "name": unamon_name,
                "description": unamon_desc,
                "stats": unamon_stats,
                "picture": None
            })
            safe_file_write("caught_unamon.txt", caught_data)

            embed = discord.Embed(title=f"Congratulations, {ctx.author.name}!", description=f"You caught **{unamon_name}**!", color=discord.Color.green())
            embed.set_footer(text=f"Type .u to view all your caught Unamon.")
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)
    elif reaction.emoji == "👎":
        embed = discord.Embed(description=f"No stats generated.", color=discord.Color.blue())
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

@discord_bot.command()
async def u(ctx, *, arg=None):
    user_id = str(ctx.author.id)
    caught_unamon = safe_file_read('caught_unamon.txt')

    if user_id not in caught_unamon:
        embed = discord.Embed(title="Oops!", description="You haven't caught any Unamon yet!", color=discord.Color.red())
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
        return

    unamon_list = caught_unamon[user_id]

    if arg is None:
        if not unamon_list:
            embed = discord.Embed(title="Oops!", description="You haven't caught any Unamon yet!", color=discord.Color.red())
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)
            return

        unamon_names = [unamon["name"] for unamon in unamon_list]
        embed = discord.Embed(title=f"{ctx.author.name}'s Caught Unamon", description="\n".join(unamon_names), color=discord.Color.blue())
        embed.set_footer(text="Type .u <name> to view the details of a specific Unamon.")
    else:
        unamon = next((f for f in unamon_list if f["name"].lower() == arg.lower()), None)

        if unamon is None:
            embed = discord.Embed(title="Oops!", description=f"You haven't caught an Unamon named {arg} yet!", color=discord.Color.red())
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)
            return

        color = discord.Color.random()
        embed1 = discord.Embed(title=f"{unamon['name']}'s Description", description=unamon["description"], color=color)
        embed1.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        embed2 = discord.Embed(title=f"{unamon['name']}'s Stats", description=unamon["stats"], color=color)
        embed2.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        if unamon["picture"] is not None:
            embed1.set_thumbnail(url=unamon["picture"])
            embed2.set_thumbnail(url=unamon["picture"])
        message = await ctx.send(embed=embed1)
        await message.add_reaction("⬅️")
        await message.add_reaction("➡️")
        current_embed = 1

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️"] and reaction.message == message

        while True:
            try:
                reaction, user = await discord_bot.wait_for("reaction_add", timeout=300, check=check)

                if str(reaction.emoji) == "⬅️" and current_embed == 2:
                    current_embed = 1
                    await message.edit(embed=embed1)
                    await message.remove_reaction("⬅️", user)
                elif str(reaction.emoji) == "➡️" and current_embed == 1:
                    current_embed = 2
                    await message.edit(embed=embed2)
                    await message.remove_reaction("➡️", user)
                else:
                    await message.remove_reaction(reaction, user)
            except asyncio.TimeoutError:
                break

    embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

@discord_bot.command()
async def train(ctx, *, name: str):
    unamon = get_unamon_by_name(ctx.author.id, name.title())
    if unamon is None:
        embed = discord.Embed(description="You don't have an Unamon with that name.", color=discord.Color.red())
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
        return

    training_unamon = get_training_unamon_by_user(ctx.author.id)
    if training_unamon is not None:
        embed = discord.Embed(description=f"You are already training {training_unamon[1]}!", color=discord.Color.orange())
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
        return

    embed = discord.Embed(description=f"You are now training {unamon['name']}!", color=discord.Color.green())
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

    with open("unamon_training.txt", "a") as f:
        f.write(f"{ctx.author.id},{unamon['name']},1,0\n")

@train.error
async def train_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(description="Please provide a name for the Unamon you want to train.", color=discord.Color.red())
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

@discord_bot.command()
async def xp(ctx):
    training_unamon = get_training_unamon_by_user(ctx.author.id)
    if training_unamon is None:
        embed = discord.Embed(description=f"You are not training any Unamon.", color=discord.Color.red())
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
        return

    user_id, unamon_name, level, current_xp = training_unamon
    required_xp = int(5 * level ** 3 / 4)
    embed = discord.Embed(title=f"{unamon_name.upper()}", description=f"Level: {level}\nXP: {current_xp}/{required_xp}", color=discord.Color.blue())
    embed.add_field(name="Progress", value=f"{'█' * int(current_xp / required_xp * 10)}{'░' * (10 - int(current_xp / required_xp * 10))}")
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

@discord_bot.command()
async def release(ctx, *, name: str):
    unamon = get_unamon_by_name(ctx.author.id, name.title())
    if unamon is None:
        embed = discord.Embed(description=f"You don't have an Unamon with that name.", color=discord.Color.red())
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
        return

    caught_data = safe_file_read("caught_unamon.txt")
    caught_data[str(ctx.author.id)] = [unamon for unamon in caught_data.get(str(ctx.author.id), []) if unamon["name"] != name.title()]
    safe_file_write("caught_unamon.txt", caught_data)

    training_unamon = get_training_unamon_by_user(ctx.author.id)
    if training_unamon is not None and training_unamon[1] == name.title():
        with open("unamon_training.txt", "r") as f:
            lines = f.readlines()
        with open("unamon_training.txt", "w") as f:
            f.writelines(line for line in lines if line.strip() != f"{ctx.author.id},{name.title()},{training_unamon[2]},{training_unamon[3]}")

    embed = discord.Embed(description=f"You let {name.title()} be free!", color=discord.Color.green())
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

@release.error
async def release_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(description="Please provide a name for the Unamon you want to release.", color=discord.Color.red())
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

@discord_bot.command()
async def rename(ctx, *, name: str):
    unamon = get_unamon_by_name(ctx.author.id, name.title())
    if unamon is None:
        embed = discord.Embed(description=f"You don't have an Unamon with that name.", color=discord.Color.red())
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
        return

    embed = discord.Embed(description=f"What would you like to rename {name.title()} to?", color=discord.Color.blue())
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

    def check(message):
        return message.author == ctx.author and message.channel == ctx.channel

    try:
        message = await discord_bot.wait_for("message", timeout=60, check=check)
    except asyncio.TimeoutError:
        embed = discord.Embed(description=f"You didn't respond in time, {ctx.author.mention}!", color=discord.Color.red())
        await ctx.send(embed=embed)
        return

    caught_data = safe_file_read("caught_unamon.txt")
    for unamon in caught_data[str(ctx.author.id)]:
        if unamon["name"] == name.title():
            unamon["name"] = message.content.title()
            break
    safe_file_write("caught_unamon.txt", caught_data)

    embed = discord.Embed(description=f"You have renamed {name.title()} to {message.content.title()}.", color=discord.Color.green())
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

@rename.error
async def rename_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(description="Please provide a name for the Unamon you want to rename.", color=discord.Color.red())
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

@discord_bot.event
async def on_message(message):
    await discord_bot.process_commands(message)

    training_unamon = get_training_unamon_by_user(message.author.id)
    if training_unamon is None:
        return

    user_id, unamon_name, level, current_xp = training_unamon
    xp = int(level ** 1.5 + random.randint(1, 5))
    required_xp = int(5 * level ** 3 / 4)
    current_xp += xp

    if current_xp >= required_xp:
        level += 1
        current_xp = 0
        embed = discord.Embed(description=f"Congratulations! {message.author.mention}'s {unamon_name} has leveled up to level {level}!", color=discord.Color.green())
        await message.channel.send(embed=embed)
    update_training_unamon(user_id, unamon_name, level, current_xp)

    if level == 100:
        embed = discord.Embed(description=f"{message.author.mention}'s {unamon_name} has reached level 100!", color=discord.Color.green())
        await message.channel.send(embed=embed)
        with open("unamon_training.txt", "r") as f:
            lines = f.readlines()
        with open("unamon_training.txt", "w") as f:
            f.writelines(line for line in lines if line.strip() != f"{user_id},{unamon_name},100,0")

@discord_bot.command()
async def addpic(ctx, *, name: str):
    unamon = get_unamon_by_name(ctx.author.id, name.title())
    if unamon is None:
        embed = discord.Embed(description=f"You don't have an Unamon with that name.", color=discord.Color.red())
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
        return

    embed = discord.Embed(description=f"Please provide a picture for {name.title()}.", color=discord.Color.blue())
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

    def check(message):
        return message.author == ctx.author and message.channel == ctx.channel

    try:
        message = await discord_bot.wait_for("message", timeout=60, check=check)
    except asyncio.TimeoutError:
        embed = discord.Embed(description=f"You didn't respond in time, {ctx.author.mention}!", color=discord.Color.red())
        await ctx.send(embed=embed)
        return

    caught_data = safe_file_read("caught_unamon.txt")
    for unamon in caught_data[str(ctx.author.id)]:
        if unamon["name"] == name.title():
            unamon["picture"] = message.content
            break
    safe_file_write("caught_unamon.txt", caught_data)

    embed = discord.Embed(description=f"You have added a picture for {name.title()}.", color=discord.Color.green())
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

@addpic.error
async def addpic_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(description="Please provide a name for the Unamon you want to add a picture to.", color=discord.Color.red())
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

# Help command that displays all commands
discord_bot.remove_command("help")
@discord_bot.command()
async def help(ctx):
    embed = discord.Embed(title="Help", description="Here are all the commands you can use:", color=discord.Color.blue())
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
    embed.add_field(name="Discovering", value="`.gen <word1> <word2>` - Generates an Unamon with the given words.\n`.gen` - Generates an Unamon with random words.", inline=False)
    embed.add_field(name="Examining", value="`.u` - Displays all your caught Unamon.\n`.u <name>` - Displays the details of the Unamon with the given name.\n", inline=False)
    embed.add_field(name="Studying", value="`.rename <name>` - Renames the Unamon with the given name.\n`.addpic <name>` - Adds a picture for the Unamon with the given name.", inline=False)
    embed.add_field(name="Training", value="`.train <name>` - Starts training the Unamon with the given name.\n`.xp` - Displays the progress of your training Unamon.", inline=False)
    embed.add_field(name="Releasing", value="`.release <name>` - Releases the Unamon with the given name.", inline=False)
    await ctx.send(embed=embed)

@discord_bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        embed = discord.Embed(description=f"Invalid command. Type `.help` for a list of commands.", color=discord.Color.red())
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

@discord_bot.command()
async def addunamon(ctx):
    caught_data = safe_file_read("caught_unamon.txt")
    embed = discord.Embed(description=f"Please mention the user you want to add the Unamon to.", color=discord.Color.blue())
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

    def check(message):
        return message.author == ctx.author and message.channel == ctx.channel

    try:
        message = await discord_bot.wait_for("message", timeout=60, check=check)
    except asyncio.TimeoutError:
        embed = discord.Embed(description=f"You didn't respond in time, {ctx.author.mention}!", color=discord.Color.red())
        await ctx.send(embed=embed)
        return
    user = message.mentions[0]

    fields = ["name", "description", "stats", "picture"]
    responses = {}

    for field in fields:
        embed = discord.Embed(description=f"Please provide a {field} for the Unamon.", color=discord.Color.blue())
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

        try:
            message = await discord_bot.wait_for("message", timeout=6000, check=check)
            responses[field] = message.content
        except asyncio.TimeoutError:
            embed = discord.Embed(description=f"You didn't respond in time, {ctx.author.mention}!", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

    caught_data.setdefault(str(user.id), []).append({
        "name": responses["name"].title(),
        "description": responses["description"],
        "stats": responses["stats"],
        "picture": responses["picture"]
    })
    safe_file_write("caught_unamon.txt", caught_data)

    embed = discord.Embed(title=f"Congratulations, {ctx.author.name}!", description=f"You added **{responses['name'].title()}**!", color=discord.Color.green())
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

discord_bot.run(TOKEN)