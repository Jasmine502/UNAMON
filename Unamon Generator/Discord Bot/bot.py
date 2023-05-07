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

# Function to get Fakemon name and description from Poe API
def get_fakemon_info(client, words):
    # Construct message for Poe API
    message = f"Come up with a unique Fakemon, along with its typing(s) and a detailed design, that combines the concepts of '{words[0]}' and '{words[1]}'. Please make sure that the name of the Fakemon MUST be the very first word of the text"
    
    # Send message to Poe API
    response = ""
    for chunk in client.send_message("chinchilla", message):
        response += chunk["text_new"]
    
    # Remove any non-alphabetic characters from Fakemon name
    fakemon_name = re.sub(r"[^a-zA-Z]", "", response.split()[0])
    fakemon_desc = response.strip()

    return fakemon_name, fakemon_desc

def generate_stats(client, fakemon_name):
    # Prompt for Fakemon stats
    prompt = f"Come up with the appropriate following stats/info for {fakemon_name}:\n" \
             "Signature Move (with a short description), it's PP, Attack DMG, Accuracy %, the move's type, the effectiveness percentage, and the level it's learned\n" \
             "The Category of the Fakemon\n" \
             "It's height and weight in imperial units\n" \
             "It's stats (HP, ATK, DEF, SpA, SpD and Speed).\n" \
             "Evolves from/into (if any)\n" \
             "An interesting, unique and creative PokéDex entry.\n" \
             "3 existing abilities that it can learn (with a short description of what it does), last of them being a Hidden Ability"
    
    # Send prompt to Poe API and get response
    response = ""
    for chunk in client.send_message("chinchilla", prompt):
        response += chunk["text_new"]
    
    return response


def get_fakemon_by_name(user_id, name):
    with open("caught_fakemon.txt", "r") as f:
        caught_fakemon = json.load(f)
    if str(user_id) not in caught_fakemon:
        return None
    for fakemon in caught_fakemon[str(user_id)]:
        if fakemon["name"] == name:
            return fakemon
    return None


def get_training_fakemon_by_user(user_id):
    with open("fakemon_training.txt", "r") as f:
        lines = f.readlines()
        for line in lines:
            parts = line.strip().split(",")
            if parts[0] == str(user_id):
                return (int(parts[0]), parts[1], int(parts[2]), int(parts[3]))
    return None


def update_training_fakemon(user_id, fakemon_name, level, current_xp):
    new_lines = []
    with open("fakemon_training.txt", "r") as f:
        for line in f:
            line_parts = line.strip().split(",")
            if line_parts[0] == str(user_id) and line_parts[1] == fakemon_name:
                new_lines.append(f"{user_id},{fakemon_name},{level},{current_xp}")
            else:
                new_lines.append(line.strip())

    with open("fakemon_training.txt", "w") as f:
        f.write("\n".join(new_lines))

@client.event
async def on_ready():
    print('Bot is readyyyyyy')


@client.command()
async def gen(ctx, *words):
    # Map user IDs to Poe API tokens
    users = {
        "294589366599417856": "BcZb2oEDNIXTLIzazQjuHA%3D%3D",  # JAY
        "386145081092079623": "sRNsvgWw5SOdyuDB2wSaMg%3D%3D",  # AM
    }
    user_id = str(ctx.author.id)
    pToken = users.get(user_id)

    # If user is not recognised
    if not pToken:
        await ctx.send("I don't know you.")
        return

    # Submit token and clear context
    pClient = poe.Client(pToken)
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
                embed = discord.Embed(description=f"Cancelled Fakemon generation.", color=discord.Color.red())
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
        embed = discord.Embed(description=f"Please provide either 2 words, or no words to generate a Fakemon.", color=discord.Color.red())
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
        return

 # Generate Fakemon description with Poe
    embed = discord.Embed(description=f"Generating Fakemon...", color=discord.Color.blue())
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
    msg = await ctx.send(embed=embed)
    try:
        fakemon_name, fakemon_desc = get_fakemon_info(pClient, words)
    except Exception as e:
        await ctx.send(f"Error: {str(e)}")
        return
    color = discord.Color.random()
    embed = discord.Embed(title=f"{fakemon_name.upper()}", description=fakemon_desc, color=color)
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
    await msg.edit(embed=embed)
    await asyncio.sleep(1)

    # Ask if user wants to generate stats from the above description
    embed = discord.Embed(description=f"Generate stats for **{fakemon_name}**?", color=discord.Color.blue())
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
        embed = discord.Embed(description=f"Generating stats for **{fakemon_name}**...", color=discord.Color.blue())
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        msg = await ctx.send(embed=embed)
        fakemon_stats = generate_stats(pClient, fakemon_name)
        embed = discord.Embed(title=f"{fakemon_name.upper()} STATS", description=fakemon_stats, color=color)
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
            embed = discord.Embed(description=f"You didn't catch the {fakemon_name} in time, {ctx.author.mention}!", color=discord.Color.red())
            await ctx.send(embed=embed)
        else:
            # Load the caught fakemon file
            caught_file = os.path.join(os.path.dirname(__file__), "caught_fakemon.txt")
            if not os.path.exists(caught_file):
                with open(caught_file, "w") as f:
                    f.write(json.dumps({}))
            with open(caught_file, "r") as f:
                caught_data = json.loads(f.read())

            # Add the caught fakemon to the file
            caught_data.setdefault(str(ctx.author.id), [])
            caught_data[str(ctx.author.id)].append({
                "name": fakemon_name,
                "description": fakemon_desc,
                "stats": fakemon_stats,
            })
            with open(caught_file, "w") as f:
                f.write(json.dumps(caught_data))

            # Send a congratulatory message
            embed = discord.Embed(title=f"Congratulations, {ctx.author.name}!", description=f"You caught **{fakemon_name}**!", color=discord.Color.green())
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)
    elif reaction.emoji == "👎":
        embed = discord.Embed(description=f"No stats generated.", color=discord.Color.blue())
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

@client.command()
async def u(ctx, *, arg=None):
    user_id = str(ctx.author.id)
    
    with open('caught_fakemon.txt', 'r') as f:
        caught_fakemon = json.load(f)
    
    if user_id not in caught_fakemon:
        embed = discord.Embed(title="Oops!", description="You haven't caught any Fakemon yet!", color=discord.Color.red())
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
        return
    
    fakemon_list = caught_fakemon[user_id]
    
    if arg is None:
        if not fakemon_list:
            embed = discord.Embed(title="Oops!", description="You haven't caught any Fakemon yet!", color=discord.Color.red())
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)
            return
        
        fakemon_names = [fakemon["name"] for fakemon in fakemon_list]
        embed = discord.Embed(title=f"{ctx.author.name}'s Caught Fakemon", description="\n".join(fakemon_names), color=discord.Color.blue())
    else:
        fakemon = next((f for f in fakemon_list if f["name"].lower() == arg.lower()), None)
        
        if fakemon is None:
            embed = discord.Embed(title="Oops!", description=f"You haven't caught a Fakemon named {arg} yet!", color=discord.Color.red())
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)
            return
        
        color = discord.Color.random()
        embed1 = discord.Embed(title=f"{fakemon['name']}'s Description", description=fakemon["description"], color=color)
        embed1.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        embed2 = discord.Embed(title=f"{fakemon['name']}'s Stats", description=fakemon["stats"], color=color)
        embed2.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
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
    fakemon = get_fakemon_by_name(ctx.author.id, name.title())
    if fakemon is None:
        embed = discord.Embed(description="You don't have a Fakemon with that name.", color=discord.Color.red())
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
        return

    training_fakemon = get_training_fakemon_by_user(ctx.author.id)
    if training_fakemon is not None:
        embed = discord.Embed(description=f"You are already training {training_fakemon[1]}!", color=discord.Color.orange())
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
        return

    embed = discord.Embed(description=f"You are now training {fakemon['name']}!", color=discord.Color.green())
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

    # Add the Fakemon to the fakemon_training.txt file with level 1
    with open("fakemon_training.txt", "a") as f:
        f.write(f"{ctx.author.id},{fakemon['name']},1,0\n")


@client.event
async def on_message(message):
    await client.process_commands(message)

    # Check if the author of the message is training a Fakemon
    training_fakemon = get_training_fakemon_by_user(message.author.id)
    if training_fakemon is None:
        return

    # Calculate the XP gained from the message
    xp = random.randint(1, 3)

    # Update the Fakemon's XP and level
    user_id, fakemon_name, level, current_xp = training_fakemon
    required_xp = 10 * level ** 2
    current_xp += xp
    if current_xp >= required_xp:
        level += 1
        current_xp = 0
        embed = discord.Embed(description=f"Congratulations! {message.author.mention}'s {fakemon_name} has leveled up to level {level}!", color=discord.Color.green())
        await message.channel.send(embed=embed)
    update_training_fakemon(user_id, fakemon_name, level, current_xp)


client.run(TOKEN)