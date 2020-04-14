'''
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

This program is written by Rhythm Lunatic.
'''

'''
HOW THE DATABASES WORK
girlsfrontline.json: Data scraped from gfwiki. Plus NPCs and Sangvis Ferri dolls.
gf_flavortext.json: Bonus data not scraped from gfwiki. Can include quotes too if you add a "quotes" dict to the gf_flavortext with the keys inside them (Look at Destroyer for an example)
Why is stuff injected in instead of being preprocessed? Because it's easier to maintain, girlsfrontline.json takes a long time to update

Here's the quote keys if you didn't dump the data from the girls frontline game like I told you to:
"dialogue1"       - first adjutant dialogue
"dialogue2"       - second adjutant dialogue
"dialogue3"       - third adjutant dialogue, this has a lower chance of appearing
"dialoguewedding" - wedding adjutant dialogue, said sometimes after you've ~~married~~ oathed them
"soulcontract"    - dialogue when you marry them
"introduce"       - Dialogue used when you look at them in the index. (The english translators copypasted from gain, but it's unique in CN)
"gain"            - Dialogue when you obtain them
"allhallows"      - Dialogue used during halloween.
"newyear"         - Take a wild guess.
"valentine"       - ...
"christmas"       - ...

There are various others but they're only shown in the index, they're translations for voice lines and stuff

'''

import discord
import json
#Error handler
import traceback
#To insert ability parameters for dolls
import re
#environment token
import os
#For random flavor texts if quotes are present.
import random
#Time is needed for gfstatus time sort.
import time
#datetime is needed to show seasonal quotes. Yes, really.
#from datetime import datetime
#Return closest result for dolls. (Thank god because nobody ever spells anything correctly with this bot)
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
#to round down equipment values, because it's calculated on the fly..
import math

client = discord.Client()
#Your discord bot token. For your safety this is an environment variable, but you're free to put your token here if you really want to.
DISCORD_TOKEN=os.environ['GFBOT_TOKEN']
#The prefix for the bot commands. Default is $gf
COMMAND_PREFIX="$gf"
#The domain for the images extracted from Girls' Frontline. The bot will combine it like PIC_DOMAIN + "pic_ump45.png"
#This is my server, in case you didn't already realize that.
PIC_DOMAIN="http://103.28.71.152:998/pic/"
#The domain for the equipment images extracted from Girls' Frontline. The bot will combine it like PIC_EQUIP_DOMAIN + "pic_ump45.png"
PIC_EQUIP_DOMAIN="http://103.28.71.152:998/pic/equip/"
#The domain for the icons for dolls like the ones that are on the top left of the doll cards.
#Icons are disabled because they make embeds worse.
#ICON_DOMAIN="http://103.28.71.152:999/pic_compressed/icons/"
#The domain for the Girls' Frontline wiki (urls are kept in girlsfrontline.json)
SITE_DOMAIN = "https://en.gfwiki.com"
#pls don't touch.
version = "IOP 3.21-20200414"

#This is the exp table for levelling up a T-Doll.
#Accumulated exp is calculated on the fly.
exp_table = [
	#exp table is flat from 1-26.
	100,  200,  300,  400,  500,
	600,  700,  800,  900,  1000,
	1100, 1200, 1300, 1400, 1500,
	1600, 1700, 1800, 1900, 2000,
	2100, 2200, 2300, 2400, 2500,
	2600,
	#from here the requirements change up a bit
	2800,
	3100,
	3400,
	4200, #30
	4600,
	5000,
	5400,
	5800,
	6300,
	6700,
	7200,
	7700,
	8200,
	8800, #40
	9300,
	9900,
	10500,
	11100,
	11800,
	12500,
	13100,
	13900,
	14600,
	15400, #50
	16100,
	16900,
	17700,
	18600,
	19500,
	20400,
	21300, #57... It's flat again
	22300,
	23300,
	24300, #60
	25300,
	26300,
	27400, #63
	28500,
	29600,
	30800,
	32000,
	33200,
	34400, #70
	45100,
	46800,
	48600,
	50400,
	52200,
	54000,
	55900,
	57900,
	59800,
	61800,
	63900,
	66000,
	68100,
	70300,
	72600,
	74800,
	77100,
	79500,
	81900,
	84300,
	112600,
	116100,
	119500,
	123100,
	126700,
	130400,
	134100,
	137900,
	141800,
	145700, #99... Below is 100-120
	100000,120000,140000,160000,180000,200000,220000,240000,280000,360000,480000,640000,900000,1200000,1600000,2200000,3000000,4000000,5000000,6000000,0
]
assert (len(exp_table) == 100 or len(exp_table) == 120),"Exp table is wrong size. Length was "+str(len(exp_table))

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    
def printWarn(text):
	print(bcolors.WARNING + text + bcolors.ENDC)

def printError(text):
	print(bcolors.FAIL + text + bcolors.ENDC)


gfcolors = [
	0xadadad, #NPCs & SF - Grey
	0,        #Nothing has 1 stars.
	0xffffff, #2 stars   - White
	0x6bdfce, #3 stars   - Turquoise
	0xd6e35a, #4 stars   - Green
	0xffb600, #5 stars   - Orange
	0xffb600, #6 stars   - Orange
	0xdfb6ff  #EXTRAstar - Purple
]
'''def getgfcolors(n):
	if n == 100:
		return 0xdfb6ff
	elif n > 5:
		return gfcolors[5]
	else:
		return gfcolors[n]'''

def num2stars(n):
	#★☆⚝
	if n == 7:
		return "⚝"
	#NPCs and SF dolls don't really have rarities so don't return any stars
	elif n < 1:
		return ""
	#For HK416 MOD 2
	elif n > 5:
		#Behold, the pythonic way of duplicating text. "str"*5 would be "strstrstrstrstr"
		return "★"*n
	#Normal dolls
	st = ""
	for i in range(5):
		if i < n:
			st = st + "★"
		else:
			st = st + "☆"
	#The really pythonic way would be "★"*n+"☆"*(5-n) but I don't think anyone would be able to read that
	return st


def intTryParse(value, errorVal=-1):
	try:
		return int(value)
	except:
		return errorVal

#And I thought I'd never have to use this...
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
	#The bot itself doesn't count as a member
	numMembers -= len(client.servers)
	print("Serving " + str(len(client.servers)) +" bases and "+str(numMembers)+ " commanders")
	return "Serving " + str(len(client.servers)) +" bases and "+str(numMembers)+ " commanders"

'''
internalName = internal name of doll.
quoteType = quote key you want. (Scroll up to the top if you don't know)
'''
def getQuote(internalName, quoteType):
	#Yes I know the ifs can be an and statement I'm not changing it
	if quotedex:
		if internalName in quotedex:
			if quoteType in quotedex[internalName]:
				return " ".join(quotedex[internalName][quoteType])
	return False
	
#unnecessary
#def quoteExists(internalName,quoteType):
#	return quotedex and internalName in quotedex and quotetype in quotedex[internalName]

#super unnecessary
'''
def getFlavorText(dollInternalName):
	quote = None
	curDate = datetime.now()
	if (curDate.month == 1 and curDate.day == 1) or (curDate.month==12 and curDate.day == 31):
		quote = getQuote(dollInternalName,"newyear")
	if (curDate.month == 2 and curDate.day == 14):
		quote = getQuote(dollInternalName,"valentine")
	elif (curDate.month == 10 and curDate.day > 25):
		quote = getQuote(dollInternalName,"allhallows")
	elif curDate.month == 12 and curDate.day > 15:
		quote = getQuote(dollInternalName,"christmas")
	if quote:
		return quote
	#the MOD 3 dolls can have blank gain tags for some reason, so check if it's not an empty string.
	if getQuote(dollInternalName,"gain") != "":
		return getQuote(dollInternalName, random.choice(["dialogue1","dialogue2","dialogue3","dialoguewedding","gain"]))
	else:
		return getQuote(dollInternalName, random.choice(["dialogue1","dialogue2","dialogue3","dialoguewedding"]))
'''

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
	
#if statements for all the things!!!!!!
def dollInfo(doll):
	embed = discord.Embed(title="No."+(str(doll["num"]) if doll['num'] > 0 else "?")+" - "+ doll['name'] + " " + num2stars(doll['rating']), url=SITE_DOMAIN+doll['url'], color=gfcolors[doll['rating']])
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
		
	#Some NPCs have descriptions.
	if 'description' in doll:
		embed.add_field(name="Description", value=doll['description'], inline=False)
		
	#embed.add_field(name="Tile Bonus Types", value=doll['bonus_type'], inline=True)
	if doll['name'] in bonusdex and 'flavor' in bonusdex[doll['name']]:
		embed.set_footer(text=bonusdex[doll['name']]['flavor'])
	else:
		if 'internalName' in doll:
			#quote = getFlavorText(doll['internalName'])
			quote = None
			#the MOD 3 dolls can have blank gain tags for some reason, so check if it's not an empty string.
			if getQuote(doll['internalName'],"gain") != "":
				quote = getQuote(doll['internalName'], random.choice(["dialogue1","dialogue2","dialogue3","dialoguewedding","gain"]))
			else:
				quote = getQuote(doll['internalName'], random.choice(["dialogue1","dialogue2","dialogue3","dialoguewedding"]))
			if quote:
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
	if 'stats' in equip:
		outStats = ""
		for k in equip['stats']:
			print(k)
			outStats += "**"+k+":** "
			#Fuck this data I swear to god
			#The min stat is an int... But only guarenteed if growth stat exists!
			#If growth doesn't exist then it can be a string because fuck you
			if 'growth' in equip['stats'][k]:
				if (equip['stats'][k]['growth'] == -9999):
					outStats += "??? (Missing data!)"
					print("Missing keys in equip.")
					print(str(equip['stats'][k]))
				elif 'max' in equip['stats'][k]:
					outStats += str(math.floor(equip['stats'][k]['max'] * equip['stats'][k]['growth'])) + "\n"
				elif 'min' in equip['stats'][k]:
					outStats += str(math.floor(equip['stats'][k]['min'] * equip['stats'][k]['growth'])) + "\n"
				else:
					outStats += "??? (Bad data in JSON?)"
					print("Has growth key, but no min/max key.")
					print(str(equip['stats'][k]))
			elif 'max' in equip['stats'][k]:
				outStats += str(equip['stats'][k]['max']) + "\n"
			elif 'min' in equip['stats'][k]:
				outStats += str(equip['stats'][k]['min']) + "\n"
			else:
				outStats += "??? (Missing data!)"
				print("Bad keys in equip.")
				print(str(equip['stats'][k]))
		embed.add_field(name="Stats",value=outStats,inline=True)
	#if 'constStats' in equip:
	#	stats = "**Movement:** "+str(equip['constStats']['mov']) + "**, Crit. rate:** " + str(equip['constStats']['crit_rate'])+"%, **Crit DMG:** "+str(equip['constStats']['crit_dmg']) + ", **Armor Pen.:** " + str(equip['constStats']['pen'])
	#	stats += "\n**HP:** "+str(equip['maxStats']['hp']) + ", **DMG:** " + str(equip['maxStats']['dmg']) + ", **ACC:** " + str(equip['maxStats']['acc']) + ", **EVA:** " + str(equip['maxStats']['eva']) + ", **ROF:** " + str(equip['maxStats']['rof']) + ", **Armor:** "+ str(equip['maxStats']['armor'])
	#	embed.add_field(name="Max Stats",value=stats)
		
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
		print(PIC_EQUIP_DOMAIN+equip['img'])
	return embed

# This turns an embed into a regular message that looks like an embed
# because some people refuse to turn on embeds
def embed2text(embed):
	#print(embed.fields)
	msg = ""
	msg += "**" + embed.title + "**\n"
	for field in embed.fields:
		msg += "__"+field.name+"__\n"
		msg += field.value + "\n"
	return msg
	

"""
param: doll or equip to search
search_equip: if true, search equipment dex instead of doll dex.

If result was an exact match, returns None as the second returned var as closest search was unnecessary.
Otherwise the second returned var is a tuple of doll names and closeness percentage. Ex: [["M4A1",80],["M16A1",75],["M4 SOPMOD II",60]]
"""
def getSearchResult(param, search_equip=False):
	if search_equip == True:
		res = process.extract(param, [equip['name'] for equip in equipmentdex], limit=3)
		print("Result: "+res[0][0])
		for equip in equipmentdex:
			if res[0][0] == equip['name']:
				return equip, res
	else:
		for doll in frontlinedex:
			if param == doll['name'].lower():
				return doll, None
			elif 'alias' in doll and param == doll['alias'].lower():
				print(param+" -> "+doll['name'])
				return doll, None
		
		res = process.extract(param, [doll['name'] for doll in frontlinedex], limit=3)
		print("Result: "+res[0][0]+" ("+str(res[0][1])+"% match)")
		if res[0][1] < 80:
			printWarn("Match result was <80%, might be a doll that doesn't exist.")
		for doll in frontlinedex:
			if res[0][0] == doll['name']:
				return doll, res
	#raise Exception("This shouldn't be possible! No result found in search.")
	printError("This shouldn't be possible! No result found in search.")



#This REALLY should not be a function
def getPossibleCostumes(doll):
	msg = "Costumes for "+doll['name']+": "
	for i in range(len(doll['costumes'])):
		msg+=chr(i+65)+". **"+doll['costumes'][i]['name']+"**, "
	msg+="\nYou can choose a costume by letter, name, number, or hitting the corresponding react button below. Ex. `"+doll['name']+", A` or `"+doll['name']+", "+doll['costumes'][1]['name']+"`"
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
				
				if RepresentsInt(costumeType):
					print("chr was already a number, no remapping.")
					i = int(costumeType)
				else:
					print("Remapped chr to int.")
					i = ord(costumeType.upper())-65
				
				if i < len(doll['costumes']) and i >= 0:
					return doll['name'] + ": "+doll['costumes'][i]['name']+"\n"+PIC_DOMAIN+doll['costumes'][i]['pic']
				else:
					print("chr/int was too high or too low. "+str(i)+" "+costumeType)
					return "Parameter is more than the number of costumes in this T-Doll."
			else:

				res = process.extract(costumeType, [costume['name'] for costume in doll['costumes']], limit=1)
				for costume in doll['costumes']:
					if costume['name'] == res[0][0]:
						return doll['name'] + ": "+costume['name']+"\n"+PIC_DOMAIN+costume['pic']
				#return doll['name'] + ": "+doll['costumes'][res[0][0]]['name']+"\n"+PIC_DOMAIN+doll['costumes'][res[0][0]]['pic']
			#print(costumeType + " not found in "+doll['name'])
			#return "Couldn't find that costume. "+getPossibleCostumes(doll)
			#return False
			#If we got here, search for the closest costume
		#else
		return doll['name'] + ":\n"+PIC_DOMAIN+doll['img']
	#else
	printWarn("T-Doll "+doll['name']+ " is missing image information.")
	if 'img' in doll:
		return "There are either no costumes for this T-Doll or the data is missing. Default art:"+doll['img']
	return "Sorry, either there are no images for this doll or the data is missing."
	#return False

@client.event
async def on_ready():
	print("The bot is ready!")
	#print(str(client.user.id))
	#https://discordapp.com/oauth2/authorize?client_id=351447700064960522&scope=bot&permissions=0
	#Send Messages, Manage Messages, Embed Links, and Add Reactions is required for optimal use.
	print("Add me with https://discordapp.com/oauth2/authorize?client_id="+client.user.id+ "&scope=bot&permissions=26688")
	await client.change_presence(game=discord.Game(name=serverCount()))

@client.event
async def on_server_join(server):
	await client.change_presence(game=discord.Game(name=serverCount()))

@client.event
async def on_server_remove(server):
	await client.change_presence(game=discord.Game(name=serverCount()))

#Behold, a stateless function by parsing my own messages
#You know what? It's better if it's stateless anyways
@client.event
async def on_reaction_add(reaction,user):
	#If the reaction added was by the bot itself
	if user == client.user:
		return
	#If the message that the reaction was added to is not a message this bot sent, return.
	if reaction.message.author != client.user:
		return
	msg = reaction.message.content.splitlines()
	
	#Don't do anything if this reaction is a custom emoji.
	if reaction.custom_emoji:
		return
	
	#Check if it's a search result
	#This is an example of how NOT to write a function
	if msg[0].startswith("No T-Doll was") and reaction.emoji in ['⏪','⏩']:
		dollList = msg[0].split(": ")[-1].split(", ")
		if len(reaction.message.embeds) < 1:
			printError("What? search result was not an embed.")
			return
		else:
			#print(reaction.message.embeds[0])
			curDollName = ' '.join(reaction.message.embeds[0]['title'].split(" - ")[1].split(' ')[:-1])
			print(curDollName)
			curIndex = 0
			for d in dollList:
				if curDollName == d:
					break;
				else:
					curIndex+=1
			print(str(curIndex)+ " "+dollList[curIndex])
			if reaction.emoji == "⏩" and curIndex+1 < len(dollList):
				curIndex+=1
			elif reaction.emoji == "⏪" and curIndex > 0:
				curIndex-=1
			else:
				return
			for doll in frontlinedex:
				if dollList[curIndex] == doll['name']:
					await client.edit_message(reaction.message,embed=dollInfo(doll))
					try:
						await client.clear_reactions(reaction.message)
						for e in ['⏪','⏩']:
							try:
								await client.add_reaction(reaction.message,e)
							except:
								print("Missing manage messages permissions...")
					except:
						print("Missing manage messages permissions...")
					return
	
	#lame hack to check if it's a --list result
	#We check backwards becuse the "No T doll was found blah blah" message might appear
	elif msg[-2].startswith("Costumes for"):
		#print(msg[0].split(":")[0])
		name = msg[-2].split(":")[0][(len("Costumes for")+1):]
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
	elif msg[-1].endswith(".png") and reaction.emoji == "🔥":
		name,costume = msg[-2].split(":")
		
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
	#Lame hack to check if this is an equipment result
	elif 'exclusive equipment' in msg[0] and '(' in msg[-1]:
		#Found 2 exclusive equipment for HK416: EOT XPS3, Tactical Headband
		# -> ['EOT XPS3', 'Tactical Headband']
		selection = intTryParse(msg[-1][1:].split("/")[0])
		equipmentList = msg[0].split(": ")[-1].split(", ")
		if reaction.emoji == '⏪' and selection > 1:
			selection -= 1
		elif reaction.emoji == '⏩' and selection < len(equipmentList):
			selection += 1
		else:
			#Just do nothing
			return
		#else:
		#	print("Tried changing equipment selection but the selection is unknown/invalid?")
		#	print("Selection: "+ str(selection))
		#	print("Reaction: "+reaction.emoji)
		#	print(equipmentList)
		#	print("Msg:\n" + reaction.message.content)
		#	return
		for equip in equipmentdex:
			if equipmentList[selection-1] == equip['name']:
				newMsg = msg[0] + "\n("+str(selection)+"/"+str(len(equipmentList))+")"
				await client.edit_message(reaction.message,new_content=newMsg, embed=equipInfo(equip))
				try:
					await client.clear_reactions(reaction.message)
					for e in ['⏪','⏩']:
						try:
							await client.add_reaction(reaction.message,e)
						except:
							print("Missing manage messages permissions...")
				except:
					print("Missing manage messages permissions...")
				return
		printError("WTF? Can't find equipment!")
		printError("Selection: "+ str(selection))
		printError("Reaction: "+reaction.emoji)
		print(equipmentList)
		printError("Msg:\n" + reaction.message.content)
	else:
		printWarn("Someone reacted on a message the bot posted, but there's nothing for the bot to handle?")
		printWarn("User reacted with " +reaction.emoji)
		printWarn("==MESSAGE CONTENT==")
		printWarn(reaction.message.content)
		printWarn("==END CONTENT==")
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
	
	command = None
	param = None
	if message.content.startswith(COMMAND_PREFIX):
		print(message.content)
		a = message.content.split(" ")
		#print(a)
		command = a[0][len(COMMAND_PREFIX):]
		if len(a) > 1:
			#This is just a really fucked up way of combining it back into a string without the command in the params
			param = " ".join([i.lower() for i in a[1:]])
	else:
		return
	
	#print(command)
	if command == "status":
		st = "Running "+version+"\n"
		st += serverCount()
		#st += "\n"+str(len(frontlinedex))+" dolls indexed (incl. MOD variants & 1 kalina)"
		numDolls = 0
		numMods = 0
		for d in frontlinedex:
			if 'mod' in d:
				numMods+=1
			else:
				numDolls+=1
		st+="\n"+str(numDolls)+" dolls indexed (incl. NPCs). "+str(numMods/3)+" MODs indexed. (MOD1/2/3 counted as one MOD)"
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
			#print(time_list)
			st += "\nThe T-Doll with the shortest production time is "+time_list[0][0] + " with a timer of "+time_list[0][1]+"."
			st += "\nThe T-Doll with the longest production time is "+time_list[-1][0] + " with a timer of "+time_list[-1][1]+"."
		#Because it's cool and it's not that expensive
		type_list = {}
		for doll in frontlinedex:
			if doll['type'] not in type_list:
				type_list[doll['type']] = 0
			type_list[doll['type']]+=1
		st += "\n__Number of dolls per type:__"
		for type in type_list:
			st += "\n**"+type+":** "+str(type_list[type])
		
		await client.send_message(message.channel, st)
		#print("Attempting to change the status to " + st)
		#await client.change_presence(game=discord.Game(name="testing"))
		#print("done")
		return
	elif command == "help" or command == "h":
		if param != None:
			if param == "image":
				msg = "**Summary:**\nSearch doll images and costumes. This command is in beta. Changing costumes with reaction buttons coming eventually.\n"
				msg += "**Detailed Usage:**\n"
				msg += "Press the fire react to show damage art for a doll. Remove the fire react to show normal art.\n"
				msg += "Costumes are ordered from A to the number of costumes, with damage art coming after regular art. A is always default and B is always default damaged. If doll has a MOD 3 costume, C and D are MOD 3 and MOD 3 damaged.\n"
				msg += "You can spell costumes wrong and still get the closest result.\n"
				msg += "You can append the '--list' or '-l' flag to the end of your search to show all the costume names.\n"
				msg += "**Examples:**\n"
				msg += "`"+COMMAND_PREFIX+"image UMP45`: Show UMP45's default costume.\n"
				msg += "`"+COMMAND_PREFIX+"image Skorpion, Crimson Starlet`: Show Skorpion's Crimson Starlet costume.\n"
				msg += "`"+COMMAND_PREFIX+"image UMP9,B`: Show UMP9's damaged art, which is the second costume in the list.\n"
				msg += "`"+COMMAND_PREFIX+"image M16A1,C`: Show M16A1's 3rd costume.\n"
				msg += "`"+COMMAND_PREFIX+"image Negev --list`: Show all available costumes for Negev.\n"
				msg += "You can also use numbers instead of letters. Ex. `"+COMMAND_PREFIX+"image UMP9,2`\n"
				await client.send_message(message.channel, msg)
			elif param == "timer":
				msg = "Find a matching doll or equip for the timer. Fairies coming eventually.\n"
				msg += "Usage examples:\n"
				msg += "`"+COMMAND_PREFIX+"timer 0:40` or `"+COMMAND_PREFIX+"timer :40`: Search for a matching timer of 0 hours 40 mins\n"
				msg += "`"+COMMAND_PREFIX+"timer 8:00` or `"+COMMAND_PREFIX+"timer 08:00` or `"+COMMAND_PREFIX+"timer 08:00:00`: Search for a matching timer of 8 hours\n"
				await client.send_message(message.channel, msg)
			elif param == "status":
				msg = "Show the amount of servers this bot is in and the number of dolls and equipment indexed."
				#msg += "\nIf --extra is appended the lowest and highest production timers for weapons and dolls will be shown."
				msg += "\nAlso shows the number of dolls in each type (HG,SMG,AR,SG,RF)."
				await client.send_message(message.channel, msg)
			elif param == "exp":
				msg = "Estimate how much exp is required to get from one level to another."
				msg += "\nExample: `"+COMMAND_PREFIX+"exp 5,25`: Estimate how much exp and combat reports it takes to get from level 5 to 25."
				msg += "\nExample: `"+COMMAND_PREFIX+"exp 75`: Estimate how much exp and combat reports it takes to get from level 1 to 75."
				await client.send_message(message.channel,msg)
			elif param == "equip":
				msg = "Search for equipment or fairies. If you search a doll's name, it will return the exclusive equipment for that doll."
				msg += "\nExample: `"+COMMAND_PREFIX+"equip Additional Process Module`: Returns information on the 'Additional Process Module' equipment."
				msg += "\nExample: `"+COMMAND_PREFIX+"equip HK416`: Returns HK416's exclusive equipment. You can switch results with the react buttons."
				await client.send_message(message.channel, msg)
			else:
				printWarn("Tried to get help for "+param+ " but there was none.")
				await client.send_message(message.channel, "No help available for this command yet.")
			return
		msg = "I am I.O.P., a Discord bot that will give you useful information about T-Dolls and equipment.\n"
		msg+="Running version "+version+"\n"
		msg+= "Commands:\n**"+COMMAND_PREFIX+"search / "+COMMAND_PREFIX+"s**: Search a T-Doll and display all information. Example: `"+COMMAND_PREFIX+"search UMP45`\n"
		msg+="**"+COMMAND_PREFIX+"search2**: The same as above but the message will be text instead of an embed. Example: `"+COMMAND_PREFIX+"search2 UMP9`\n"
		msg+="**"+COMMAND_PREFIX+"equip / "+COMMAND_PREFIX+"e**: Search an equipment or fairy. **This command is in beta, some information is still missing.** Example: `"+COMMAND_PREFIX+"equip Armor Fairy`\n"
		msg+="**"+COMMAND_PREFIX+"image / "+COMMAND_PREFIX+"i:** Search a T-Doll's image and display it, or search a doll's costume. Check this command's help for more information. Example: `"+COMMAND_PREFIX+"image UMP40`, `"+COMMAND_PREFIX+"image M16A1,Boss`\n"
		if quotedex:
			msg+="**"+COMMAND_PREFIX+"quote / "+COMMAND_PREFIX+"q:** List all the quotes for a doll. If the command doesn't fail, that is.\n"
		msg+="**"+COMMAND_PREFIX+"timer / "+COMMAND_PREFIX+"t:** List T-Dolls or equipment that match the production timer. Ex. `"+COMMAND_PREFIX+"timer 8:10` or `"+COMMAND_PREFIX+"timer 0:40`\n"
		msg+="**"+COMMAND_PREFIX+"status:** See diagnostic information like the amount of dolls indexed, number of discords, etc\n"
		msg+="**"+COMMAND_PREFIX+"exp:** Estimate how much exp is required to get from one level to another. Ex. `"+COMMAND_PREFIX+"exp 100,115`\n"
		msg+="**"+COMMAND_PREFIX+"help / "+COMMAND_PREFIX+"h:** You're looking at it.\n"
		msg+="For advanced help, do `"+COMMAND_PREFIX+"help <short name of command>`. Example: `"+COMMAND_PREFIX+"help image`, `$gfhelp quote`\n\n"
		msg+="Invite: Check github page\n"
		msg+="Github: https://github.com/RhythmLunatic/Girls-Frontline-Discord-Search\n"
		msg+="Contact: /u/RhythmLunatic on Reddit or RhythmLunatic on Github\n"
		msg+="The information in this bot is Ⓒ en.gfwiki.com and licenced under CC BY-SA 3.0. Support the wiki!\n"
		msg+="Girls Frontline Discord Search is licenced under AGPLv3. Support free and open source software!"
		await client.send_message(message.channel, msg)
		return
	
	#All commands below this require a parameter.
	if param == None:
		#await client.send_message(message.channel, "This command requires a parameter.")
		print("Tried using a command without a parameter?")
		return

	if command == "search" or command == "s":
		print("[SEARCH] "+param)

		doll, res = getSearchResult(param)
		embed = dollInfo(doll)

		try:
			if res:
				msg = await client.send_message(message.channel, content="No T-Doll was found with that exact name, so I'm returning the closest result. Did you mean: "+", ".join([i[0] for i in res]), embed=embed)
				for e in ['⏪','⏩']:
					try:
						await client.add_reaction(msg,e)
					except:
						print(e+" is not a valid emoji")
			else:
				await client.send_message(message.channel, embed=embed)
		except Exception as e:
			#await client.send_message(message.channel, content="An error occured and I am unable to complete your request. Perhaps you have embed permissions turned off?")
			#print("An error occured. Here is the affected doll:")
			#print(doll)
			#I don't really want this to be a warn because someone could keep embed permissions off and spam it but whatever
			printWarn("Exception occured trying to send the message, probably missing embed permissions.")
			print(e)
			try:
				msg = "You are currently looking at a simplified view because embed permissions are turned off. Please turn them on, or if you always want a simplified view use search2. Most commands will not work with embeds turned off!\n"
				msg += embed2text(embed)
				await client.send_message(message.channel, content=msg)
			except Exception as e:
				printError("Tried to send message twice and failed, giving up. Here is the affected doll:")
				print(doll)
		return
	elif command == "search2":
		doll, res = getSearchResult(param)
		embed = dollInfo(doll)
		await client.send_message(message.channel, content=embed2text(embed))
		
	elif command == "equip" or command == "e":
		print("[EQUIP] "+param)
		#Check if they searched a doll's name. Only match exact names.
		for doll in frontlinedex:
			#If we got here, they searched a doll's name.
			if param == doll['name'].lower() or ('alias' in doll and param == doll['alias'].lower()):
				#Add each exclusive equipment to this array, since there might be multiple exclusives.
				equipmentResults = []
				for equip in equipmentdex:
					if 'valid' in equip and param in equip['valid'].lower():
						equipmentResults.append(equip)
				if len(equipmentResults) == 0:
					await client.send_message(message.channel, content="Found no exclusive equipment for "+doll['name']+". (If this is wrong, please file a bug report)")
				elif len(equipmentResults) > 1:
					msgText = "Found "+str(len(equipmentResults))+" exclusive equipment for "+doll['name']+": " + ", ".join([e['name'] for e in equipmentResults])
					msgText += "\n(1/"+str(len(equipmentResults))+")"
					msg = await client.send_message(message.channel, content=msgText, embed=equipInfo(equipmentResults[0]))
					#Yes I know you don't need to show the back button when it's the first selection but it's simpler this way
					for e in ['⏪','⏩']:
						try:
							await client.add_reaction(msg,e)
						except:
							print(e+" is not a valid emoji")
				else:
					await client.send_message(message.channel, content="Found 1 exclusive equipment for "+doll['name']+".",embed=equipInfo(equipmentResults[0]))
				return
		try:
			equip, res = getSearchResult(param,True)
			embed = equipInfo(equip)
			if res[0][1] == 100:
				await client.send_message(message.channel, embed=embed)
			else:
				await client.send_message(message.channel, content="No equipment was found with that exact name, so I'm returning the closest result. Did you mean: "+", ".join([i[0] for i in res]), embed=embed)
		except Exception as e:
			await client.send_message(message.channel, content="An error has occured while trying to get equipment data. Perhaps the data for this equipment is missing.")
			print(traceback.print_exc())
			printWarn(embed2text(equipInfo(equip)))
		return
	elif command == "image" or command == "i":
		param = param.split(",")
		#print("[IMAGE] "+param)
		costumeType = False
		if len(param) > 1:
			costumeType = param[-1].strip()
		param = param[0]
		#As dumb as it is, this sets --list param because the below code searches the doll
		if param.split(" ")[-1] == "--list" or param.split(" ")[-1] == "list" or param.split(" ")[-1] == "-l":
			param = " ".join(param.split(" ")[:-1])
			costumeType = "--list"
		print("[IMAGE] " +param + ", " +str(costumeType))
		doll, res = getSearchResult(param)
		msgText = ""
		if res:
			msgText = "No T-Doll was found with that name, so I'm returning the closest result. Did you mean: "+", ".join([i[0] for i in res]) + "\n"
		if costumeType == "--list" or costumeType == "-l":
			if 'costumes' in doll:
				msgText += getPossibleCostumes(doll)
				msg = await client.send_message(message.channel, msgText)
				#ord starts at 127462 btw
				emojis = ["🇦","🇧","🇨","🇩","🇪","🇫","🇬","🇭","🇮","🇯","🇰","🇱","🇲","🇳","🇴","🇵","🇶","🇷","🇸","🇹"]
				
				#Do whatever is lower, the number of costumes or the emojis. G36 has 20 costumes right now (ignoring my broken parser) but she might have more in the future and you can't put that many emoji in.
				#20 = the number of emoji discord will let you add to a message.
				for i in range( min( len(doll['costumes']), 20 ) ):
					try:
						await client.add_reaction(msg,emojis[i])
					except:
						print(emojis[i]+" is not a valid emoji or you put too many emojis on")
			else:
				printWarn("T-Doll "+doll['name']+" is missing costume information.")
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
	elif command == "timer" or command == "t":
		print("[TIMER] "+param)
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
		#Speedup: Only search equipment if the time is <1 hour or searching a Fairy.
		if int(param.split(':')[0]) == 0 or 'fairy' in param:
			equipRes = []
			for equip in equipmentdex:
				if 'production' in equip and 'timer' in equip['production']:
					if param == equip['production']['timer']:
						equipRes.append(equip)
			#We have to do the doll search afterwards, though!
			for doll in frontlinedex:
				if 'production' in doll and 'timer' in doll['production']:
					if param == doll['production']['timer']:
						res.append(doll)
			
			if len(equipRes) == 0 and len(res) == 0:
				await client.send_message(message.channel, "No equipment or T-Doll was found matching that production timer.")
				print("No match found for "+param)
			elif len(equipRes) == 1 and len(res) == 0:
				await client.send_message(message.channel, content="Found an exact match for the timer.", embed=equipInfo(equipRes[0]))
			elif len(equipRes) == 0 and len(res) == 1:
				await client.send_message(message.channel, content="Found an exact match for the timer.", embed=dollInfo(res[0]))
			else:
				msg = "Equipment that matches this production timer: "+", ".join(i['name'] for i in equipRes)
				msg += "\nT-Dolls that match this production timer: "+", ".join(i['name']+" ("+i['type']+" "+num2stars(i['rating']) +")" for i in res)
				await client.send_message(message.channel, msg)
			return
			

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
	elif command == "quote" or command == "q":
		if quotedex:
			print("[QUOTE] "+param)
			doll, res = getSearchResult(param)
			if 'internalName' in doll:
				if doll['internalName'] in quotedex:
					msg = doll['name']+"'s quotes:\n"
					for key,value in sorted(quotedex[doll['internalName']].items()):
						msg += "**"+key.capitalize()+"**: "+" ".join(value)+"\n"
					await client.send_message(message.channel, msg)
				else:
					await client.send_message(message.channel, "This doll has no quotes... Somehow.")
					printWarn(doll['name']+" with internalName "+doll['internalName']+ " has no quotes.")
			else:
				printWarn("T-Doll "+doll['name']+" is missing the internal name.")
				await client.send_message(message.channel, "Sorry, the internal name for this doll is missing, which is needed to pull the quote from the data.")
			return
		else:
			await client.send_message(message.channel, "This command is unavailable. If you are the bot owner, check https://github.com/RhythmLunatic/Girls-Frontline-Discord-Search for instructions.")
	elif command == "exp":
		print("[EXP] "+param)
		start = None
		end = None
		try:
			#some people try $gfexp 100 120 so just accept both
			#if param was $gfexp 100, nothing to split
			param = param.replace(" ",",")
			if ',' in param:
				start,end=param.split(",")
				start = intTryParse(start.strip())
			else:
				start = 1
				end = param
			
			end = intTryParse(end.strip())
			if start == -1 or end == -1:
				await client.send_message(message.channel,"1st or 2nd argument was not a number. Use this command like: `"+COMMAND_PREFIX+"exp 5,100` (where 5 is start, 100 is end)")
				return
		except Exception:
			#await client.send_message(message.channel, "An error has occured and I am unable to complete your request. Perhaps your argument was malformed.")
			await client.send_message(message.channel,"parameter was invalid. Use this command like:\n `"+COMMAND_PREFIX+"exp 5` (where 5 is end)\n`"+COMMAND_PREFIX+"exp 100,120` (where 100 is start and 120 is end)")
			printWarn("Invalid argument for gfexp.")
			print(traceback.print_exc())
		#else:
		#	start = 1
		#	end = intTryParse(param)
		#	if end == -1:
		#		await client.send_message(message.channel,"parameter was not a number. Use this command like: `"+COMMAND_PREFIX+"exp 5` (where 5 is end)")
		#		return
		
		if end > len(exp_table):
			await client.send_message(message.channel,"Calculations for levels above "+str(len(exp_table))+" are not supported.")
			return
		n = 0
		for i in range(start-1,end-1):
			n+=exp_table[i]
		msg =  "Exp required to go from level " + str(start) + " to level "+str(end) + ": **"+str(n)+"**\n"
		msg += "Combat reports required: **"+str(math.ceil(n/3000))+"**"
		await client.send_message(message.channel,msg)
		return
			
#startup...
print("Starting up I.O.P. version "+version+"...")
print("Discord.py version is "+discord.__version__)
print("Reading the frontlinedex into memory. This may take a while.")
with open("girlsfrontline.json", "r") as file_obj:
	frontlinedex = json.loads(file_obj.read())
print("Reading bonus information...")
with open("gf_flavortext.json", "r") as file_obj:
	bonusdex = json.loads(file_obj.read())
if os.path.isfile("NewCharacterVoice.json"):
	print("Reading quotes.")
	with open("NewCharacterVoice.json", "r") as file_obj:
		quotedex = json.loads(file_obj.read())
	print(COMMAND_PREFIX+"quote is now available!")

print("Injecting aliases into the frontlinedex and quotes into the quotedex...")
for doll in frontlinedex:
	if doll['name'] in bonusdex:
		if 'alias' in bonusdex[doll['name']]:
			doll['alias'] = bonusdex[doll['name']]['alias']
		'''
		To inject, a lot of checks are needed.
		1. quotes must be loaded.
		2. doll must have a quotes key in the bonusdex.
		3. doll must have its internal name, since the quotedex works by internal names.
		'''
		if quotedex and 'quotes' in bonusdex[doll['name']] and 'internalName' in doll:
			quotedex[doll['internalName']] = bonusdex[doll['name']]['quotes']

	

#for doll in frontlinedex:
#	if doll['name'] == "Five-seveN":
#		assert doll['alias'], "Missing aliases!"

print("Reading equipment data into memory. This may take a while.")
file_obj = open("equipment.json", "r")
equipmentdex = json.loads(file_obj.read())
file_obj.close()

print("Done! Now logging in...")
client.run(DISCORD_TOKEN)
