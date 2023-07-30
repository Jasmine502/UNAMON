from discord.ext import commands
from dotenv import load_dotenv
import discord, random, poe, requests, re, time, asyncio, os, json


load_dotenv()  # load environment variables from .env file

TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.default()
intents.message_content = True

client = commands.Bot(command_prefix='.', intents=intents)

def generate_words():
    response = requests.get("https://random-word-api.herokuapp.com/word?number=2")
    return response.json()

# Function to get Unamon name and description from Poe API
def get_unamon_info(client, words):
    # Construct message for Poe API
    message = f"Come up with a unique Unamon (a Fakemon of my universe), along with its typing(s) and a detailed design, that combines the concepts of '{words[0]}' and '{words[1]}'. Please make sure that the name of the Unamon MUST be the very first word of the text"
    
    # Send message to Poe API
    response = ""
    for chunk in client.send_message("chinchilla", message):
        response += chunk["text_new"]
    
    # Remove any non-alphabetic characters from Unamon name
    unamon_name = re.sub(r"[^a-zA-Z]", "", response.split()[0])
    unamon_desc = response.strip()

    return unamon_name, unamon_desc

def generate_stats(client, unamon_name):
    # Prompt for Unamon stats
    prompt = f"Come up with the appropriate following stats/info for {unamon_name}:\n" \
             "Signature Move (with a short description), it's PP, Attack DMG, Accuracy %, the move's type, the effectiveness percentage, and the level it's learned\n" \
             "The Category of the Unamon\n" \
             "It's height and weight in imperial units\n" \
             "It's cry in onomatopoeia\n" \
             "It's stats (HP, ATK, DEF, SpA, SpD and Speed).\n" \
             "Evolves from/into (if any)\n" \
             "An interesting, unique and creative PokéDex entry.\n" \
             "3 existing abilities that it can learn (with a short description of what it does), last of them being a Hidden Ability"
    
    # Send prompt to Poe API and get response
    response = ""
    for chunk in client.send_message("chinchilla", prompt):
        response += chunk["text_new"]
    
    return response


def get_unamon_by_name(user_id, name):
    with open("caught_unamon.txt", "r") as f:
        caught_unamon = json.load(f)
    if str(user_id) not in caught_unamon:
        return None
    for unamon in caught_unamon[str(user_id)]:
        if unamon["name"] == name:
            return unamon
    return None


def get_training_unamon_by_user(user_id):
    with open("unamon_training.txt", "r") as f:
        lines = f.readlines()
        for line in lines:
            parts = line.strip().split(",")
            if parts[0] == str(user_id):
                return (int(parts[0]), parts[1], int(parts[2]), int(parts[3]))
    return None


def update_training_unamon(user_id, unamon_name, level, current_xp):
    new_lines = []
    with open("unamon_training.txt", "r") as f:
        for line in f:
            line_parts = line.strip().split(",")
            if line_parts[0] == str(user_id) and line_parts[1] == unamon_name:
                new_lines.append(f"{user_id},{unamon_name},{level},{current_xp}")
            else:
                new_lines.append(line.strip())

    with open("unamon_training.txt", "w") as f:
        f.write("\n".join(new_lines))


@client.event
async def on_ready():
    print('Bot is readyyyyyy')

    # Display with an embed a greeting from the bot
    embed = discord.Embed(title="Hello!", description="I'm ready to discover some new Unamon!", color=discord.Color.blue())
    embed.set_author(name="Unamon Generator", icon_url="https://i.imgur.com/6EkzZWy.png")
    await client.get_channel(1095804559198273648).send(embed=embed)


@client.command()
async def gen(ctx, *words):
    # Map user IDs to Poe API tokens
    users = {}
    for user_id in os.environ:
        user_id = str(ctx.author.id)
        users[user_id] = os.getenv(user_id)
    pToken = users.get(user_id)

    # If user or token not found, return
    if not pToken:
        embed = discord.Embed(description=f"Sorry, you are not recognised as a user, or your token is invalid.", color=discord.Color.red())
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
        return
    
    # Submit token and clear context
    pClient = poe.Client(pToken)

    # Clear context to Poe API
    pClient.send_chat_break("chinchilla")

    # If no words provided, generate random words
    if not words:
        while True:
            words = generate_words()
            embed = discord.Embed(title=f"Random words:", description=f"**{words[0]}**\n**{words[1]}**\n\nProceed?", color=discord.Color.blue())
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
            message = await ctx.send(embed=embed)
            await message.add_reaction('👍')
            await message.add_reaction('👎')
            await message.add_reaction('❌')
            
            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ['👍', '👎', '❌'] and reaction.message == message
            
            try:
                reaction, user = await client.wait_for('reaction_add', timeout=60.0, check=check)
            except asyncio.TimeoutError:
                embed = discord.Embed(description=f"Messaged timed out for {ctx.author.mention}. Try again later.", color=discord.Color.red())
                await ctx.send(embed=embed)
                return
            if str(reaction.emoji) == '👍':
                break
            elif str(reaction.emoji) == '❌':
                embed = discord.Embed(description=f"Cancelled Unamon generation.", color=discord.Color.red())
                embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
                await ctx.send(embed=embed)
                return
            else:
                words = []
                continue
            words = generate_words()
            embed.description = f"**{words[0]}**\n**{words[1]}**"
            await message.edit(embed=embed)


    # If custom words provided, validate the input
    elif len(words) != 2:
        embed = discord.Embed(description=f"Please provide either 2 words, or no words to generate an Unamon.", color=discord.Color.red())
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
        return

 # Generate Unamon description with Poe
    embed = discord.Embed(description=f"Generating Unamon...", color=discord.Color.blue())
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
    msg = await ctx.send(embed=embed)
    try:
        unamon_name, unamon_desc = get_unamon_info(pClient, words)
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

    # Ask if user wants to generate stats from the above description
    embed = discord.Embed(description=f"Generate stats for **{unamon_name}**?", color=discord.Color.blue())
    message = await ctx.send(embed=embed)
    await message.add_reaction("👍")
    await message.add_reaction("👎")
    
    try:
        reaction, user = await client.wait_for('reaction_add', check=lambda reaction, user: user == ctx.author and reaction.emoji in ['👍', '👎'], timeout=600.0)
    except asyncio.TimeoutError:
        embed = discord.Embed(description=f"Messaged timed out for {ctx.author.mention}. Try again later.", color=discord.Color.red())
        await ctx.send(embed=embed)
        return
        
    # If user wants to generate stats, generate them with Poe
    if reaction.emoji == "👍":
        embed = discord.Embed(description=f"Generating stats for **{unamon_name}**...", color=discord.Color.blue())
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        msg = await ctx.send(embed=embed)
        unamon_stats = generate_stats(pClient, unamon_name)
        embed = discord.Embed(title=f"{unamon_name.upper()} STATS", description=unamon_stats, color=color)
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        await msg.edit(embed=embed)

        # Add the 🎣 reaction to the message
        await msg.add_reaction('🎣')

        # Define a function to check if the user reacted with 🎣
        def check(reaction, user):
            return str(reaction.emoji) == '🎣' and user == ctx.author and reaction.message.id == msg.id

        # Wait for the user to react with 🎣
        try:
            reaction, user = await client.wait_for('reaction_add', timeout=600.0, check=check)
        except asyncio.TimeoutError:
            embed = discord.Embed(description=f"You didn't catch the {unamon_name} in time, {ctx.author.mention}!", color=discord.Color.red())
            await ctx.send(embed=embed)
        else:
            # Load the caught Unamon file
            caught_file = os.path.join(os.path.dirname(__file__), "caught_unamon.txt")
            if not os.path.exists(caught_file):
                with open(caught_file, "w") as f:
                    f.write(json.dumps({}))
            with open(caught_file, "r") as f:
                caught_data = json.loads(f.read())

            # Add the caught Unamon to the file
            caught_data.setdefault(str(ctx.author.id), [])
            caught_data[str(ctx.author.id)].append({
                "name": unamon_name,
                "description": unamon_desc,
                "stats": unamon_stats,
                "picture": None
            })
            with open(caught_file, "w") as f:
                f.write(json.dumps(caught_data))

            # Send a congratulatory message
            embed = discord.Embed(title=f"Congratulations, {ctx.author.name}!", description=f"You caught **{unamon_name}**!", color=discord.Color.green())
            embed.set_footer(text=f"Type .u to view all your caught Unamon.")
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)
    elif reaction.emoji == "👎":
        embed = discord.Embed(description=f"No stats generated.", color=discord.Color.blue())
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

@client.command()
async def u(ctx, *, arg=None):
    user_id = str(ctx.author.id)
    
    with open('caught_unamon.txt', 'r') as f:
        caught_unamon = json.load(f)
    
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
        # add thumbnail if it exists
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
                reaction, user = await client.wait_for("reaction_add", timeout=300, check=check)
                
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
        
        return
    
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)


@client.command()
async def train(ctx, *, name: str):
    unamon = get_unamon_by_name(ctx.author.id, name.title())
    if unamon is None:
        embed = discord.Embed(description="You don't have an Unamon with that name.", color=discord.Color.red())
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
        return


    # Check if the user is already training an Unamon
    training_unamon = get_training_unamon_by_user(ctx.author.id)
    if training_unamon is not None:
        embed = discord.Embed(description=f"You are already training {training_unamon[1]}!", color=discord.Color.orange())
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
        return

    embed = discord.Embed(description=f"You are now training {unamon['name']}!", color=discord.Color.green())
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

    # Add the Unamon to the unamon_training.txt file with level 1
    with open("unamon_training.txt", "a") as f:
        f.write(f"{ctx.author.id},{unamon['name']},1,0\n")


# Handle invalid train parameters
@train.error
async def train_error(ctx, error):
    # Check if the error is a missing parameter error
    if isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(description="Please provide a name for the Unamon you want to train.", color=discord.Color.red())
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
        return
    

# Handle the case where paramaters are not provided
@train.error
async def train_error(ctx, error):
    # Check if the error is a missing parameter error
    if isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(description="Please provide a name for the Unamon you want to train.", color=discord.Color.red())
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
        return

# A command that allows users to check the progress of their training Unamon
@client.command()
async def xp(ctx):
    # Check if the user is training an Unamon
    training_unamon = get_training_unamon_by_user(ctx.author.id)
    if training_unamon is None:
        embed = discord.Embed(description=f"You are not training any Unamon.", color=discord.Color.red())
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
        return

    # Display the progress of the Unamon in an organised embed, with a progress bar of the XP
    user_id, unamon_name, level, current_xp = training_unamon
    required_xp = int(5 * level ** 3 / 4)
    embed = discord.Embed(title=f"{unamon_name.upper()}", description=f"Level: {level}\nXP: {current_xp}/{required_xp}", color=discord.Color.blue())
    embed.add_field(name="Progress", value=f"{'█' * int(current_xp / required_xp * 10)}{'░' * (10 - int(current_xp / required_xp * 10))}")
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)


# A command that allows users to release their Unamon of choice
@client.command()
async def release(ctx, *, name: str):
    # Check if the user has the Unamon they want to release
    unamon = get_unamon_by_name(ctx.author.id, name.title())
    if unamon is None:
        embed = discord.Embed(description=f"You don't have an Unamon with that name.", color=discord.Color.red())
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
        return

    # Load the caught Unamon file
    caught_file = os.path.join(os.path.dirname(__file__), "caught_unamon.txt")
    if not os.path.exists(caught_file):
        with open(caught_file, "w") as f:
            f.write(json.dumps({}))
    with open(caught_file, "r") as f:
        caught_data = json.loads(f.read())

    # Remove the Unamon from the file
    caught_data[str(ctx.author.id)] = [unamon for unamon in caught_data[str(ctx.author.id)] if unamon["name"] != name.title()]
    with open(caught_file, "w") as f:
        f.write(json.dumps(caught_data))

    # Remove the Unamon from the training file if it is being trained
    training_unamon = get_training_unamon_by_user(ctx.author.id)
    if training_unamon is not None and training_unamon[1] == name.title():
        with open("unamon_training.txt", "r") as f:
            lines = f.readlines()
        with open("unamon_training.txt", "w") as f:
            for line in lines:
                if line.strip() != f"{ctx.author.id},{name.title()},{training_unamon[2]},{training_unamon[3]}":
                    f.write(line)

    # Send a message confirming the release
    embed = discord.Embed(description=f"You let {name.title()} be free!", color=discord.Color.green())
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

# If user tries to release an Unamon without providing a name
@release.error
async def release_error(ctx, error):
    # Check if the error is a missing parameter error
    if isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(description="Please provide a name for the Unamon you want to release.", color=discord.Color.red())
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
        return

# Rename the Unamon with the given name
@client.command()
async def rename(ctx, *, name: str):
    # Check if the user has the Unamon they want to rename
    unamon = get_unamon_by_name(ctx.author.id, name.title())
    if unamon is None:
        embed = discord.Embed(description=f"You don't have an Unamon with that name.", color=discord.Color.red())
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
        return

    # Ask the user for the new name
    embed = discord.Embed(description=f"What would you like to rename {name.title()} to?", color=discord.Color.blue())
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

    def check(message):
        return message.author == ctx.author and message.channel == ctx.channel

    try:
        message = await client.wait_for("message", timeout=60, check=check)
    except asyncio.TimeoutError:
        embed = discord.Embed(description=f"You didn't respond in time, {ctx.author.mention}!", color=discord.Color.red())
        await ctx.send(embed=embed)
        return

    # Update the Unamon's name in the caught_unamon.txt file
    with open("caught_unamon.txt", "r") as f:
        caught_unamon = json.load(f)
    for unamon in caught_unamon[str(ctx.author.id)]:
        if unamon["name"] == name.title():
            unamon["name"] = message.content.title()
            break
    with open("caught_unamon.txt", "w") as f:
        f.write(json.dumps(caught_unamon))

    # Send a message confirming the rename
    embed = discord.Embed(description=f"You have renamed {name.title()} to {message.content.title()}.", color=discord.Color.green())
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

# If user tries to rename an Unamon without providing a name
@rename.error
async def rename_error(ctx, error):
    # Check if the error is a missing parameter error
    if isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(description="Please provide a name for the Unamon you want to rename.", color=discord.Color.red())
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
        return

# Level up the training Unamon if the user sends a message
@client.event
async def on_message(message):
    await client.process_commands(message)

    # Check if the author of the message is training an Unamon
    training_unamon = get_training_unamon_by_user(message.author.id)
    if training_unamon is None:
        return

    # Update the Unamon's XP and level
    user_id, unamon_name, level, current_xp = training_unamon

    # Calculate the XP gained from the message
    xp = int(level ** 1.5 + random.randint(1, 5))

    # Calculate the required XP for the next level and update the Unamon's level and XP
    required_xp = int(5 * level ** 3 / 4)
    current_xp += xp

    if current_xp >= required_xp:
        level += 1
        current_xp = 0
        embed = discord.Embed(description=f"Congratulations! {message.author.mention}'s {unamon_name} has leveled up to level {level}!", color=discord.Color.green())
        await message.channel.send(embed=embed)
    update_training_unamon(user_id, unamon_name, level, current_xp)

    # Check if the Unamon has reached level 100 and stop training it if so
    if level == 100:
        embed = discord.Embed(description=f"{message.author.mention}'s {unamon_name} has reached level 100!", color=discord.Color.green())
        await message.channel.send(embed=embed)
        with open("unamon_training.txt", "r") as f:
            lines = f.readlines()
        with open("unamon_training.txt", "w") as f:
            f.writelines(line for line in lines if line.strip() != f"{user_id},{unamon_name},100,0")

# Allows user to add a picture for their Unamon and will show as a thumbnail in the embed
@client.command()
async def addpic(ctx, *, name: str):
    # Check if the user has the Unamon they want to add a picture to
    unamon = get_unamon_by_name(ctx.author.id, name.title())
    if unamon is None:
        embed = discord.Embed(description=f"You don't have an Unamon with that name.", color=discord.Color.red())
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
        return

    # Ask the user for the picture
    embed = discord.Embed(description=f"Please provide a picture for {name.title()}.", color=discord.Color.blue())
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

    def check(message):
        return message.author == ctx.author and message.channel == ctx.channel

    try:
        message = await client.wait_for("message", timeout=60, check=check)
    except asyncio.TimeoutError:
        embed = discord.Embed(description=f"You didn't respond in time, {ctx.author.mention}!", color=discord.Color.red())
        await ctx.send(embed=embed)
        return

    # Update the Unamon's picture in the caught_unamon.txt file
    with open("caught_unamon.txt", "r") as f:
        caught_unamon = json.load(f)
    for unamon in caught_unamon[str(ctx.author.id)]:
        if unamon["name"] == name.title():
            unamon["picture"] = message.content
            break
    with open("caught_unamon.txt", "w") as f:
        f.write(json.dumps(caught_unamon))
    
    # Send a message confirming the picture
    embed = discord.Embed(description=f"You have added a picture for {name.title()}.", color=discord.Color.green())
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

# If user tries to add a picture to an Unamon without providing a name
@addpic.error
async def addpic_error(ctx, error):
    # Check if the error is a missing parameter error
    if isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(description="Please provide a name for the Unamon you want to add a picture to.", color=discord.Color.red())
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
        return


# Help command that displays all commands
client.remove_command("help")
@client.command()
async def help(ctx):
    embed = discord.Embed(title="Help", description="Here are all the commands you can use:", color=discord.Color.blue())
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
    embed.add_field(name="Discovering", value="`.gen <word1> <word2>` - Generates an Unamon with the given words.\n`.gen` - Generates an Unamon with random words.", inline=False)
    embed.add_field(name="Examining", value="`.u` - Displays all your caught Unamon.\n`.u <name>` - Displays the details of the Unamon with the given name.\n", inline=False)
    embed.add_field(name="Studying", value="`.rename <name>` - Renames the Unamon with the given name.\n`.addpic <name>` - Adds a picture for the Unamon with the given name.", inline=False)
    embed.add_field(name="Training", value="`.train <name>` - Starts training the Unamon with the given name.\n`.xp` - Displays the progress of your training Unamon.", inline=False)
    embed.add_field(name="Releasing", value="`.release <name>` - Releases the Unamon with the given name.", inline=False)
    await ctx.send(embed=embed)


# If user tries to use an invalid command that is not a missing parameter error
@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        embed = discord.Embed(description=f"Invalid command. Type `.help` for a list of commands.", color=discord.Color.red())
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
        return
    raise error


# DEV COMMANDS ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# A command that allows devs adds custom Unamon with name, description, stats and picture
@client.command()
async def addunamon(ctx):
    # Load the caught Unamon file
    caught_file = os.path.join(os.path.dirname(__file__), "caught_unamon.txt")
    if not os.path.exists(caught_file):
        with open(caught_file, "w") as f:
            f.write(json.dumps({}))
    with open(caught_file, "r") as f:
        caught_data = json.loads(f.read())

    # First ask which user to add the Unamon to
    embed = discord.Embed(description=f"Please mention the user you want to add the Unamon to.", color=discord.Color.blue())
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

    def check(message):
        return message.author == ctx.author and message.channel == ctx.channel

    try:
        message = await client.wait_for("message", timeout=60, check=check)
    except asyncio.TimeoutError:
        embed = discord.Embed(description=f"You didn't respond in time, {ctx.author.mention}!", color=discord.Color.red())
        await ctx.send(embed=embed)
        return
    user = message.mentions[0]

    # Ask for name, description, stats and picture
    embed = discord.Embed(description=f"Please provide a name for the Unamon.", color=discord.Color.blue())
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)


    def check(message):
        return message.author == ctx.author and message.channel == ctx.channel

    try:
        message = await client.wait_for("message", timeout=6000, check=check)
    except asyncio.TimeoutError:
        embed = discord.Embed(description=f"You didn't respond in time, {ctx.author.mention}!", color=discord.Color.red())
        await ctx.send(embed=embed)
        return
    name = message.content

    embed = discord.Embed(description=f"Please provide a description for the Unamon.", color=discord.Color.blue())
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

    try:
        message = await client.wait_for("message", timeout=6000, check=check)
    except asyncio.TimeoutError:
        embed = discord.Embed(description=f"You didn't respond in time, {ctx.author.mention}!", color=discord.Color.red())
        await ctx.send(embed=embed)
        return
    description = message.content
    
    embed = discord.Embed(description=f"Please provide stats for the Unamon.", color=discord.Color.blue())
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

    try:
        message = await client.wait_for("message", timeout=6000, check=check)
    except asyncio.TimeoutError:
        embed = discord.Embed(description=f"You didn't respond in time, {ctx.author.mention}!", color=discord.Color.red())
        await ctx.send(embed=embed)
        return
    stats = message.content

    embed = discord.Embed(description=f"Please provide a picture for the Unamon.", color=discord.Color.blue())
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

    try:
        message = await client.wait_for("message", timeout=6000, check=check)
    except asyncio.TimeoutError:
        embed = discord.Embed(description=f"You didn't respond in time, {ctx.author.mention}!", color=discord.Color.red())
        await ctx.send(embed=embed)
        return
    picture = message.content

    # Add the Unamon to the file assigning it to the user
    caught_data.setdefault(str(user.id), [])
    caught_data[str(user.id)].append({
        "name": name.title(),
        "description": description,
        "stats": stats,
        "picture": picture
    })
    with open(caught_file, "w") as f:
        f.write(json.dumps(caught_data))

    # Send a congratulatory message
    embed = discord.Embed(title=f"Congratulations, {ctx.author.name}!", description=f"You added **{name.title()}**!", color=discord.Color.green())
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

client.run(TOKEN)