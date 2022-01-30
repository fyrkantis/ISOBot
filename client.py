from Modules import dateModule, inputModule, textModule, unitModule

# External Libraries
import os
import discord

from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD = os.getenv("DISCORD_GUILD")
ID = os.getenv("DISCORD_ID")

class MyClient(discord.Client):
	async def on_ready(self):
		print(f"{self.user} has connected to Discord!")
		servers = await self.fetch_guilds().flatten()
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
		inputModule.addSlashCommands(self, ids)
		print("Successfully added slash commands.")
	
	async def on_message(self, message):
		if not message.author.bot:
			foundDates = dateModule.pattern.findall(message.content)
			foundUnits = unitModule.generatePattern().findall(message.content)
			foundIso = False
			if len(foundDates) > 0 or len(foundUnits) > 0:
				print(f"{message.created_at}, #{message.channel.name} in \"{message.channel.guild.name}\" by {message.author}: {message.content}")
				print(foundDates)
				dates = []
				for date in foundDates:
					toAdd = dateModule.DateFormat(date)
					print(toAdd, end = " ")
					if toAdd.iso:
						foundIso = True
						print("ISO format.")
						continue
					if len(toAdd.alternatives) <= 0:
						print("Definitively not a date.")
						continue
					if len(toAdd.tags) <= 2 and not (["Mon"] in toAdd.tags or ["Month" in toAdd.tags]): # TODO: Replace with less jank solution that actually works.
						print("Maybe not a date.")
						continue
					print("Wrong format")
					dates.append(toAdd)
				units = []
				for unit in foundUnits:
					toAdd = unitModule.Unit(unit)
					print(toAdd, end = ": ")
					if toAdd.iso:
						foundIso = True
						print("ISO unit.")
						continue
					if toAdd.unitType is None:
						print("Not a unit.")
						continue
					print("Wrong unit.")
					units.append(toAdd)
				
				if len(dates) > 0 or len(units) > 0:
					sentence = textModule.Sentence(message)
					embed = discord.Embed(title = sentence.title(), description = sentence.subtitle(), color = 0xe4010c)
					file = discord.File("Assets/warning.png", filename="warning.png")
					embed.set_thumbnail(url="attachment://warning.png")

					for date in dates:
						embed.add_field(name = f"**{date.write()}**", value = sentence.dateAnalysis(date), inline = False)

					for unit in units:
						embed.add_field(name = f"**{unit.write()}**", value = sentence.unitAnalysis(unit), inline = False)
					
					embed.set_footer(text = sentence.footer(), icon_url = "https://cdn.discordapp.com/avatars/796794008172888134/6b073c408aa584e4a03d7cfaf00d1e66.png?size=256") # TODO: Test stability.
					await message.reply(file = file, embed = embed)
					print("")
				elif foundIso:
					await message.add_reaction("✅")
					print("Date is ISO-8601 compliant.\n")

client = MyClient()

try:
	client.run(TOKEN)
except discord.errors.HTTPException as e:
	print(f"Tried to run client but received \"{e}\" from discord:")
	print(f"Response: {e.response}")
#https://stackoverflow.com/questions/67268074/discord-py-429-rate-limit-what-does-not-making-requests-on-exhausted-buckets
#{e.response['message']}
#Time left: {e.response['retry_after']}
#Global rate limit: {e.response['global']}""")