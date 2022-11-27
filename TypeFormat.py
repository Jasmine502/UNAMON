import pyperclip

# List of Pokémon types
types = ['Normal', 'Fire', 'Water', 'Electric', 'Grass', 'Ice', 'Fighting', 'Poison', 'Ground', 'Flying', 'Psychic', 'Bug', 'Rock', 'Ghost', 'Dragon', 'Dark', 'Steel', 'Fairy']

# Detect when something is copied to the clipboard
while True:
    if pyperclip.paste() in types:
        # If it is a string that is any of the Pokémon types, run the following program
        type = pyperclip.paste()
        # Create a "Format" string variable, which goes "[[File:" + whatever the type was in all caps + " SYMBOL.png|30px]]<br>[[" + the type in title case + "]]"
        format = "[[File:" + type.upper() + " SYMBOL.png|30px]]<br>[[" + type.title() + "]]"
        # Paste the Format string variable
        pyperclip.copy(format)
        