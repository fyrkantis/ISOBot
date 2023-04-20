from Modules import dateModule, textModule, inputModule

# External Libraries
import os
from discord import Client, Intents, Embed, File, Status, Activity, ActivityType, errors
from dotenv import load_dotenv

def userOnline(guild, id):
	member = guild.get_member(id)
	if member is None:
		return False
	return member.status == Status.online

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = Intents.default()
intents.messages = True
intents.message_content = True
client = Client(intents = intents)

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
	print(":)")

@client.event
async def on_message(message):
	#if userOnline(message.guild, 732228885739077632):
	#	print("ISO Bot Experimental is already online here.")
	#	return
	if not message.author.bot:
		foundDates = dateModule.pattern.findall(message.content)
		foundIso = False
		if len(foundDates) > 0:
			print(f"{message.created_at}, #{message.channel.name} in \"{message.channel.guild.name}\" by {message.author}: {message.content}")
			async with message.channel.typing():
				dateIso = dateModule.DateFormat.Iso()
				dateIso.order = True # Assumes order is correct.
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
				
				if len(dates) > 0:
					sentence = textModule.Sentence(message)
					embed = Embed(title = sentence.title(), description = sentence.subtitle(dateIso), color = 0xe4010c)
					file = File("Assets/warning.png", filename="warning.png")
					embed.set_thumbnail(url="attachment://warning.png")

					for date in dates:
						embed.add_field(name = f"**{date.write()}**", value = sentence.dateAnalysis(date), inline = False)
					
					embed.set_footer(text = sentence.footer(), icon_url = "https://cdn.discordapp.com/avatars/796794008172888134/6b073c408aa584e4a03d7cfaf00d1e66.png") # TODO: Test stability.
					await message.reply(file = file, embed = embed)
					print("")
				elif foundIso:
					await message.add_reaction("✅")
					print("Date is ISO-8601 compliant.\n")
	elif message.author.id == 1098255899165990973 and "iso" in message.content.lower():
		sentence = textModule.Sentence(message)
		await message.reply(sentence.insult())
	

try:
	client.run(TOKEN)
except errors.HTTPException as e:
	print(f"Tried to run client but received \"{e}\" from discord:")
	print(f"Response: {e.response}")
#https://stackoverflow.com/questions/67268074/discord-py-429-rate-limit-what-does-not-making-requests-on-exhausted-buckets
#{e.response['message']}
#Time left: {e.response['retry_after']}
#Global rate limit: {e.response['global']}""")