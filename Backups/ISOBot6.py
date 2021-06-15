import os
import re
import math
import random
import sqlite3
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

# Returns a string of lines with inputs inbetween.
def writeFormat(inputs, lines = None):
	# Allows inputs to be a class containing both arguments.
	if isinstance(inputs, DateFormat):
		lines = inputs.lines
		inputs = inputs.inputs
	send = lines[0]
	for i in range(len(inputs)):
		send += inputs[i]
		send += lines[i + 1]
	return send


class Date():
	def __init__(self, tokens, values, inputs = None):
		self.year = None
		self.yearLength = None
		self.month = None
		self.day = None

		for i in range(len(values)):
			if tokens[i][0] == "Y":
				self.year = values[i]
				if inputs:
					self.yearLength = len(inputs[i])
				else:
					self.yearLength = len(str(self.year))
			elif tokens[i][0] == "M":
				self.month = values[i]
			elif tokens[i][0] == "D":
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
	# An analysis of how iso-8601 compliant a date format could be.
	class Iso():
		def __init__(self, tokens = None, lines = None):
			self.order = False
			self.types = False
			self.lines = False
			self.spaces = False

			if tokens:
				self.checkTokens(tokens)
			if lines:
				self.checkLines(lines)

		def checkTokens(self, tokens):
			# Checks if the tag order is correct.
			if not self.order:
				if (len(tokens) == 3 and tokens[0][0] == "Y" and tokens[1][0] == "M" and tokens[2][0] == "D") or (len(tokens) == 2 and ((tokens[0][0] == "Y" and tokens[1][0] == "M") or (tokens[0][0] == "M" and tokens[0][0] == "D"))):
					self.order = True
			
			# Checks if the tag lengths are correct. TODO: Fix detection of written months.
			if not self.types:
				for token in tokens:
					if (token[0] == "Y" and len(token) != 4) or ((token[0] == "M" or token[0] == "D") and len(token) != 2):
						return
				self.types = True

		def checkLines(self, lines):
			if not self.lines or not self.spaces:
				isoLines = True
				isoSpaces = True

				# Checks if all the lines are correct. TODO: Fix detection of first and last separators.
				for line in lines[1:-1]:
					if line.strip() == "-":
						if line != "-":
							isoSpaces = False
					else:
						isoLines = False
				
				if not self.lines and isoLines:
					self.lines = True
				
				if not self.spaces and isoSpaces:
					self.spaces = True
		
		def compareBools(self, compare): # Maybe not necessary.
			self.order = self.order or compare.order
			self.types = self.types or compare.types
			self.lines = self.lines or compare.lines
			self.spaces = self.spaces or compare.spaces
		
		# Returns if iso is possible
		def __bool__(self):
			return self.order and self.types and self.lines and self.spaces
		
		def __str__(self):
			return f"Correct order: {self.order}, types: {self.types}, lines: {self.lines} and spaces: {self.spaces}"
	
	# A possible date, with all tag orders resulting in that date.
	class DateAlt():
		def __init__(self, date, tokens, iso):
			self.date = date
			self.tags = [tokens]
			self.iso = iso
		
		def __str__(self):
			return f"{self.date} (formatted as {self.tags}) {self.iso}"
		
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
		
		self.inputs = [] # Years, months and days saved as strings.
		self.values = [] # Years, months and days saved as numbers.
		self.tags = [] # Tags consist of tokens, ["YYYY", "MM", "DD"] is a tag, "YYYY" is a token.
		self.lines = [] # Everything between the numbers or month names.

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
		self.iso = self.Iso(lines = self.lines)

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

	def addAlt(self, tokens): # TODO: Rethink how incorrect lines are handled.
		date = Date(tokens, self.values, self.inputs)

		# Tries to find a fitting dateAlt for the tag to be sorted into.
		for i in range(len(self.dateAlts)):
			if self.dateAlts[i].date == date:
				self.dateAlts[i].tags.append(tokens)
				self.dateAlts[i].iso.checkTokens(tokens)
				self.iso.compareBools(self.dateAlts[i].iso)
				return
		# Adds another dateAlt if one doesn't already exist.
		dateAlt = self.DateAlt(date, tokens, self.Iso(tokens, self.lines))
		self.iso.compareBools(dateAlt.iso)
		self.dateAlts.append(dateAlt)
	
	def __str__(self):
		return f"{writeFormat(self)}, with values {self.values} representing {self.tags}, thus all possible formats are {self.dateAlts}. {self.iso}"
	
	def __repr__(self):
		return "\n" + str(self) + "\n"

class Sentence():
	def __init__(self, channel):
		self.skew = 0
		self.limit = 5
	
	def word(self, wordType, amount = 1, form = 0):
		send = ""
		if amount > 0:
			cursor = connection.cursor()
			query = """
				SELECT
					wordType,
					inflection,
					baseWord,
					random() AS priority
				FROM
					standardWords
				WHERE (wordType IN (\""""
			query += wordType
			if wordType == "com" or wordType == "gra":
				query += "\", \"adv"
			query += """\"))
				ORDER BY priority
				LIMIT @0;
			"""
			cursor.execute(query, [amount])
			for word in cursor.fetchall():

				# Adds things before the word.
				if word[0] == "adj" and word[1] == 0: # Adjective grades.
					if form == 1:
						send += "more "
					elif form == 2:
						send += "most "
				
				# Adds the word.
				send += word[2]

				# Adds things after the word.
				if word[0] == "adj": # Adjective grades.
					if word[1] == 1:
						if form == 1:
							send += "er"
						elif form == 2:
							send += "est"
					elif word[1] == 2:
						if form == 1:
							send += "ier"
						elif form == 2:
							send += "iest"
				elif word[0] == "adv" and wordType == "gra": # Changes adverbs to be descriptive.
					send += "ly"
				elif word[0] == "ins" and form == 1: # Changes insult amount.
					send += "s"
				send += " "
		return send

	# Analysis of single date
	def generate(self, dateFormat, shorten = False):
		dateAlts = dateFormat.dateAlts
		if len(dateAlts) == 1:
			send = "This must mean "
		else:
			send = "This could mean anything between:\n"
		for j in range(len(dateAlts)):
			dateAlt = dateAlts[j]
			if len(dateAlts) != 1:
				send += "- "
			send += "**"
			send += str(dateAlt.date)
			send += "** (formatted as "
			for k in range(len(dateAlt.tags)):
				send += "*"
				send += writeFormat(dateAlt.tags[k], dateFormat.lines)
				send += "*"
				if k + 2 < len(dateAlt.tags):
					send += ", "
				elif k + 2 == len(dateAlt.tags):
					send += " or "
			send += "), "
			if len(dateAlts) == 1:
				send += "but it"
			else:
				send += "which"
			send += " should be written *"
			send += dateAlt.date.isoString()
			send += "*.\n"
			if not shorten:
				send += "\nFix this date by "

				# Lists everything wrong with the date.
				fixes = []
				if not dateAlt.iso.types:
					fixes.append("writing the years, months and days as numbers with leading zeros (as in *1969-12-31* or *2021-04-09*)")
				if not dateAlt.iso.order:
					fixes.append("ordering the numbers correctly (as in *year-month-day*)")
				if not dateAlt.iso.lines:
					fixes.append("only using lines - as separators (as in *YYYY-MM-DD*)")
				if not dateAlt.iso.spaces:
					fixes.append("not using any spaces whatsoever")
				
				for j in range(len(fixes)):
					send += fixes[j]
					if j + 2 < len(fixes):
						send += ", "
					elif j + 2 == len(fixes):
						send += " and "
				send += ".\n"
		
		# Shortens date (crudely if needed) if it's too long.
		if len(send) > 1024:
			if shorten:
				send = send[:1020] + "..."
			else:
				send = self.generate(dateFormat, True)
		return send
	
	def title(self):
		send = ""
		if random.randint(0, 3) == 0:
			send += "Non ISO-8601 compliant "
		else:
			send += self.word("gra", random.randint(0, 1)).capitalize()
			send += self.word("bin", random.randint(0, 1))
			send += self.word("adj")
		send += "date formatting detected:"
		send = send[0].upper() + send[1:]
		return send
	
	def subtitle(self):
		send = ""
		if random.randint(0, 2) == 0:
			send += "You dun messed up, "
			send += self.word("bin", random.randint(0, 1))
			send += self.word("adj", random.randint(0, 1))
			send += self.word("ins").rstrip()
			send += "!"
		elif random.randint(0, 1) == 0:
			send += "Only "
			send += self.word("com", random.randint(0, 1))
			send += self.word("bin", random.randint(0, 1))
			send += self.word("ins", form = 1)
			send += "write like this!"
		else:
			send += "This is the "
			send += self.word("adj", form = 2)
			send += self.word("bin", random.randint(0, 1))
			send += self.word("obj")
			send += "I've "
			if random.randint(0, 1) == 0:
				send += "ever seen!"
			else:
				send += "laid my eyes upon!"
		return send
	
	def footer(self):
		return "My name is ISO Bot and I hate you!"

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
		if not message.author.bot:

			dateFormats = []
			whole = re.findall("(?<!(\\+|\\*|=))(((\\/|\\\\|\\-|^) *)?(((year|month) *)?((\\d{2,4}|[1-9]) *((st|nd|rd|th) *)?|(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\\w* *)((month|year|of|,) *)*(\\/|\\\\|\\-|\\s) *){1,2}(((\\d{2,4}|[1-9])( *(st|nd|rd|th)(\\s|$))?|(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\\w*))( *(\\/|\\\\|\\-|$))?)(?!(\\d|\\+|\\*|=))", message.content, re.I)
			if len(whole) > 0:
				print(f"{message.created_at}, #{message.channel.name} in \"{message.channel.guild.name}\" by {message.author}: {message.content}")
			
			for i in range(len(whole)):
				toAdd = DateFormat(whole[i][1])
				print(toAdd)
				if not toAdd.iso:
					dateFormats.append(toAdd)
			
			if len(dateFormats) > 0:
				sentence = Sentence(message.channel)
				embed = discord.Embed(title = sentence.title(), description = sentence.subtitle(), color = 0xe4010c)
				file = discord.File("Assets/warning.png", filename="warning.png")
				embed.set_thumbnail(url="attachment://warning.png")

				for dateFormat in dateFormats:
					embed.add_field(name = "**" + writeFormat(dateFormat) + "**", value = sentence.generate(dateFormat), inline = False)
				
				embed.set_footer(text = sentence.footer(), icon_url = "https://cdn.discordapp.com/avatars/796794008172888134/6b073c408aa584e4a03d7cfaf00d1e66.png?size=256") # TODO: Test stability.
				await message.reply(file = file, embed = embed)
				print("")
			elif len(whole) > 0:
				await message.add_reaction("✅")
				print("Date is ISO-8601 compliant.\n")

connection = sqlite3.connect("database.sqlite")

for i in range(20):
	print(Sentence(None).subtitle())

client = MyClient()
client.run(TOKEN)