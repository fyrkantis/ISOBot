from discord.flags import fill_with_flags, flag_value
from Modules import dateModule, dataModule, textModule

# External Libraries
import os
import re
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
		send = f"Currently connected to {len(servers)} servers: \""
		for i in range(len(servers)):
			send += servers[i].name
			send += "#"
			send += str(servers[i].id)
			if i < len(servers) - 2:
				send += "\", \""
			elif i == len(servers) - 2:
				send += "\" and \""
			else:
				send += "\".\n"
		print(send)
	
	async def on_message(self, message):
		if not message.author.bot:

			dateFormats = []
			whole = re.findall("(?<!([\\d\\w\\+\\*=\\/\\\\-]))(((\\/|\\\\|\\-|^) *)?(((year|month) *)?((\\d{2,4}|[1-9]) *((st|nd|rd|th) *,? *)?|(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\\w* *,? *)((month|year|of))*(\\/|\\\\|\\-| ) *){1,2}(((\\d{2,4}|[1-9])( *(st|nd|rd|th)(\\s|$))?|(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\\w*))( *(\\/|\\\\|\\-|$))?)(?!([\\d\\w\\+\\*=\\/\\\\-]))", message.content, re.I)
			if len(whole) > 0:
				print(f"{message.created_at}, #{message.channel.name} in \"{message.channel.guild.name}\" by {message.author}: {message.content}")
			
			for i in range(len(whole)):
				toAdd = dateModule.DateFormat(whole[i][1])
				print(toAdd)
				if not toAdd.iso:
					dateFormats.append(toAdd)
			
			if len(dateFormats) > 0:
				sentence = textModule.Sentence(message)
				embed = discord.Embed(title = sentence.title(), description = sentence.subtitle(), color = 0xe4010c)
				file = discord.File("Assets/warning.png", filename="warning.png")
				embed.set_thumbnail(url="attachment://warning.png")

				for dateFormat in dateFormats:
					embed.add_field(name = "**" + dateFormat.writeFormat() + "**", value = sentence.generate(dateFormat), inline = False)
				
				embed.set_footer(text = sentence.footer(), icon_url = "https://cdn.discordapp.com/avatars/796794008172888134/6b073c408aa584e4a03d7cfaf00d1e66.png?size=256") # TODO: Test stability.
				await message.reply(file = file, embed = embed)
				print("")
			elif len(whole) > 0:
				await message.add_reaction("✅")
				print("Date is ISO-8601 compliant.\n")

client = MyClient()
client.run(TOKEN)