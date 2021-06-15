import os
import re
import shlex
import random
import sqlite3
import discord

from discord_slash import SlashCommand
from discord_slash.utils.manage_commands import create_choice, create_option

from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD = os.getenv("DISCORD_GUILD")
ID = os.getenv("DISCORD_ID")

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

# Makes an ascii table out of data.
def writeTable(data, names = None, maxLengths = None):
	if not names is None:
		data.insert(0, names)
	lengths = []
	for r in range(len(data)):
		for c in range(len(data[r])):
			if c >= len(lengths):
				lengths.append(0)
			
			if data[r][c] is None: # Makes empty cells empty.
				data[r][c] = ""
			elif not maxLengths is None and len(str(data[r][c])) > maxLengths[min(c, len(maxLengths) - 1)]: # Cuts off too long cells.
				data[r][c] = str(data[r][c])[:(maxLengths[(min(c, len(maxLengths) - 1))] - 1)] + "…"
			
			if len(str(data[r][c])) > lengths[c]:
				lengths[c] = len(str(data[r][c]))
	send = ""
	for r in range(len(data)):
		for c in range(len(lengths)):
			send += "|"
			if c < len(data[r]):
				if isinstance(data[r][c], str):
					send += data[r][c]
				send += " " * (lengths[c] - len(str(data[r][c])))
				if not isinstance(data[r][c], str):
					send += str(data[r][c])
			else:
				send += " " * lengths[c]
			#send += " "
			if c + 1 == len(lengths):
				send += "|"
				if r + 1 < len(data):
					send += "\n"
					if r == 0 and not names is None:
						for length in lengths:
							send += "|" + ("-" * length)
						send += "|\n"
	return send



class Date():
	def __init__(self, tokens, values, inputs = None):
		self.year = None
		self.yearLength = None
		self.month = None
		self.day = None
		self.valid = None

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
		
		# Checks if the day fits within the month's length.
		if self.month and self.day:
			monthLength = 31
			if self.month % 2 == 0:
				if self.month == 2:
					monthLength = 29
					if self.yearLength: # Assumes leap year, but tries to outrule.
						if not self.year % 2 == 0 or (self.yearLength == 4 and not (self.year % 4 == 0 and (not self.year % 100 == 0 or self.year % 400 == 0))):
							monthLength = 28
				elif self.month <= 6:
					monthLength = 30
			else:
				if self.month >= 9:
					monthLength = 30
			self.valid = self.day <= monthLength
		elif not self.month:
			self.valid = False
	
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
		if self.valid is False:
			send += "Invalid date "
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
		if self.valid:
			send += months[self.month - 1]
		else:
			send += "month "
			send += str(self.month)
		if self.year:
			send += " year "
			send += self.yearString()
		send = send[0].upper() + send[1:]
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
			
			# Checks if the tag lengths are correct. TODO: Fix detection for written months.
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
		if date.valid is False:
			return

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
	def __init__(self, message):
		self.skew = 0
		self.limit = 5
		self.message = message
	
	def word(self, wordTypes, grade = 0, amount = 0):
		wordList = []
		allTypes = ""
		for i in range(len(wordTypes)):
			if not isinstance(wordTypes[i], int):
				count = 1
				if i + 1 < len(wordTypes) and isinstance(wordTypes[i + 1], int):
					count = wordTypes[i + 1]
				for j in range(count):
					wordList.append(wordTypes[i])
				if count > 0:
					allTypes += ", "
					allTypes += wordTypes[i]

		if len(wordList) == 0:
			return ""
		
		# Generates query.
		query = """
WITH t AS (
	SELECT word"""
		query += allTypes
		query += """, random() as r FROM (
		SELECT * FROM defaultLibrary UNION ALL SELECT * FROM customLibrary WHERE server = @0
		) ORDER BY r
)
SELECT * FROM"""
		joinOn = ""
		for i in range(len(wordList)):
			if i > 0:
				query += "\n	JOIN"
				if i == 1:
					joinOn += "\nON"
				elif i > 1:
					joinOn += " AND"
				joinOn += " t"
				joinOn += str(i - 1)
				joinOn += ".word != t"
				joinOn += str(i)
				joinOn += ".word"
			query += "\n	(SELECT word, "
			query += wordList[i]
			query += " FROM t WHERE "
			query += wordList[i]
			query += " NOT NULL LIMIT 1) AS t"
			query += str(i)
		query += joinOn

		# Executes query.
		cursor = connection.cursor()
		cursor.execute(query, [self.message.guild.id])
		allWords = cursor.fetchall()
		words = list(allWords[0])

		# Inflects fetched words.
		send = ""
		for i in range(len(wordList)):
			word = words.pop(0)
			inflection = words.pop(0)
			if wordList[i] == "adjective":
				if inflection <= 3:
					if grade == 1:
						send += "more "
					elif grade == 2:
						send += "most "
			elif wordList[i] == "insult":
				if inflection == 3:
					if amount < 2:
						send += "piece of "
					else:
						send += "pieces of "
					
			send += word
			if wordList[i] == "adjective":
				if inflection == 1:
					send += "ic"
				elif inflection == 2:
					send += "ish"
				elif inflection == 3:
					send += "ed up"
				elif inflection >= 4:
					if inflection == 5:
						send += word[-1]
						if grade == 0:
							send += "y"
						else:
							send += "i"
					if grade == 1:
						send += "er"
					elif grade == 2:
						send += "est"
			elif wordList[i] == "binder":
				if inflection == 1:
					send += "ing"
			elif wordList[i] == "degree":
				if inflection > 0:
					send += "ly"
			elif wordList[i] == "insult":
				if inflection <= 2:
					if inflection == 2:
						send += "er"
					if amount == 2:
						send += "s"
			elif wordList[i] == "state":
				if inflection == 2:
					send += "ed up"
			
			if wordList[i] == "comment":
				if amount == 2:
					send += "s"
			send += " "
		
		return send

	# Analysis of single date
	def generate(self, dateFormat, shorten = False):
		dateAlts = dateFormat.dateAlts
		if len(dateAlts) == 1:
			send = "This must mean "
		else:
			send = "This could mean "
			send += self.word(["binder", random.randint(0, 1)])
			send += "anything between:\n"
		for j in range(len(dateAlts)):
			dateAlt = dateAlts[j]
			if len(dateAlts) != 1:
				send += "- "
			send += "**"
			send += str(dateAlt.date)
			send += "** ("
			if random.randint(0, 1) == 0:
				send += "for some reason "
			send += "formatted as "
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
			send += "*"
			if random.randint(0, 5) != 0:
				send += ", "
				if random.randint(0, 2) == 0:
					send += "you "
					send += self.word(["state", random.randint(0, 1), "binder", random.randint(0, 1), "insult"]).rstrip()
				elif random.randint(0, 1) == 0:
					send += "unlike your "
					send += self.word(["binder", random.randint(0, 1), "object"]).rstrip()
				else:
					send += self.word(["degree", random.randint(0, 1), "binder", random.randint(0, 1), "adjective"]).rstrip()
			send += ".\n"
			if not shorten:
				start = ""
				if random.randint(0, 1) == 0:
					start += "You better "
				start += self.word(["binder", random.randint(0, 1)])
				start += "fix this date by "
				send += start[0].upper() + start[1:]

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
		if random.randint(0, 2) != 0:
			send += random.choice(["Detected ", "I see ", "How DARE you unleash this "])
			send += self.word(["degree", random.randint(0, 1), "binder", random.randint(0, 1), "adjective"])
			send += "non ISO-8601 compliant "
		else:
			send += "My "
			send += self.word(["binder", random.randint(0, 1)])
			send += random.choice(["aperture blades ", "lenses ", "light sensors "])
			send += random.choice(["bring me nothing but pain", "are cracking", "have never hurt more"])
			send += " from seeing your "
			send += self.word(["adjective", random.randint(0, 1)])
		send += "date formatting:"
		send = send[0].upper() + send[1:]
		return send
	
	def subtitle(self):
		send = ""
		if random.randint(0, 3) == 0:
			send += "You dun messed up, "
			send += self.word(["binder", random.randint(0, 1), "adjective", random.randint(0, 1), "insult"]).rstrip()
			send += "!"
		elif random.randint(0, 2) == 0:
			send += "Only "
			send += self.word(["state", random.randint(0, 1), "binder", random.randint(0, 1), "insult"], amount = 2)
			send += "write like this!"
		elif random.randint(0, 1) == 0:
			if random.randint(0, 1) == 0:
				send += "What the "
			else:
				send += "What in the "
				send += self.word(["state", "binder", random.randint(0, 1)])
			
			send += self.word(["comment"])
			send += random.choice(["is this?", "do you call this?"])
		else:
			send += "This is the "
			send += self.word(["adjective", "binder", random.randint(0, 1), "object"], grade = 2)
			send += "I've "
			send += random.choice(["ever seen!", "laid my eyes upon!"])
		return send
	
	def footer(self):
		send = ""
		if random.randint(0, 1) == 0:
			send += "My name is ISO Bot and I hate you!"
		else:
			send += "Here's an important date to remember: "
			send += (datetime.today() + timedelta(days=1)).isoformat()[:10]
			send += " at 1:59 AM, because that's when I'll be outside your house with a "
			send += self.word(["binder"])
			send += random.choice(["tazer", "pair of scissors", "rusty spoon", "brick"])
			send += "!"
		return send

class MyClient(discord.Client):
	async def on_ready(self):
		print(f"{datetime.utcnow()}, {self.user} has connected to Discord!")
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
				toAdd = DateFormat(whole[i][1])
				print(toAdd)
				if not toAdd.iso:
					dateFormats.append(toAdd)
			
			if len(dateFormats) > 0:
				sentence = Sentence(message)
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

guild_ids = [732240720487776356, 746842558180622396]

client = MyClient()
slash = SlashCommand(client, sync_commands = True)

@slash.subcommand(
	base = "words",
	name = "show",
	description = "I'll write out all custom words that I'm currently using from this server's word library.",
	options = [
		create_option(
			name = "library",
			description = "Would you like to see a diffrent library? Paste a server ID here, or select another option.",
			option_type = 3,
			required = False,
			choices = [
				create_choice(name = "server", value = "server"),
				create_choice(name = "default", value = "default"),
				create_choice(name = "connected", value = "connected"),
				create_choice(name = "everything", value = "everything")
			]
		),
		create_option(
			name = "server",
			description = "Paste a valid server ID to se the server's custom word library.",
			option_type = 3,
			required = False
		)
	],
 	guild_ids = guild_ids
)
async def writeWords(ctx, library = None, server = None):
	cursor = connection.cursor()
	cursor.execute("PRAGMA table_info(defaultLibrary)") # Gathers all column names.
	columns = []
	for column in cursor.fetchall():
		columns.append(column[1])
	columnLengths = [11, 9, 4]

	# Selects query and arguments.
	target = "customLibrary WHERE server = @0"
	args = []
	send = "Showing "
	if server and server.isdigit():
		columns.pop(1)
		columnLengths.pop(1)
		args = [int(server)]
		send += str(server)
		send += " \""
		send += client.get_guild(int(server)).name
		send += "\"'s "
	elif library and library.lower() == "default":
		target = "defaultLibrary"
		send += "the default "
	elif library and library.lower() == "connected":
		send += "every connected "
	elif library and library.lower() == "everything":
		send += "this server's word library, the default word library *and* every connected "
	else:
		columns.pop(1)
		columnLengths.pop(1)
		args = [ctx.guild.id]
		send += "this server's "
	send += "word library:\n```"

	query = "SELECT "
	for i in range(len(columns)):
		query += columns[i]
		if i + 1 < len(columns):
			query += ", "
	query += " FROM " + target + " ORDER BY word;"

	cursor.execute(query, args)
	words = []
	for word in cursor.fetchall():
		words.append(list(word))
	if len(words) > 0:
		send += writeTable(words, columns, columnLengths)
	else:
		send += "There are no words in this library."
	send += "```"
	await ctx.send(send)

@slash.subcommand(
	base = "words",
	name = "add",
	description = "Add a new word to this server's custom word library, and I'll start using it.",
	options = [
		create_option(
			name = "word",
			description = "This is the base of the word. Use the other parameters to specify how the word should be used.",
			option_type = 3,
			required = True
		),
		create_option(
			name = "adjective",
			description = "Input inflection IF this sentence works: \"You are the (word) person ever.\".",
			option_type = 4,
			required = False,
			choices = [
				create_choice(name = "most (word). Example: Devoid.", value = 0),
				create_choice(name = "most (word)ic. Example: Idiot.", value = 1),
				create_choice(name = "most (word)ish. Example: Dick.", value = 2),
				create_choice(name = "most (word)ed up. Example: Mess.", value = 3),
				create_choice(name = "(word)est. Example: Stupid.", value = 4),
				create_choice(name = "(word + last letter, so wordd)iest. Example: Crap.", value = 5)
			]
		),
		create_option(
			name = "binder",
			description = "Input inflection IF this sentence works: \"You are very (word) bad.\".",
			option_type = 4,
			required = False,
			choices = [
				create_choice(name = "(word). Example: Damn.", value = 0),
				create_choice(name = "(word)ing. Example: Fuck.", value = 1)
			]
		),
		create_option(
			name = "comment",
			description = "Input inflection IF this sentence works: \"What the (word) is this?\".",
			option_type = 4,
			required = False,
			choices = [
				create_choice(name = "(word). Example: Hell.", value = 0)
			]
		),
		create_option(
			name = "degree",
			description = "Input inflection IF this sentence works: \"You are (word) bad person.\".",
			option_type = 4,
			required = False,
			choices = [
				create_choice(name = "a (word). Example: Very.", value = 0),
				create_choice(name = "a (word)ly. Example: Real.", value = 1),
				create_choice(name = "an (word)ly. Example: Extreme.", value = 2)
			]
		),
		create_option(
			name = "insult",
			description = "Input inflection IF this sentence works: \"You are (word).\".",
			option_type = 4,
			required = False,
			choices = [
				create_choice(name = "an (word). Example: Idiot.", value = 0),
				create_choice(name = "a (word). Example: Moron.", value = 1),
				create_choice(name = "a (word)er. Example: Fuck.", value = 2),
				create_choice(name = "a piece of (word). Example: Shit.", value = 2)
			]
		),
		create_option(
			name = "object",
			description = "Input inflection IF this sentence works: \"What's this (word)?\".",
			option_type = 4,
			required = False,
			choices = [
				create_choice(name = "(word). Example: Mess.", value = 0)
			]
		),
		create_option(
			name = "state",
			description = "Input inflection IF this sentence works: \"You are (word) fucking idiot.\".",
			option_type = 4,
			required = False,
			choices = [
				create_choice(name = "an (word). Example: Absolute.", value = 0),
				create_choice(name = "a (word). Example: Real.", value = 1),
				create_choice(name = "a (word)ed up. Example: Mess.", value = 2)
			]
		)
	],
	guild_ids = guild_ids
)
async def add(ctx, word, **kwargs):
	query = "INSERT INTO customLibrary (word, server"
	print(kwargs)
	for key in kwargs.keys():
		query += ", "
		query += key
	query += ") VALUES (@0, @1"
	for value in kwargs.values():
		query += ", "
		query += str(value)
	query += ");"
	print(query)
	cursor = connection.cursor()
	cursor.execute(query, [word, ctx.guild.id])
	cursor.close()
	connection.commit()

	await ctx.send("Sorry, no.")

@slash.subcommand(
	base = "words",
	name = "help",
	description = "AAA! What are theese \"words\" commands, and what do they do?",
	guild_ids = guild_ids
)
async def help(ctx):
	await ctx.send("Good luck!")
#@slash.slash(
#	name = "word",
#	description = "My language is based several libraries of curse words. See or modify them by using this command.",
#	options = [
#		create_option(
#			name = "show",
#			description = "I'll write out all custom words that I'm currently using from this server's word library.",
#			option_type = 2,
#			required = False,
#			options = [
#				create_option(
#					name = "showaaa",
#					description = "I'll write out all custom words that I'm currently using from this server's word library.aaa",
#					option_type = 1,
#					required = False
	#				options = [
#					create_option(
#						name = "library",
#						description = "Do you want to see a diffrent library? Enter a server ID here, or select another option.",
#						option_type = 3,
#						required = False,
#						choices = [
#							create_choice(name = "default", value = "default"),
#							create_choice(name = "connected", value = "connected")
#						]
#				)
#			]
#		)
#	],
#	guild_ids = guild_ids
#)
#async def word(ctx):
#	print("AAA")

#@slash.subcommand(
#	base = "word",
#	subcommand_group = "show",
#	name = "showaaa",
#	description = "I'll write out all custom words that I'm currently using from this server's word library.aaa",
#	options = [
#		create_option(
#			name = "library",
#			description = "Do you want to see a diffrent library? Enter a server ID here, or select another option.",
#			option_type = 3,
#			required = False,
#			choices = [
#				create_choice(name = "default", value = "default"),
#				create_choice(name = "connected", value = "connected")
#			]
#		)
#	],
#	guild_ids = guild_ids
#)
#async def test(ctx):
#	print("BBB")

#@slash.slash(
#	name = "add-word",
#	description = "Tell me a new word you'd like me to use in this server. Type \"/write-words default\" for examples.",
#	options = [
#		create_option(
#			name = "baseWord",
#			description = "Make sure it'll work with what the other parameters add before and/or after it."
#		),
#		create_option(
#			name = "wordType",
#			 
#		)
#	]
#)

#@slash.slash(name="ping", guild_ids = guild_ids)
#async def _ping(ctx):
#	await ctx.send(f"Pong! ({client.latency*1000}ms)")

#@slash.slash(
#	name = "test",
#	description = "This is just a test command, nothing more.",
#	options = [
#		create_option(
#			name = "option",
#			description = "This is the first option we have.",
#			option_type = 3,
#			required = False
#		)
#	],
#	guild_ids = guild_ids
#)
#async def test(ctx, option):
#	await ctx.send(content = f"You said: {option}!")



connection = sqlite3.connect("database.sqlite")

client.run(TOKEN)

""",
		create_option(
			name = "add",
			description = "Tell me a new word I should add to this server's word library. Use \"word show\" for examples.",
			option_type = 1,
			required = False,
			options = [
				create_option(
					name = "base-word",
					description = "Make sure it'll work with what the other parameters add before and/or after it.",
					option_type = 3,
					required = True
				),
				create_option(
					name = "word-type",
					description = "This tells me where to use the word, which is important. Use \"word type\" for more info.",
					option_type = 3,
					required = True,
					choices = [
						create_choice(name = "adjective", value = "adj"),
						create_choice(name = "adverb", value = "adv"),
						create_choice(name = "binder", value = "bin"),
						create_choice(name = "comment", value = "com"),
						create_choice(name = "grade", value = "gra"),
						create_choice(name = "insult", value = "ins"),
						create_choice(name = "object",value = "obj")
					]
				),
				create_option(
					name = "inflection",
					description = "This tells me how to modify the word, and is not always needed. Use \"word type\" for more info.",
					option_type = 4,
					required = False
				)
			]
		)"""