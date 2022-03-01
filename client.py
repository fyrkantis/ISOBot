from Modules import dateModule, inputModule, textModule, unitModule

# External Libraries
import os
from discord import Client, Embed, File, Activity, ActivityType, errors
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD = os.getenv("DISCORD_GUILD")
ID = os.getenv("DISCORD_ID")
client = Client()

@client.event
async def on_ready():
	print(f"{client.user} has connected to Discord!")
	servers = await client.fetch_guilds().flatten()
	ids = []
	send = f"Currently connected to {len(servers)} servers: \""
	for i in range(len(servers)):
		ids.append(servers[i].id)
		send += servers[i].name
		send += "#"
		send += str(servers[i].id)
		if i < len(servers) - 2:
			send += "\", \""
		elif i == len(servers) - 2:
			send += "\" and \""
		else:
			send += "\"."
	print(send)
	inputModule.addSlashCommands(client, ids)
	print("Successfully added slash commands.")
	status = " you, use ISO-8601."
	activity = ActivityType.watching
	await client.change_presence(activity = Activity(name = status, type = activity))
	print(str(activity) + status)

@client.event
async def on_message(message):
	if not message.author.bot:
		foundDates = dateModule.pattern.findall(message.content)
		foundUnits = unitModule.getFindPattern().findall(message.content)
		foundIso = False
		if len(foundDates) > 0 or len(foundUnits) > 0:
			print(f"{message.created_at}, #{message.channel.name} in \"{message.channel.guild.name}\" by {message.author}: {message.content}")
			async with message.channel.typing():
				dateIso = dateModule.DateFormat.Iso()
				dates = []
				for date in foundDates:
					toAdd = dateModule.DateFormat(date)
					print(toAdd, end = " ")
					if toAdd.iso:
						foundIso = True
						print("ISO format.")
						continue
					if toAdd.definetlyDate == False:
						print("Definitively not a date.")
						continue
					if toAdd.definetlyDate is None:
						print("Maybe not a date.")
						continue
					print("Wrong format")
					dateIso += toAdd.iso
					dateIso.order = dateIso.order and toAdd.iso.order
					dates.append(toAdd)
				
				unitIso = unitModule.BaseUnit.Iso()
				units = []
				for unit in foundUnits:
					toAdd = unitModule.Unit(unit)
					print(toAdd, end = " ")
					if toAdd.iso:
						foundIso = True
						print("ISO unit.")
						continue
					if len(toAdd.subUnits) <= 0:
						print("Not a unit.")
						continue
					print("Wrong unit."
					)
					unitIso += toAdd.iso
					units.append(toAdd)
				
				if len(dates) > 0 or len(units) > 0:
					if len(dates) <= 0:
						dateIso.order = True # Hotfix
					
					sentence = textModule.Sentence(message)
					embed = Embed(title = sentence.title(), description = sentence.subtitle(dateIso, unitIso), color = 0xe4010c)
					file = File("Assets/warning.png", filename="warning.png")
					embed.set_thumbnail(url="attachment://warning.png")

					for date in dates:
						embed.add_field(name = f"**{date.write()}**", value = sentence.dateAnalysis(date), inline = False)

					for unit in units:
						embed.add_field(name = f"**{unit.rawInput}**", value = sentence.unitAnalysis(unit), inline = False)
					
					embed.set_footer(text = sentence.footer(), icon_url = "https://cdn.discordapp.com/avatars/796794008172888134/6b073c408aa584e4a03d7cfaf00d1e66.png") # TODO: Test stability.
					await message.reply(file = file, embed = embed)
					print("")
				elif foundIso:
					await message.add_reaction("✅")
					print("Date is ISO-8601 compliant.\n")

try:
	client.run(TOKEN)
except errors.HTTPException as e:
	print(f"Tried to run client but received \"{e}\" from discord:")
	print(f"Response: {e.response}")
#https://stackoverflow.com/questions/67268074/discord-py-429-rate-limit-what-does-not-making-requests-on-exhausted-buckets
#{e.response['message']}
#Time left: {e.response['retry_after']}
#Global rate limit: {e.response['global']}""")