import discord
import json
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
version = "IOP 2.4-20190726"
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

#@client.event
#async def loaddex(message):
#	reload()
#	await client.send_message(message.channel, "Done.")
def serverCount():
	print("Serving " + str(len(client.servers)) +" commanders")
	return "Serving " + str(len(client.servers)) +" commanders"

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
	return embed
	

def equipInfo(equip):
	embed = discord.Embed(title=equip['name'] + " " + num2stars(equip['rating']), url=SITE_DOMAIN+equip['url'], color=gfcolors[equip['rating']])
	#embed.add_field(name="Type", value=equip['type'], inline=True)
	#{ "hp" : 40, "ammo": 10, "ration": 10, "dmg": 12, "acc": 6, "eva": 9, "rof": 31, "spd": 15, "armor": 0, "crit_rate": 20, "crit_dmg": 50, "pen": 10},
	#embed.add_field(name="Base Stats", value="**HP:** "+str(equip['baseStats']['hp']) + ", **DMG:** " + str(equip['baseStats']['dmg']) + ", **ACC:** " + str(equip['baseStats']['acc']) + ", **EVA:** " + str(equip['baseStats']['eva']) + ", **ROF:** " + str(equip['baseStats']['rof']))
	if 'constStats' in equip:
		stats = "**Movement:** "+str(equip['constStats']['mov']) + "**, Crit. rate:** " + str(equip['constStats']['crit_rate'])+"%, **Crit DMG:** "+str(equip['constStats']['crit_dmg']) + ", **Armor Pen.:** " + str(equip['constStats']['pen'])
		stats += "\n**HP:** "+str(equip['maxStats']['hp']) + ", **DMG:** " + str(equip['maxStats']['dmg']) + ", **ACC:** " + str(equip['maxStats']['acc']) + ", **EVA:** " + str(equip['maxStats']['eva']) + ", **ROF:** " + str(equip['maxStats']['rof']) + ", **Armor:** "+ str(equip['maxStats']['armor'])
		embed.add_field(name="Max Stats",value=stats)
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
	#Not all equips have abilities yet since some are unreleased.
	if 'ability' in equip:
		embed.add_field(name="Skill: "+equip['ability']['name'], value=getAbility(equip,'ability'), inline=False)
	if 'ability2' in equip:
		embed.add_field(name="2nd Skill: "+equip['ability2']['name'], value=getAbility(equip,'ability2'), inline=False)

	
	#if equip['name'] in bonusdex and 'flavor' in bonusdex[equip['name']]:
	#	embed.set_footer(text=bonusdex[equip['name']]['flavor'])
	if 'img' in equip:
		embed.set_image(url=PIC_EQUIP_DOMAIN+equip['img'])
		print(PIC_DOMAIN+equip['img'])
	return embed

def getSearchResult(param):
	res = process.extract(param, [doll['name'] for doll in frontlinedex], limit=3)
	return res[0][0], res

def postdollCostume(doll,costumeType):
	if 'costumes' in doll:
		if costumeType:
			if costumeType == "--list":
				return "Costumes for "+doll['name']+": "+", ".join(doll['costumes'].keys())
			else:
				for cName in doll['costumes'].keys():
					if cName.lower() == costumeType.lower():
						if cName.endswith("_damage"):
							name = cName.split("_")[0]+" (Damaged)"
							return doll['name'] + ": "+name+"\n"+PIC_DOMAIN+doll['costumes'][cName]
						else:
							return doll['name'] + ": "+cName+"\n"+PIC_DOMAIN+doll['costumes'][cName]
			print(costumeType + " not found in "+doll['name'])
			return "Couldn't find that costume. Costumes: "+", ".join(doll['costumes'].keys())
		#else
		return doll['name'] + ":\n"+PIC_DOMAIN+doll['img']
	#else
	return "Sorry, either there are no images for this doll or the data is missing."

#Behold, a stateless function, by parsing my own messages
#Spaghetti code is subjective, ok?
@client.event
async def on_reaction_add(reaction,user):
	if user == client.user:
		return
	if reaction.message.author != client.user:
		return
	msg = reaction.message.content.splitlines()
	if not msg[-1].endswith(".png"):
		return
	name,costume = msg[0].split(":")
	if "(" in costume:
		#costume = costume.split("(")[0].strip()
		return
	elif costume.strip() == "":
		costume = "default_damage"
	else:
		costume = costume.strip() + "_damage"
		
	for doll in frontlinedex:
		if name == doll['name']:
			await client.edit_message(reaction.message,new_content=postdollCostume(doll,costume))
	return
	
#Behold, the above but it's the opposite
@client.event
async def on_reaction_remove(reaction,user):
	if user == client.user:
		return
	if reaction.message.author != client.user:
		return
	msg = reaction.message.content.splitlines()
	if not msg[-1].endswith(".png"):
		return
	name,costume = msg[0].split(":")
	if "(" in costume:
		costume = costume.split("(")[0].strip()
	else:
		return
	for doll in frontlinedex:
		if name == doll['name']:
			await client.edit_message(reaction.message,new_content=postdollCostume(doll,costume))
	return
	
@client.event
async def on_message(message):
	if message.author == client.user:
		return
	if message.content.startswith(COMMAND_PREFIX+"status"):
		param = message.content[(len(COMMAND_PREFIX+"status")+1):].lower()
		st = serverCount()
		st += "\n"+str(len(frontlinedex))+" dolls indexed (incl. MOD variants & 1 kalina)"
		st += "\n"+str(len(equipmentdex))+" equipments indexed."
		#require --extra because this command is expensive to compute and I don't want people spamming it.
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
				await client.send_message(message.channel, embed=embed)
				return
			elif 'alias' in doll and param == doll['alias'].lower():
				print(param+" -> "+doll['name'])
				embed = dollInfo(doll)
				await client.send_message(message.channel, embed=embed)
				return
		dollName, res = getSearchResult(param)
		for doll in frontlinedex:
			if dollName == doll['name']:
				embed = dollInfo(doll)
				await client.send_message(message.channel, content="No T-Doll was found with that exact name, so I'm returning the closest result. Did you mean: "+", ".join([i[0] for i in res]), embed=embed)
				return
		else:
			print("WARN: No T-Doll was found for " + param)
			await client.send_message(message.channel, "No T-Doll was found with that name.")
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
		for doll in frontlinedex:
			if param == doll['name'].lower():
				msg = await client.send_message(message.channel, postdollCostume(doll,costumeType))
				#This should really be refactored
				if costumeType != "--list":
					await client.add_reaction(msg,"🔥")
					#emojis = ['⏪','⏩']
					#for e in emojis:
					#	try:
					#		await client.add_reaction(msg,e)
					#	except:
					#		print(e+" is not a valid emoji")
				return
		dollName, res = getSearchResult(param)
		for doll in frontlinedex:
			if dollName == doll['name']:
				await client.send_message(message.channel, "No T-Doll was found with that name, so I'm returning the closest result. Did you mean: "+", ".join([i[0] for i in res]) + "\n"+postdollCostume(doll,costumeType))
				return
		print("WARN: No T-Doll was found for " + param)
		await client.send_message(message.channel, "No T-Doll was found with that name.")
		return
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
			for doll in frontlinedex:
				if param == doll['name'].lower():
					if 'internalName' in doll:
						if doll['internalName'] in quotedex:
							msg = ""
							for key,value in sorted(quotedex[doll['internalName']].items()):
								msg += "**"+key.capitalize()+"**: "+" ".join(value)+"\n"
							await client.send_message(message.channel, msg)
					else:
						await client.send_message(message.channel, "Sorry, the internal name for this doll is missing, which is needed to pull the quote from the data.")
					return
			res = process.extract(param, [doll['name'] for doll in frontlinedex], limit=3)
		else:
			await client.send_message(message.channel, "This command is unavailable. If you are the bot owner, check https://github.com/RhythmLunatic/Girls-Frontline-Discord-Search for instructions.")
	elif message.content.startswith(COMMAND_PREFIX+"help"):
		param = message.content[(len(COMMAND_PREFIX+"help")+1):].lower()
		if len(param) > 0:
			if param == "image":
				msg = "Search doll images and costumes. This command is in beta. Correct costume names coming eventually. Changing costumes with reaction buttons coming eventually.\n"
				msg += "Press the fire react to show damage art for a doll. Remove the fire react to show normal art."
				msg += "You can append the '--list' or '-l' flag to the end of your search to show all the costume names.\n"
				msg += "Usage examples:\n"
				msg += "`"+COMMAND_PREFIX+"image UMP45`: Show UMP45's default costume.\n"
				msg += "`"+COMMAND_PREFIX+"image M16A1,Boss`: Show M16A1's Boss costume.\n"
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
		msg = "I am I.O.P., a Discord bot that will give you useful information about T-Dolls.\n"
		msg+="Running version "+version+"\n"
		msg+= "Commands:\n**"+COMMAND_PREFIX+"search**: Search a T-Doll and display all information. Example: "+COMMAND_PREFIX+"search UMP45\n"
		msg+="**"+COMMAND_PREFIX+"image:** Search a T-Doll's image and display it, or search a doll's costume. Check this command's help for more information. Example: `"+COMMAND_PREFIX+"image UMP40`, `"+COMMAND_PREFIX+"image M16A1,Boss`\n"
		if quotedex:
			msg+="**"+COMMAND_PREFIX+"quote:** List all the quotes for a doll. If the command doesn't fail, that is.\n"
		msg+="**"+COMMAND_PREFIX+"timer:** List T-Dolls or equipment that match the production timer. Ex. `"+COMMAND_PREFIX+"timer 8:10` or `"+COMMAND_PREFIX+"timer 0:40`\n"
		msg+="**"+COMMAND_PREFIX+"status:** See diagnostic information like the amount of dolls indexed, number of discords, etc\n"
		msg+="For advanced help, do `$gfhelp <short name of command>`. Example: `"+COMMAND_PREFIX+"help image`, `$gfhelp quote`\n\n"
		msg+="Invite: Check github page\n"
		msg+="Github: https://github.com/RhythmLunatic/Girls-Frontline-Discord-Search\n"
		msg+="Contact: /u/RhythmLunatic on Reddit, RhythmLunatic on Github, or Accelerator#6473 on Discord"
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
if os.path.isfile("CharacterVoice.json"):
	print("Reading quotes.")
	file_obj = open("CharacterVoice.json", "r")
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
