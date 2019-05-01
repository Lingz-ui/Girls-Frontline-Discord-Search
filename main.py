import discord
import json
import re
import os
import random
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

client = discord.Client()
#Your discord bot token. For your safety this is an environment variable, but you're free to put your token here if you really want to.
DISCORD_TOKEN=os.environ['GFBOT_TOKEN']
#The prefix for the bot commands. Default is $gf
COMMAND_PREFIX="$gf"
#COMMAND_NAME="$gfsearch"
#The domain for the images extracted from Girls' Frontline. The bot will combine it like PIC_DOMAIN + "pic_ump45.png"
PIC_DOMAIN="http://103.28.71.152:999/pic/"
#The domain for the icons for dolls like the ones that are on the top left of the doll cards.
#Icons are disabled because they make embeds worse.
#ICON_DOMAIN="http://103.28.71.152:999/pic_compressed/icons/"
#The domain for the Girls' Frontline wiki (urls are kept in girlsfrontline.json)
SITE_DOMAIN = "https://en.gfwiki.com"
#pls don't touch.
gfcolors = [0, 0, 0xffffff, 0x6bdfce, 0xd6e35a, 0xffb600, 0xdfb6ff]
version = "IOP 2.0-20190501"
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
		embed.add_field(name="Constant Stats", value="**Movement:** "+str(doll['constStats']['mov']) + "**, Crit. rate:** " + str(doll['constStats']['crit_rate'])+"%, **Crit DMG:** "+str(doll['constStats']['crit_dmg']) + ", **Armor Pen.:** " + str(doll['constStats']['pen']) )
	if 'maxStats' in doll:
		embed.add_field(name="Max Stats", value="**HP:** "+str(doll['maxStats']['hp']) + ", **DMG:** " + str(doll['maxStats']['dmg']) + ", **ACC:** " + str(doll['maxStats']['acc']) + ", **EVA:** " + str(doll['maxStats']['eva']) + ", **ROF:** " + str(doll['maxStats']['rof']) + ", **Armor:** "+ str(doll['maxStats']['armor']) )
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
	

@client.event
async def on_message(message):
	if message.author == client.user:
		return
	if message.content.startswith(COMMAND_PREFIX+"status"):
		st = serverCount() + "\n"+str(len(frontlinedex))+" dolls indexed (incl. MOD variants)"
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
		res = process.extract(param, [doll['name'] for doll in frontlinedex], limit=3)
		if res:
			print(res[0][0])
			for doll in frontlinedex:
				if res[0][0] == doll['name']:
					embed = dollInfo(doll)
					await client.send_message(message.channel, content="No T-Doll was found with that exact name, so I'm returning the closest result. Did you mean: "+", ".join([i[0] for i in res]), embed=embed)
					return
		else:
			print("WARN: No T-Doll was found for " + param)
			await client.send_message(message.channel, "No T-Doll was found with that name.")
		return
	elif message.content.startswith(COMMAND_PREFIX+"image "):
		param = message.content[(len(COMMAND_PREFIX+"image")+1):].lower()
		print(param)
		for doll in frontlinedex:
			if param == doll['name'].lower():
				if 'img' in doll:
					msg = doll['name'] + ":\n"+PIC_DOMAIN+doll['img']
					await client.send_message(message.channel, msg)
				else:
					await client.send_message(message.channel, "Sorry, the image for this doll is missing.")
				return
		res = process.extract(param, [doll['name'] for doll in frontlinedex], limit=3)
		if res:
			#print(res)
			await client.send_message(message.channel, "No T-Doll was found with that name. Did you mean: "+", ".join([i[0] for i in res]))
		else:
			print("WARN: No T-Doll was found for " + param)
			await client.send_message(message.channel, "No T-Doll was found with that name.")
	elif message.content.startswith(COMMAND_PREFIX+"quote "):
		if quotedex:
			param = message.content[(len(COMMAND_PREFIX+"quote")+1):].lower()
			print(param)
			for doll in frontlinedex:
				if param == doll['name'].lower():
					if 'internalName' in doll:
						if doll['internalName'] in quotedex:
							msg = ""
							for key,value in quotedex[doll['internalName']].items():
								msg += "**"+key.capitalize()+"**: "+" ".join(value)+"\n"
							await client.send_message(message.channel, msg)
					else:
						await client.send_message(message.channel, "Sorry, the internal name for this doll is missing, which is needed to pull the quote from the data.")
					return
			res = process.extract(param, [doll['name'] for doll in frontlinedex], limit=3)
		else:
			await client.send_message(message.channel, "This command is unavailable. If you are the bot owner, check https://github.com/RhythmLunatic/Girls-Frontline-Discord-Search for instructions.")
	elif message.content.startswith(COMMAND_PREFIX+"help"):
		msg = "I am I.O.P., a Discord bot that will give you useful information about T-Dolls.\n"
		msg+="Running version "+version+"\n"
		msg+= "Commands:\n**"+COMMAND_PREFIX+"search**: Search a T-Doll and display all information. Example: "+COMMAND_PREFIX+"search UMP45\n"
		msg+="**"+COMMAND_PREFIX+"image:** Search a T-Doll's image and display it. Special parameters unimplemented. Example: "+COMMAND_PREFIX+"image UMP40\n"
		if quotedex:
			msg+="**"+COMMAND_PREFIX+"quote:** List all the quotes for a doll. If the command doesn't fail, that is.\n"
		msg+="**"+COMMAND_PREFIX+"status:** See how many servers this bot is in.\n\n"
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

print("Done! Now logging in...")
client.run(DISCORD_TOKEN)
