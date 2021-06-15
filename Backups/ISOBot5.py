import os
import re
import math
import random
import discord

from dotenv import load_dotenv
from datetime import datetime
from calendar import monthrange

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD = os.getenv("DISCORD_GUILD")
ID = os.getenv("DISCORD_ID")

client = discord.Client()

months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

def writeList(items, inclusive = False):
	send = ""
	for i in range(len(items)):
		send += str(items[i])
		if i + 2 < len(items):
			send += ", "
		elif i + 2 == len(items):
			if inclusive:
				send += " and "
			else:
				send += " or "
	return send

def useFormat(inputs, lines):
	send = lines[0]
	for i in range(len(inputs)):
		send += inputs[i]
		send += lines[i + 1]
	return send


class Date():
	def __init__(self, tags, values, inputs = None):
		self.year = None
		self.yearLength = None
		self.month = None
		self.day = None

		for i in range(len(values)):
			if tags[i][0] == "Y":
				self.year = values[i]
				if inputs:
					self.yearLength = len(inputs[i])
				else:
					self.yearLength = len(str(self.year))
			elif tags[i][0] == "M":
				self.month = values[i]
			elif tags[i][0] == "D":
				self.day = values[i]
	
	def yearString(self):
		send = "X" * (4 - self.yearLength)
		send += "0" * (self.yearLength - len(str(self.year)))
		send += str(self.year)
		return send

	def isoString(self):
		send = ""
		if self.year:
			send += self.yearString()
			send += "-"
		send += '0' * (2 - len(str(self.month))) + str(self.month)
		if self.day:
			send += "-"
			send += '0' * (2 - len(str(self.day))) + str(self.day)
		return send
	
	def dateString(self):
		send = ""
		if self.day:
			send += str(self.day)
			if str(self.day)[-2:-1] != "1":
				last = str(self.day)[-1:]
				if last == "1":
					send += "st"
				elif last == "2":
					send += "nd"
				elif last == "3":
					send += "rd"
				else:
					send += "th"
			else:
				send += "th"
			send += " "
		send += months[self.month - 1]
		if self.year:
			send += " year "
			send += self.yearString()
		return send
	
	def __eq__(self, other):
		if isinstance(other, Date):
			if self.year == other.year and self.month == other.month and self.day == other.day:
				return True
		return False
	
	def __str__(self):
		return self.dateString()
	
	def __repr__(self):
		return self.isoString()

class DateFormat():
	class DateAlt():
		def __init__(self, date, tokens):
			self.date = date
			self.tags = [tokens]
		
		def __str__(self):
			return f"{self.date} (formatted as {writeList(self.tags)})"
		
		def __repr__(self):
			return str(self)

	# Takes date as string and analyzes it.
	def __init__(self, whole):
		parts = re.split("(\\d+|\\w+)", whole) 

		# Separates the date into separate parts.
		# TODO: Add error handling for weird parts lists lengths.
		index = 1
		while index < len(parts):
			if parts[index] == "st" or parts[index] == "nd" or parts[index] == "rd" or parts[index] == "th":
				parts[index] = "th"
				parts[(index - 1):(index + 2)] = ["".join(parts[(index - 1):(index + 2)])]

			elif parts[index] == "of" or parts[index] == "year" or parts[index] == "month":
				parts[(index - 1):(index + 2)] = ["".join(parts[(index - 1):(index + 2)])]

			else:
				index += 2
		
		# Trims ends.
		parts[0] = parts[0].lstrip()
		parts[-1] = parts[-1].rstrip()
		
		self.inputs = []
		self.values = []
		self.tags = []
		self.lines = []

		# Sorts parts into correct categories and labels them.
		for i in range(len(parts)):
			if i % 2 == 1:
				if parts[i].isnumeric():
					j = len(self.inputs)
					self.inputs.append(parts[i])
					self.values.append(int(parts[i]))

					# Figures out what the inputs could mean.
					self.tags.append(["Y" * len(parts[i])])

					if len(parts[i]) <= 2:
						if self.values[j] <= 31:
							if self.values[j] <= 12:
								self.tags[j].append("M" * len(parts[i]))
							self.tags[j].append("D" * len(parts[i]))
					
				else: # TODO: Add case for written "first", "second", and so on. (frst, scnd)
					for j in range(len(months)):
						if parts[i][:3].lower() == months[j][:3].lower():
							self.inputs.append(parts[i])
							self.values.append(j + 1)

							if len(parts[i]) <= 3:
								self.tags.append(["Mon"])
							else:
								self.tags.append(["Month"])
							break
			else:
				self.lines.append(parts[i])
		
		self.dateAlts = []

		# Tests possible combinations.
		# TODO: Optimization that removes duplicates of arrays with only one possibility in them.
		if len(self.tags) > 1:
			for first in self.tags[0]:
				for secnd in self.tags[1]:
					if len(self.tags) > 2:
						for third in self.tags[2]:
							if first[0] != secnd[0] and secnd[0] != third[0] and third[0] != first[0]:
								self.addAlt([first, secnd, third])
					else:
						if first[0] != secnd[0] and (first[0] == "M" or secnd[0] == "M"):
							self.addAlt([first, secnd])
		
		self.isoLevel = 0

		for i in range(len(self.dateAlts)): # TODO: Move to loop above.
			for j in range(len(self.dateAlts[i].tags)):
				tokens = self.dateAlts[i].tags[j]
				letters = []
				for k in range(len(tokens)):
					letters.append(tokens[k][0])
				if letters == ["Y", "M", "D"] or letters == ["Y", "M"] or letters == ["M", "D"]:
					if tokens == ["YYYY", "MM", "DD"] or tokens == ["YYYY", "MM"] or tokens == ["MM", ["DD"]]:
						ISOLines = True
						for line in self.lines[1:-1]:
							if line.strip() != "-":
								ISOLines = False
								break
						if ISOLines:
							self.dateAlts[i].tags[j].pop(k)
							if len(self.dateAlts[i].tags) == 0:
								self.dateAlts.pop(i)
							self.isoLevel = max(self.isoLevel, 3)
						else:
							self.isoLevel = max(self.isoLevel, 2)
					else:
						self.isoLevel = max(self.isoLevel, 1)
	
	def addAlt(self, tags):
		date = Date(tags, self.values, self.inputs)
		for i in range(len(self.dateAlts)):
			if self.dateAlts[i].date == date:
				self.dateAlts[i].tags.append(tags)
				return
		self.dateAlts.append(self.DateAlt(date, tags))
	
	def __str__(self):
		return f"Date consisting of lines: {self.lines} and inputs: {self.inputs}, translated into values: {self.values}, which could represent: {self.tags}.\nAll possible dates are: {self.dateAlts}, which gives the date a max ISO-8601 level of {self.isoLevel}."
	
	def __repr__(self):
		return "\n" + str(self) + "\n"

class Sentence():
	def generate(self, dateFormats):
		send = ""
		if len(dateFormats) == 1:
			send += "Found a date that isn't ISO-8601 compliant."
		else:
			send += "Found some dates that aren't ISO-8601 compliant."
		
		for i in range(len(dateFormats)):
			send += "\nYou wrote *\""
			send += useFormat(dateFormats[i].inputs, dateFormats[i].lines)
			send += "\"*"
			dateAlts = dateFormats[i].dateAlts
			if len(dateAlts) == 1:
				send += ", which must mean "
			else:
				send += ". This could mean anything between "
			for j in range(len(dateAlts)):
				dateAlt = dateAlts[j]
				send += "**"
				send += str(dateAlt.date)
				send += "** (formatted as "
				for k in range(len(dateAlt.tags)):
					send += "*"
					send += useFormat(dateAlt.tags[k], dateFormats[i].lines)
					send += "*"
					if k + 2 < len(dateAlt.tags):
						send += ", "
					elif k + 2 == len(dateAlt.tags):
						send += " or "
				send += ")"
				if len(dateAlts) == 1:
					send += ". This"
				else:
					send += ", which"
				send += " should be written *"
				send += dateAlt.date.isoString()
				send += "*"
				if j + 1 < len(dateAlts):
					send += "; "
			send += ". Fix this date by "
			if dateFormats[i].isoLevel == 0:
				send += "ordering the numbers correctly, as in year-month-day"
			elif dateFormats[i].isoLevel == 1:
				send += "writing the years, months and days as numbers (with leading zeros), as in 1969-12-31 or 2021-04-09"
			elif dateFormats[i].isoLevel == 2:
				send += "only using lines **-** as separators (no spaces), as in YYYY-MM-DD"
			send += "."
		return send


class MyClient(discord.Client):
	async def on_ready(self):
		print(f"{datetime.utcnow()}, {self.user} has connected to Discord!")
		servers = await self.fetch_guilds().flatten()
		send = f"Currently connected to {len(servers)} servers: \""
		for i in range(len(servers)):
			send += servers[i].name
			if i < len(servers) - 2:
				send += "\", \""
			elif i == len(servers) - 2:
				send += "\" and \""
			else:
				send += "\".\n"
		print(send)
	
	async def on_message(self, message):
		print(f"{message.created_at}, #{message.channel.name} in \"{message.channel.guild.name}\" by {message.author}: {message.content}")
		if not message.author.bot:

			dateFormats = []
			whole = re.findall("(?<!(\\+|\\*|=))(((\\/|\\\\|\\-|^) *)?(((year|month) *)?((\\d{2,4}|[1-9]) *((st|nd|rd|th) *)?|(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\\w* *)((month|year|of|,) *)*(\\/|\\\\|\\-|\\s) *){1,2}(((\\d{2,4}|[1-9])( *(st|nd|rd|th)(\\s|$))?|(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\\w*))( *(\\/|\\\\|\\-|$))?)(?!(\\d|\\+|\\*|=))", message.content, re.I)
			
			for i in range(len(whole)):
				toAdd = DateFormat(whole[i][1])
				if toAdd.isoLevel < 3:
					dateFormats.append(toAdd)
			
			if len(dateFormats) > 0:
				embed = discord.Embed(title = "Someone messed up their date formatting!", description = message.author.mention, color = discord.Color.red())
				for dateFormat in dateFormats:
					embed.add_field(name = useFormat(dateFormat.inputs, dateFormat.lines), value = dateFormat.dateAlts, inline = True)
				await message.reply(embed = embed)
				#await message.reply(Sentence().generate(dateFormats))
			elif len(whole) > 0:
				await message.add_reaction("✅")
				print(f"{datetime.utcnow()}, date is ISO-8601 compliant.")


client = MyClient()
client.run(TOKEN)