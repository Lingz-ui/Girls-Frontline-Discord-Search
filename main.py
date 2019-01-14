import discord
import json
import re

client = discord.Client()
DISCORD_TOKEN="your_key_here"
SITE_DOMAIN = "https://en.gfwiki.com"
gfcolors = [0, 0, 0xffffff, 0x6bdfce, 0xd6e35a, 0xffb600, 0xdfb6ff]
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

@client.event
async def on_ready():
	print("The bot is ready!")
	await client.change_presence(game=discord.Game(name="I'm a specialist!"))

@client.event
async def on_message(message):
	if message.author == client.user:
		return
	if message.content.startswith("$gfsearch2 "):
		#The string "$gfsearch2 " is 11 characters, so cut it off
		param = message.content[11:].lower()
		print(param)
		#await client.send_message(message.channel, "World")
		for doll in frontlinedex:
			if param == doll['name'].lower():
				embed = discord.Embed(title="No."+str(doll["num"])+" - "+ doll['name'] + " " + num2stars(doll['rating']), url=SITE_DOMAIN+doll['url'], color=gfcolors[doll['rating']])
				embed.add_field(name="Type", value=doll['type'], inline=True)
				#{ "hp" : 40, "ammo": 10, "ration": 10, "dmg": 12, "acc": 6, "eva": 9, "rof": 31, "spd": 15, "armor": 0, "crit_rate": 20, "crit_dmg": 50, "pen": 10},
				embed.add_field(name="Base Stats", value="HP: "+str(doll['baseStats']['hp']) + ", DMG: " + str(doll['baseStats']['dmg']) + ", ACC: " + str(doll['baseStats']['acc']) + ", EVA: " + str(doll['baseStats']['eva']) + ", ROF: " + str(doll['baseStats']['rof']))
				embed.add_field(name="Max Stats", value="HP: "+str(doll['maxStats']['hp']) + ", DMG: " + str(doll['maxStats']['dmg']) + ", ACC: " + str(doll['maxStats']['acc']) + ", EVA: " + str(doll['maxStats']['eva']) + ", ROF: " + str(doll['maxStats']['rof']))
				obtain_info = ""
				if 'stage' in doll['production']:
					obtain_info += 'STAGE: ' + doll['production']['stage'] + "\n"
				if 'reward' in doll['production']:
					obtain_info += 'REWARD: ' + doll['production']['reward'] + "\n"
				if 'timer' in doll['production']:
					obtain_info += 'Production Timer: ' + doll['production']['timer']
				embed.add_field(name="How To Obtain", value=obtain_info,inline=False)
				if 'normal' in doll['production']:
					a = doll['production']['normal']
					f = "Manpower: "+str(a['manpower']) + " Ammo: " + str(a['ammo']) + " Rations: " + str(a['rations']) + " Parts: " + str(a['parts'])
					if doll['production']['placebo'] == True:
						f += "\n*Production requirements are placebo & may not increase drop rate"
					embed.add_field(name="Normal Production Requirement", value=f, inline=True)
				if 'heavy' in doll['production']:
					a = doll['production']['heavy']
					f = "Manpower: "+str(a['manpower']) + " Ammo: " + str(a['ammo']) + " Rations: " + str(a['rations']) + " Parts: " + str(a['parts'])
					embed.add_field(name="Heavy Production Requirement", value=f, inline=True)
				
				abilityText = doll['ability']['text']
				while True:
					searchObj = re.search("\(\$([^\)]+)\)", abilityText)
					if searchObj:
						key = searchObj.group()[2:-1]
						print("key: " + key)
						val = doll['ability'][key][-1]
						abilityText = abilityText.replace(searchObj.group(), val)
					else:
						break
				if 'cooldown' in doll['ability']:
					abilityText += "\nCooldown: " + str(doll['ability']['cooldown'][-1]) + " seconds"
				embed.add_field(name="Ability: "+doll['ability']['name'], value=abilityText, inline=False)
				
				embed.add_field(name="Tile Bonus", value=doll['tile_bonus'], inline=True)
				embed.add_field(name="Tile Bonus Ability", value=doll['bonus_desc'], inline=True)
				#embed.add_field(name="Tile Bonus Types", value=doll['bonus_type'], inline=True)
				embed.set_footer(text="Data is Ⓒ en.gfwiki.com and licenced under CC BY-SA 3.0.")
				await client.send_message(message.channel, embed=embed)
				return
			
		await client.send_message(message.channel, "No T-Doll was found with that name.")
		return
		
#startup...
print("Reading the frontlinedex into memory. This may take a while.")
file_obj = open("girlsfrontline.json", "r")
frontlinedex = json.loads(file_obj.read())
file_obj.close()
print("Done!")
client.run(DISCORD_TOKEN)
