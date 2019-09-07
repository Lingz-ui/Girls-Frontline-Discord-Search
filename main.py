import discord
import json
#Error handler
import traceback
#To insert ability parameters for dolls
import re
import os
#For random flavor texts if quotes are present.
import random
#Time is needed for gfstatus time sort.
import time
#Return closest result for dolls. (Thank god because nobody ever spells anything correctly with this bot)
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

client = discord.Client()
#Your discord bot token. For your safety this is an environment variable, but you're free to put your token here if you really want to.
DISCORD_TOKEN=os.environ['GFBOT_TOKEN']
#The prefix for the bot commands. Default is $gf
COMMAND_PREFIX="$gf"
#COMMAND_NAME="$gfsearch"
#The domain for the images extracted from Girls' Frontline. The bot will combine it like PIC_DOMAIN + "pic_ump45.png"
#This is my server, in case you didn't already realize that.
PIC_DOMAIN="http://103.28.71.152:999/pic/"
#The domain for the equipment images extracted from Girls' Frontline. The bot will combine it like PIC_EQUIP_DOMAIN + "pic_ump45.png"
PIC_EQUIP_DOMAIN="http://103.28.71.152:999/pic/equip/"
#The domain for the icons for dolls like the ones that are on the top left of the doll cards.
#Icons are disabled because they make embeds worse.
#ICON_DOMAIN="http://103.28.71.152:999/pic_compressed/icons/"
#The domain for the Girls' Frontline wiki (urls are kept in girlsfrontline.json)
SITE_DOMAIN = "https://en.gfwiki.com"
#pls don't touch.
gfcolors = [0, 0, 0xffffff, 0x6bdfce, 0xd6e35a, 0xffb600, 0xdfb6ff]
version = "IOP 2.49-20190810"
def num2stars(n):
	#★☆
	st = ""
	if n > 5:
		return "⚝"
	for i in range(5):
		if i < n:
			st = st + "★"
		else:
			st = st + "☆"
	return st

def RepresentsInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False

#@client.event
#async def loaddex(message):
#	reload()
#	await client.send_message(message.channel, "Done.")
def serverCount():
	#Create a variable to store amount of members per server
	numMembers = 0
	#Loop through the servers, get all members and add them up
	for s in client.servers:
	    numMembers += len(s.members)
	print("Serving " + str(len(client.servers)) +" bases and "+str(numMembers)+ " commanders")
	return "Serving " + str(len(client.servers)) +" bases and "+str(numMembers)+ " commanders"

@client.event
async def on_ready():
	print("The bot is ready!")
	#print(str(client.user.id))
	#https://discordapp.com/oauth2/authorize?client_id=351447700064960522&scope=bot&permissions=0
	print("Add me with https://discordapp.com/oauth2/authorize?client_id="+client.user.id+ "&scope=bot&permissions=0")
	await client.change_presence(game=discord.Game(name=serverCount()))

@client.event
async def on_server_join(server):
	await client.change_presence(game=discord.Game(name=serverCount()))

@client.event
async def on_server_remove(server):
	await client.change_presence(game=discord.Game(name=serverCount()))


def getQuote(internalName, quoteType):
	if quotedex:
		if internalName in quotedex:
			if quoteType in quotedex[internalName]:
				return " ".join(quotedex[internalName][quoteType])
	return False
	
def getAbility(doll, tag):
	abilityText = doll[tag]['text']
	while True:
		searchObj = re.search("\(\$([^\)]+)\)", abilityText)
		if searchObj:
			key = searchObj.group()[2:-1]
			print("key: " + key)
			val = doll[tag][key][-1]
			abilityText = abilityText.replace(searchObj.group(), val)
		else:
			break
	if 'cooldown' in doll[tag]:
		abilityText += "\n**Cooldown:** " + str(doll[tag]['cooldown'][-1]) + " seconds"
	if 'initial' in doll[tag]:
		abilityText += ", "+str(doll[tag]['initial']) + " seconds initial cooldown"
	return abilityText
	
#There was honestly no need to make this a function
#if statements for all the things!!!!!!
def dollInfo(doll):
	embed = discord.Embed(title="No."+(str(doll["num"]) if doll['num'] > 1 else "?")+" - "+ doll['name'] + " " + num2stars(doll['rating']), url=SITE_DOMAIN+doll['url'], color=gfcolors[doll['rating']])
	embed.add_field(name="Type", value=doll['type'], inline=True)
	#{ "hp" : 40, "ammo": 10, "ration": 10, "dmg": 12, "acc": 6, "eva": 9, "rof": 31, "spd": 15, "armor": 0, "crit_rate": 20, "crit_dmg": 50, "pen": 10},
	#embed.add_field(name="Base Stats", value="**HP:** "+str(doll['baseStats']['hp']) + ", **DMG:** " + str(doll['baseStats']['dmg']) + ", **ACC:** " + str(doll['baseStats']['acc']) + ", **EVA:** " + str(doll['baseStats']['eva']) + ", **ROF:** " + str(doll['baseStats']['rof']))
	if 'constStats' in doll:
		stats = "**Movement:** "+str(doll['constStats']['mov']) + "**, Crit. rate:** " + str(doll['constStats']['crit_rate'])+"%, **Crit DMG:** "+str(doll['constStats']['crit_dmg']) + ", **Armor Pen.:** " + str(doll['constStats']['pen'])
		stats += "\n**HP:** "+str(doll['maxStats']['hp']) + ", **DMG:** " + str(doll['maxStats']['dmg']) + ", **ACC:** " + str(doll['maxStats']['acc']) + ", **EVA:** " + str(doll['maxStats']['eva']) + ", **ROF:** " + str(doll['maxStats']['rof']) + ", **Armor:** "+ str(doll['maxStats']['armor'])
		embed.add_field(name="Max Stats",value=stats)
	obtain_info = ""
	if 'stage' in doll['production']:
		obtain_info += '**STAGE:** ' + doll['production']['stage'] + "\n"
	if 'reward' in doll['production']:
		obtain_info += '**REWARD:** ' + doll['production']['reward'] + "\n"
	if 'timer' in doll['production']:
		obtain_info += '**Production Timer:** ' + doll['production']['timer']
	if 'upgrade' in doll['production']:
		obtain_info += "**UPGRADE:** "+doll['production']['upgrade']
	if doll['name'] in bonusdex and 'drop_rate' in bonusdex[doll['name']]:
		obtain_info += "\n**Normal Prod. Drop Rate:** " + str(bonusdex[doll['name']]['drop_rate'])+"% (Estimated)"
	embed.add_field(name="How To Obtain", value=obtain_info,inline=False)

	if 'normal' in doll['production']:
		a = doll['production']['normal']
		f = "**Manpower:** "+str(a[0]) + " **Ammo:** " + str(a[1]) + " **Rations:** " + str(a[2]) + " **Parts:** " + str(a[3])
		if doll['name'] in bonusdex and 'voodoo' in bonusdex[doll['name']]:
			a = bonusdex[doll['name']]['voodoo']
			f += "\nVoodoo: " + "**Manpower:** "+str(a[0]) + " **Ammo:** " + str(a[1]) + " **Rations:** " + str(a[2]) + " **Parts:** " + str(a[3])
			f += "\n*Voodoo recipes are placebo & may not increase drop rate*"
	
		embed.add_field(name="Normal Production Requirement", value=f, inline=True)
	#Yes I know it's horrible
	elif 'minResource' in doll['production']:
		f = "**Total resources used must be >=** " + str(doll['production']['minResource'])
		if doll['name'] in bonusdex and 'voodoo' in bonusdex[doll['name']]:
			a = bonusdex[doll['name']]['voodoo']
			f += "\nVoodoo: " + "**Manpower:** "+str(a[0]) + " **Ammo:** " + str(a[1]) + " **Rations:** " + str(a[2]) + " **Parts:** " + str(a[3])
			f += "\n*Voodoo recipes are placebo & may not increase drop rate*"

		embed.add_field(name="Normal Production Requirement", value=f, inline=True)


	if 'heavy' in doll['production']:
		a = doll['production']['heavy']
		f = "**Manpower:** "+str(a[0]) + " **Ammo:** " + str(a[1]) + " **Rations:** " + str(a[2]) + " **Parts:** " + str(a[3])
		embed.add_field(name="Heavy Production Requirement", value=f, inline=True)
	#Not all dolls have abilities yet since some are unreleased.
	if 'ability' in doll:
		embed.add_field(name="Skill: "+doll['ability']['name'], value=getAbility(doll,'ability'), inline=False)
	if 'ability2' in doll:
		embed.add_field(name="2nd Skill: "+doll['ability2']['name'], value=getAbility(doll,'ability2'), inline=False)

	if 'tile_bonus' in doll:
		embed.add_field(name="Tile Buff ", value=doll['tile_bonus'], inline=True)
		embed.add_field(name="Tile Buff Ability", value=doll['bonus_desc'], inline=True)
	#embed.add_field(name="Tile Bonus Types", value=doll['bonus_type'], inline=True)
	if doll['name'] in bonusdex and 'flavor' in bonusdex[doll['name']]:
		embed.set_footer(text=bonusdex[doll['name']]['flavor'])
	else:
		quote = False
		if 'internalName' in doll:
			if getQuote(doll['internalName'],"gain") != "":
				quote = getQuote(doll['internalName'], random.choice(["dialogue1","dialogue2","dialogue3","gain"]))
			else:
				quote = getQuote(doll['internalName'], random.choice(["dialogue1","dialogue2","dialogue3"]))
		if quote != False:
			embed.set_footer(text=quote)
		else:
			embed.set_footer(text="Data is Ⓒ en.gfwiki.com and licenced under CC BY-SA 3.0.")

	if 'img' in doll:
		embed.set_image(url=PIC_DOMAIN+doll['img'])
		print(PIC_DOMAIN+doll['img'])
	#print(embed)
	#icons
	#These are disabled because it makes the embed WORSE, not better. There's reduced space for text on mobile.
	#if doll['rating'] > 5:
	#	embed.set_thumbnail(url=ICON_DOMAIN+"Icon_"+doll['type']+"_EXTRAstar.png")
	#else:
	#	embed.set_thumbnail(url=ICON_DOMAIN+"Icon_"+doll['type']+"_"+str(doll['rating'])+"star.png")
	#only for sangvis since they don't have a lot of text
	if doll['type'] == "Sangvis Ferri Doll":
		embed.set_thumbnail(url=PIC_DOMAIN+"Icon_Sangvis_Ferri.png")
	return embed
	

def equipInfo(equip):
	embed = discord.Embed(title=equip['name'] + " " + num2stars(equip['rating']), url=SITE_DOMAIN+equip['url'], color=gfcolors[equip['rating']])
	#Type is worthless, show valid for instead
	if 'valid' in equip:
		embed.add_field(name="Usable by", value=equip['valid'], inline=True)
	#embed.add_field(name="Type", value=equip['type'], inline=True)
	#{ "hp" : 40, "ammo": 10, "ration": 10, "dmg": 12, "acc": 6, "eva": 9, "rof": 31, "spd": 15, "armor": 0, "crit_rate": 20, "crit_dmg": 50, "pen": 10},
	#embed.add_field(name="Base Stats", value="**HP:** "+str(equip['baseStats']['hp']) + ", **DMG:** " + str(equip['baseStats']['dmg']) + ", **ACC:** " + str(equip['baseStats']['acc']) + ", **EVA:** " + str(equip['baseStats']['eva']) + ", **ROF:** " + str(equip['baseStats']['rof']))
	if 'constStats' in equip:
		stats = "**Movement:** "+str(equip['constStats']['mov']) + "**, Crit. rate:** " + str(equip['constStats']['crit_rate'])+"%, **Crit DMG:** "+str(equip['constStats']['crit_dmg']) + ", **Armor Pen.:** " + str(equip['constStats']['pen'])
		stats += "\n**HP:** "+str(equip['maxStats']['hp']) + ", **DMG:** " + str(equip['maxStats']['dmg']) + ", **ACC:** " + str(equip['maxStats']['acc']) + ", **EVA:** " + str(equip['maxStats']['eva']) + ", **ROF:** " + str(equip['maxStats']['rof']) + ", **Armor:** "+ str(equip['maxStats']['armor'])
		embed.add_field(name="Max Stats",value=stats)
		
	#Because the wiki doesn't list it in a clean way and I don't have everything noted down yet
	if 'production' in equip:
		obtain_info = ""
		if 'stage' in equip['production']:
			obtain_info += '**STAGE:** ' + equip['production']['stage'] + "\n"
		if 'reward' in equip['production']:
			obtain_info += '**REWARD:** ' + equip['production']['reward'] + "\n"
		if 'timer' in equip['production']:
			obtain_info += '**Production Timer:** ' + equip['production']['timer']
		if 'upgrade' in equip['production']:
			obtain_info += "**UPGRADE:** "+equip['production']['upgrade']
		#if equip['name'] in bonusdex and 'drop_rate' in bonusdex[equip['name']]:
		#	obtain_info += "\n**Normal Prod. Drop Rate:** " + str(bonusdex[equip['name']]['drop_rate'])+"% (Estimated)"
		embed.add_field(name="How To Obtain", value=obtain_info,inline=False)

		if 'normal' in equip['production']:
			a = equip['production']['normal']
			f = "**Manpower:** "+str(a[0]) + " **Ammo:** " + str(a[1]) + " **Rations:** " + str(a[2]) + " **Parts:** " + str(a[3])
			f += "\n*Official recipe for recommended production. Not a minimum requirement.*"
			if equip['name'] in bonusdex and 'voodoo' in bonusdex[equip['name']]:
				a = bonusdex[equip['name']]['voodoo']
				f += "\nVoodoo: " + "**Manpower:** "+str(a[0]) + " **Ammo:** " + str(a[1]) + " **Rations:** " + str(a[2]) + " **Parts:** " + str(a[3])
				f += "\n*Voodoo recipes are placebo & may not increase drop rate*"
		
			embed.add_field(name="Normal Production Recipe", value=f, inline=True)

		if 'heavy' in equip['production']:
			a = equip['production']['heavy']
			f = "**Manpower:** "+str(a[0]) + " **Ammo:** " + str(a[1]) + " **Rations:** " + str(a[2]) + " **Parts:** " + str(a[3])
			embed.add_field(name="Heavy Production Requirement", value=f, inline=True)
		
	#Faries have skills too!
	if 'ability' in equip:
		embed.add_field(name="Skill: "+equip['ability']['name'], value=getAbility(equip,'ability'), inline=False)
	#Future proofing... I guess
	if 'ability2' in equip:
		embed.add_field(name="2nd Skill: "+equip['ability2']['name'], value=getAbility(equip,'ability2'), inline=False)


	if 'description' in equip:
		embed.add_field(name="Description", value=equip['description'], inline=False)
	
	#if equip['name'] in bonusdex and 'flavor' in bonusdex[equip['name']]:
	#	embed.set_footer(text=bonusdex[equip['name']]['flavor'])
	if 'img' in equip:
		embed.set_image(url=PIC_EQUIP_DOMAIN+equip['img'])
		print(PIC_DOMAIN+equip['img'])
	return embed

def getSearchResult(param, search_equip=False):
	if search_equip == True:
		res = process.extract(param, [equip['name'] for equip in equipmentdex], limit=3)
		for equip in equipmentdex:
			if res[0][0] == equip['name']:
				return equip, res
	else:
		res = process.extract(param, [doll['name'] for doll in frontlinedex], limit=3)
		for doll in frontlinedex:
			if res[0][0] == doll['name']:
				return doll, res
	raise Exception("This shouldn't be possible! No result found in search.")


#This REALLY should not be a function
def getPossibleCostumes(doll):
	msg = "Costumes for "+doll['name']+": "
	for i in range(len(doll['costumes'])):
		msg+=chr(i+65)+". **"+doll['costumes'][i]['name']+"**, "
	msg+="\nYou can choose a costume by letter, name, or hitting the corresponding react button below. Ex. `"+doll['name']+", 1` or `"+doll['name']+", "+doll['costumes'][1]['name']+"`"
	return msg

def getDollCostume(doll,costumeType):
	if 'costumes' in doll:
		if costumeType:
			if costumeType == "--list":
				return ""
			#	raise Exception("--list should not be used in getDollCostume anymore.")
			#	return getPossibleCostumes(doll)
			if len(costumeType) == 1:
				print(costumeType)
				i = ord(costumeType.upper())-65
				if i < len(doll['costumes']) and i >= 0:
					return doll['name'] + ": "+doll['costumes'][i]['name']+"\n"+PIC_DOMAIN+doll['costumes'][i]['pic']
				else:
					print("chr was too high or too low. "+str(i)+" "+costumeType)
					return "Parameter is more than the number of costumes in this T-Doll."
			else:
				for costume in doll['costumes']:
					if costume['name'].lower() == costumeType.lower():
						return doll['name'] + ": "+costume['name']+"\n"+PIC_DOMAIN+costume['pic']
			print(costumeType + " not found in "+doll['name'])
			#return "Couldn't find that costume. "+getPossibleCostumes(doll)
			return False
		#else
		return doll['name'] + ":\n"+PIC_DOMAIN+doll['img']
	#else
	return "Sorry, either there are no images for this doll or the data is missing."
	#return False

#Behold, a stateless function, by parsing my own messages
#Spaghetti code is subjective, ok?
@client.event
async def on_reaction_add(reaction,user):
	if user == client.user:
		return
	#If the message that the reaction was added to is not a message this bot sent, return.
	if reaction.message.author != client.user:
		return
	msg = reaction.message.content.splitlines()
	
	#Don't do anything if this reaction is a custom emoji.
	if reaction.custom_emoji:
		return
	
	#lame hack to check if it's a --list result
	if msg[0].startswith("Costumes for"):
		#print(msg[0].split(":")[0])
		name = msg[0].split(":")[0][(len("Costumes for")+1):]
		print(name)
		#Check if it's a letter emoji
		print("Reacted with "+ reaction.emoji + " "+str(ord(reaction.emoji)))
		if ord(reaction.emoji) < 127462 or ord(reaction.emoji) > 127481:
			return
		#unicode reactions start at 127462, so convert them to regular letters (starts at 65)
		letter = chr(ord(reaction.emoji)-127397)
		print("Converted to "+letter)
		for doll in frontlinedex:
			if name == doll['name']:
				msg = await client.edit_message(reaction.message,new_content=getDollCostume(doll,letter))
				try:
					await client.clear_reactions(reaction.message)
				except:
					print("Missing manage messages permissions...")
					#await client.edit_message(msg,new_content=msg.content+"\n(I'm missing manage message permissions, so I can't clear your reactions.)")
	#Lame hack to check if this is a $gfimage command result
	elif msg[-1].endswith(".png"):
		if reaction.emoji == "🔥":
			name,costume = msg[0].split(":")
			
			#If already damage art
			if "(" in costume:
				#costume = costume.split("(")[0].strip()
				return
			elif costume.strip() == "":
				costume = "Default (Damaged)"
			else:
				costume = costume.strip() + " (Damaged)"
				
			for doll in frontlinedex:
				if name == doll['name']:
					await client.edit_message(reaction.message,new_content=getDollCostume(doll,costume))
		#Insert else statements here for left and right arrows
	return
	
#Behold, the above but it's the opposite
@client.event
async def on_reaction_remove(reaction,user):
	if user == client.user:
		return
	if reaction.message.author != client.user:
		return
	msg = reaction.message.content.splitlines()
	if msg[-1].endswith(".png"):
		if reaction.emoji == "🔥":
			name,costume = msg[0].split(":")
			if "(" in costume:
				costume = costume.split("(")[0].strip()
			else:
				return
			for doll in frontlinedex:
				if name == doll['name']:
					await client.edit_message(reaction.message,new_content=getDollCostume(doll,costume))
	return
	
@client.event
async def on_message(message):
	if message.author == client.user:
		return
	if message.content.startswith(COMMAND_PREFIX+"status"):
		param = message.content[(len(COMMAND_PREFIX+"status")+1):].lower()
		st = "Running "+version+"\n"
		st += serverCount()
		st += "\n"+str(len(frontlinedex))+" dolls indexed (incl. MOD variants & 1 kalina)"
		st += "\n"+str(len(equipmentdex))+" equipments indexed."
		#require --extra because this command is expensive to compute and I don't want people spamming it. It also doesn't work yet.
		if param == "--extra":
			time_list = []
			for doll in frontlinedex:
				if 'production' in doll and 'timer' in doll['production']:
					#Tuples
					time_list.append((doll['name'],doll['production']['timer']))
			#it's broken
			sorted((time.strptime(d[1], "%H:%M:%S") for d in time_list), reverse=False)
			print(time_list)
			st += "\nThe T-Doll with the shortest production time is "+time_list[0][0] + " with a timer of "+time_list[0][1]+"."
			st += "\nThe T-Doll with the longest production time is "+time_list[-1][0] + " with a timer of "+time_list[-1][1]+"."
		await client.send_message(message.channel, st)
		#print("Attempting to change the status to " + st)
		#await client.change_presence(game=discord.Game(name="testing"))
		#print("done")
	elif message.content.startswith(COMMAND_PREFIX+"search "):
		#The string "$gfsearch2 " is 11 characters, so cut it off
		param = message.content[(len(COMMAND_PREFIX+"search")+1):].lower()
		print(param)
		#if param.startswith("--"):
		#	temp = param.split(" ")
		#	flag = 
		#	param = param[
		#await client.send_message(message.channel, "World")
		for doll in frontlinedex:
			if param == doll['name'].lower():
				embed = dollInfo(doll)
				try:
					await client.send_message(message.channel, embed=embed)
				except Exception as e:
					await client.send_message(message.channel, content="An error occured and I am unable to complete your request.")
					print("An error occured. Here is the affected doll:")
					print(doll)
					print(e)
				return
			elif 'alias' in doll and param == doll['alias'].lower():
				print(param+" -> "+doll['name'])
				embed = dollInfo(doll)
				await client.send_message(message.channel, embed=embed)
				return
		doll, res = getSearchResult(param)
		embed = dollInfo(doll)
		await client.send_message(message.channel, content="No T-Doll was found with that exact name, so I'm returning the closest result. Did you mean: "+", ".join([i[0] for i in res]), embed=embed)
		return
		#else:
		#	print("WARN: No T-Doll was found for " + param)
		#	await client.send_message(message.channel, "No T-Doll was found with that name.")
		#return
	elif message.content.startswith(COMMAND_PREFIX+"equip "):
		#The string "$gfsearch2 " is 11 characters, so cut it off
		param = message.content[(len(COMMAND_PREFIX+"equip")+1):].lower()
		print(param)
		equip, res = getSearchResult(param,True)
		embed = equipInfo(equip)
		if res[0][1] == 100:
			await client.send_message(message.channel, embed=embed)
		else:
			await client.send_message(message.channel, content="No equipment was found with that exact name, so I'm returning the closest result. Did you mean: "+", ".join([i[0] for i in res]), embed=embed)
		return
	elif message.content.startswith(COMMAND_PREFIX+"image "):
		param = message.content[(len(COMMAND_PREFIX+"image")+1):].lower().split(",")
		costumeType = False
		if len(param) > 1:
			costumeType = param[-1].strip()
		param = param[0]
		#As dumb as it is, this sets --list param because the below code searches the doll
		if param.split(" ")[-1] == "--list" or param.split(" ")[-1] == "list" or param.split(" ")[-1] == "-l":
			param = " ".join(param.split(" ")[:-1])
			costumeType = "--list"
		print(param + ", " +str(costumeType))
		
		doll, res = getSearchResult(param)
		msgText = ""
		if res[0][1] != 100:
			msgText = "No T-Doll was found with that name, so I'm returning the closest result. Did you mean: "+", ".join([i[0] for i in res]) + "\n"

		if costumeType == "--list":
			if 'costumes' in doll:
				msgText += getPossibleCostumes(doll)
				msg = await client.send_message(message.channel, msgText)
				#ord starts at 127462 btw
				emojis = ["🇦","🇧","🇨","🇩","🇪","🇫","🇬","🇭","🇮","🇯","🇰","🇱","🇲","🇳","🇴","🇵","🇶","🇷","🇸","🇹"]
				for i in range(len(doll['costumes'])):
					try:
						await client.add_reaction(msg,emojis[i])
					except:
						print(emojis[i]+" is not a valid emoji")
			else:
				await client.send_message(message.channel, "Sorry, the data for this T-Doll is missing.")
				return			
		else:
			try:
				msgText += getDollCostume(doll,costumeType)
				msg = await client.send_message(message.channel, msgText)
				await client.add_reaction(msg,"🔥")
			except Exception:
				await client.send_message(message.channel, "An error has occured and I am unable to complete your request.")
				print(traceback.print_exc())
			#emojis = ['⏪','⏩']
			#for e in emojis:
			#	try:
			#		await client.add_reaction(msg,e)
			#	except:
			#		print(e+" is not a valid emoji")
		return
		#print("WARN: No T-Doll was found for " + param)
		#await client.send_message(message.channel, "No T-Doll was found with that name.")
		#return
	elif message.content.startswith(COMMAND_PREFIX+"timer "):
		param = message.content[(len(COMMAND_PREFIX+"timer")+1):]
		print("arg: "+param)
		if param.count(':') == 1:
			param = param +":00"
			#If timer is formatted like :20, append a 0 so it's 0:20 instead
			if param.split(":")[0] == '':
				param = "0"+param
		elif param.count(':') == 0:
			print("Argument was too ambiguous.")
			await client.send_message(message.channel, "I don't support numbers without `:`. Please format your query with `:`.")
			return
			#print("Converted " +param+" to ",end="")
			
			#if (len(param) % 2) != 0:
			#	param = "0"+param +":00"
			#if len(param) == 2:
			#	param = "0:"+param + ":00"
			#else:
			#	param = ':'.join(param[i:i+2] for i in range(0, len(param), 2)) + ":00"
			#print(param)
		try:
			#Strip leading 0 off a timer, like 08:00 -> 8:00
			#But first check if it's not 0:XX so we don't accidentally do something like 0:40 -> :40
			if int(param.split(':')[0]) != 0:
				param = param.lstrip('0')
		except:
			await client.send_message(message.channel, "This does not appear to be a timer.")
			print(param + " was not a valid timer.")
			return
		print("stripped arg: "+param)
		
		res = []
		#Speedup hack, equipment is always <1 hour and dolls are >= 1 hour so we search equipment if it's <1
		if int(param.split(':')[0]) == 0:
			for equip in equipmentdex:
				if 'production' in equip and 'timer' in equip['production']:
					if param == equip['production']['timer']:
						res.append(equip)
			if len(res) == 0:
				await client.send_message(message.channel, "No equipment was found matching that production timer.")
				print("No match found for "+param)
			elif len(res) == 1:
				await client.send_message(message.channel, content="Found an exact match for the timer.", embed=equipInfo(res[0]))
			else:
				await client.send_message(message.channel, "Equipment that matches this production timer: "+", ".join(i['name'] for i in res))

		else:
			for doll in frontlinedex:
				if 'production' in doll and 'timer' in doll['production']:
					if param == doll['production']['timer']:
						res.append(doll)
			if len(res) == 0:
				await client.send_message(message.channel, "No dolls were found matching that production timer.")
				print("No match found for "+param)
			elif len(res) == 1:
				await client.send_message(message.channel, content="Found an exact match for the timer.", embed=dollInfo(res[0]))
			else:
				await client.send_message(message.channel, "T-Dolls that match this production timer: "+", ".join(i['name']+" ("+i['type']+" "+num2stars(i['rating']) +")" for i in res))
		return
	elif message.content.startswith(COMMAND_PREFIX+"quote "):
		if quotedex:
			param = message.content[(len(COMMAND_PREFIX+"quote")+1):].lower()
			print(param)
			doll, res = getSearchResult(param)
			if 'internalName' in doll:
				if doll['internalName'] in quotedex:
					msg = doll['name']+"'s quotes:\n"
					for key,value in sorted(quotedex[doll['internalName']].items()):
						msg += "**"+key.capitalize()+"**: "+" ".join(value)+"\n"
					await client.send_message(message.channel, msg)
				else:
					await client.send_message(message.channel, "This doll has no quotes... Somehow.")
					print(doll['name']+" with internalName "+doll['internalName']+ " has no quotes.")
			else:
				await client.send_message(message.channel, "Sorry, the internal name for this doll is missing, which is needed to pull the quote from the data.")
			return
		else:
			await client.send_message(message.channel, "This command is unavailable. If you are the bot owner, check https://github.com/RhythmLunatic/Girls-Frontline-Discord-Search for instructions.")
	elif message.content.startswith(COMMAND_PREFIX+"help"):
		param = message.content[(len(COMMAND_PREFIX+"help")+1):].lower()
		if len(param) > 0:
			if param == "image":
				msg = "**Summary:**\nSearch doll images and costumes. This command is in beta. Changing costumes with reaction buttons coming eventually.\n"
				msg += "**Detailed Usage:**\n"
				msg += "Press the fire react to show damage art for a doll. Remove the fire react to show normal art.\n"
				msg += "Costumes are ordered from A to the number of costumes, with damage art coming after regular art. (A is always default and B is always default (Damaged)\n"
				msg += "You can append the '--list' or '-l' flag to the end of your search to show all the costume names.\n"
				msg += "**Examples:**\n"
				msg += "`"+COMMAND_PREFIX+"image UMP45`: Show UMP45's default costume.\n"
				msg += "`"+COMMAND_PREFIX+"image Skorpion, Crimson Starlet`: Show Skorpion's Crimson Starlet costume.\n"
				msg += "`"+COMMAND_PREFIX+"image UMP9,B`: Show UMP9's damaged art, which is the second costume in the list.\n"
				msg += "`"+COMMAND_PREFIX+"image M16A1,C`: Show M16A1's 3rd costume.\n"
				msg += "`"+COMMAND_PREFIX+"image Negev --list`: Show all available costumes for Negev.\n"
				#msg += "`"+COMMAND_PREFIX+"Negev --damaged`: Show Negev's damage art for the costume.\n"
				await client.send_message(message.channel, msg)
			elif param == "timer":
				msg = "Find a matching doll or equip for the timer. Fairies coming eventually.\n"
				msg += "Usage examples:\n"
				msg += "`"+COMMAND_PREFIX+"timer 0:40` or `"+COMMAND_PREFIX+"timer :40`: Search for a matching timer of 0 hours 40 mins\n"
				msg += "`"+COMMAND_PREFIX+"timer 8:00` or `"+COMMAND_PREFIX+"timer 08:00` or `"+COMMAND_PREFIX+"timer 08:00:00`: Search for a matching timer of 8 hours\n"
				await client.send_message(message.channel, msg)
			elif param == "status":
				msg = "Show the amount of servers this bot is in and the number of dolls and equipment indexed."
				msg += "\nIf --extra is appended the lowest and highest production timers for weapons and dolls will be shown."
				await client.send_message(message.channel, msg)
			else:
				print("Tried to get help for "+param+ " but there was none.")
				await client.send_message(message.channel, "No help available for this command yet.")
			return
		msg = "I am I.O.P., a Discord bot that will give you useful information about T-Dolls and equipment.\n"
		msg+="Running version "+version+"\n"
		msg+= "Commands:\n**"+COMMAND_PREFIX+"search**: Search a T-Doll and display all information. Example: `"+COMMAND_PREFIX+"search UMP45`\n"
		msg+="**"+COMMAND_PREFIX+"equip**: Search an equipment or fairy. **This command is in beta, some information is still missing.** Example: `"+COMMAND_PREFIX+"equip Armor Fairy`\n"
		msg+="**"+COMMAND_PREFIX+"image:** Search a T-Doll's image and display it, or search a doll's costume. Check this command's help for more information. Example: `"+COMMAND_PREFIX+"image UMP40`, `"+COMMAND_PREFIX+"image M16A1,Boss`\n"
		if quotedex:
			msg+="**"+COMMAND_PREFIX+"quote:** List all the quotes for a doll. If the command doesn't fail, that is.\n"
		msg+="**"+COMMAND_PREFIX+"timer:** List T-Dolls or equipment that match the production timer. Ex. `"+COMMAND_PREFIX+"timer 8:10` or `"+COMMAND_PREFIX+"timer 0:40`\n"
		msg+="**"+COMMAND_PREFIX+"status:** See diagnostic information like the amount of dolls indexed, number of discords, etc\n"
		msg+="For advanced help, do `$gfhelp <short name of command>`. Example: `"+COMMAND_PREFIX+"help image`, `$gfhelp quote`\n\n"
		msg+="Invite: Check github page\n"
		msg+="Github: https://github.com/RhythmLunatic/Girls-Frontline-Discord-Search\n"
		msg+="Contact: /u/RhythmLunatic on Reddit, RhythmLunatic on Github, or Accelerator#6473 on Discord\n"
		msg+="The information in this bot is Ⓒ en.gfwiki.com and licenced under CC BY-SA 3.0. Support the wiki!"
		await client.send_message(message.channel, msg)
#startup...
print("Starting up I.O.P. version "+version+"...")
print("Discord.py version is "+discord.__version__)
print("Reading the frontlinedex into memory. This may take a while.")
file_obj = open("girlsfrontline.json", "r")
frontlinedex = json.loads(file_obj.read())
file_obj.close()
print("Reading bonus information...")
file_obj = open("gf_flavortext.json", "r")
bonusdex = json.loads(file_obj.read())
file_obj.close()
if os.path.isfile("NewCharacterVoice.json"):
	print("Reading quotes.")
	file_obj = open("NewCharacterVoice.json", "r")
	quotedex = json.loads(file_obj.read())
	file_obj.close()
	print(COMMAND_PREFIX+"quote is now available!")

#Yeah it's stupid as fuck, I have to fix my scraper
print("Injecting aliases into the frontlinedex...")
for doll in frontlinedex:
	if doll['name'] in bonusdex and 'alias' in bonusdex[doll['name']]:
		doll['alias'] = bonusdex[doll['name']]['alias']
#for doll in frontlinedex:
#	if doll['name'] == "Five-seveN":
#		assert doll['alias'], "Missing aliases!"

print("Reading equipment data into memory. This may take a while.")
file_obj = open("equipment.json", "r")
equipmentdex = json.loads(file_obj.read())
file_obj.close()

print("Done! Now logging in...")
client.run(DISCORD_TOKEN)
