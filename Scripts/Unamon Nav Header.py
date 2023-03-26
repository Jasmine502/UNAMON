import pyperclip

unamon_list = ["Smoglet","Flamura","Ignantom","Flopix","Aquilia","Marinawk","Cracklesap","Salamendro","Wyvorophyll","Cryoul","Cryophant","Savitaur","Marijuadon","Shocksteed","Ryno","Spookspew","Ectoxomoth","Myrkkane","Corvapse","Neurocowl","Hypothalaven","Venion","Ampixie","Faerumen","Spelux","Ferrizari","Neuraphin","Nauticorp","Orgamarina","Orgamarino","Chrysogor","Tephron","Terroforma","Afterwrithe","Pharoant","Sekhant","Dhascarab","Roddig","Burrowatt","Excavolt","Grifling","Gryfleia","Gryfnosa","Moxra","Mosantis","Exvil","Stad","Stuana","Stainana","Wyfern","Folyvern","Grumbo","Landignor","Titanger","Magmoroch","Vesophry"]

def get_udex_number(unamon):
    return str(unamon_list.index(unamon) + 1).zfill(2)

def get_prev_unamon(unamon):
    udex_number = unamon_list.index(unamon)
    if udex_number == 0:
        return None
    return unamon_list[udex_number - 1]

def get_next_unamon(unamon):
    udex_number = unamon_list.index(unamon)
    if udex_number == len(unamon_list) - 1:
        return None
    return unamon_list[udex_number + 1]

def generate_code_format(unamon):
    udex_number = get_udex_number(unamon)
    prev_unamon = get_prev_unamon(unamon)
    next_unamon = get_next_unamon(unamon)

    code_format = '<center>\n'
    code_format += '{| class="fandom-table"\n'

    if prev_unamon:
        prev_udex_number = get_udex_number(prev_unamon)
        code_format += f'![[{prev_unamon}|←]]\n'
        code_format += '!\n'
        code_format += f'![[{prev_unamon}|#{prev_udex_number}: {prev_unamon}]]\n'
    else:
        code_format += '!\n'
        code_format += '!\n'
        code_format += '!\n'

    code_format += f'![[Unamon]]\n'

    if next_unamon:
        next_udex_number = get_udex_number(next_unamon)
        code_format += f'![[{next_unamon}|#{next_udex_number}: {next_unamon}]]\n'
        code_format += '!\n'
        code_format += f'![[{next_unamon}|→]]\n'
    else:
        code_format += '!\n'
        code_format += '!\n'
        code_format += '!\n'

    code_format += '|}</center>'
    return code_format

while True:
    unamon = input("Enter an Unamon: ").title()
    if unamon == "":
        break
    if unamon not in unamon_list:
        print("Unamon not found.")
        continue
    code_format = generate_code_format(unamon)
    print(code_format)
    pyperclip.copy(code_format)
    print()