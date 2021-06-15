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

def valueInList(tokens, optns, values): # Needs to be replaced, must've been high when writing this.
	for i in range(len(optns)): # Loops through date groups.
		displaced = []
		for j in range(len(tokens)): # Loops through tokens.
			if optns[i][0][j][0] != tokens[j][0]: # Compares tokens with the date group's first format's tokens.
				displaced.append(values[j]) # Saves values of those that are not equal.
		for k in range(len(displaced[:-1])): # Loops through values of tokens within a date group whose types aren't equal to those of the corresponding tokens.
			if displaced[k] != displaced[k + 1]: # Skips to next date group if any conflicting values differ.
				break
			elif k >= len(displaced) - 2: # Returns index of first date group where first format results in the same date.
				return i
	return False

def readFormat(tokens, values, isoify = False):
	year = ""
	month = 0
	day = 0
	for i in range(len(tokens)):
		if tokens[i][0] == "Y":
			year = (4 - len(str(values[i]))) * "X" + str(values[i])
		elif tokens[i][:3] == "Mon":
			for j in range(len(months)):
				if months[j][:3].lower() == values[i][:3].lower():
					month = j + 1
		elif tokens[i][0] == "M":
			month = int(values[i])
		elif tokens[i][0] == "D":
			day = int(values[i])
	
	# Safety check, this was the most practical place to put it.
	if year.isdigit():
		if monthrange(int(year), month)[1] < int(day):
			return False
	else:
		if monthrange(2020, month)[1] < int(day):
			return False
	
	send = ""
	if isoify:
		if year != "":
			send += year
			send += "-"
		if month < 10:
			send += "0"
		send += str(month)
		if day > 0:
			send += "-"
			if day < 10:
				send += "0"
			send += str(day)
	else:
		if day > 0:
			send += str(day)
			if day == 1:
				send += "st"
			elif day == 2:
				send += "nd"
			elif day == 3:
				send += "rd"
			else:
				send += "th"
			send += " "
		if month != 0:
			send += months[month - 1]
		if year != "":
			send += " year "
			send += str(year)
	return send

def useFormat(separators, values):
	send = separators[0]
	for i in range(len(values)):
		send += str(values[i])
		send += separators[i + 1]
	return send

def listFormats(optns, lines):
	send = ""
	for i in range(len(optns)):
		send += f"`{useFormat(lines, optns[i])}`"
		if i + 2 < len(optns):
			send += ", "
		elif i + 2 == len(optns):
			send += " or "
		
	return send

class Sentence():
	def __init__(self):
		self.pre = ["absolute", "devoid", "geriatric", "goddamn", "IQ-liberated", "little", "salty", "stupid"]
		self.binders = ["garlic bread hating", "fucking", "straight"]
		self.substantive = ["bitch", "cunt", "dumbass", "desperat ketchupflaska", "twat", "idiot", "pillock"]
		self.substantiveStart = [["dick", "dirt", "shit", "knob", "toilet", "whank"], ["dip", "piece of "], ["waste of "], ["dick", "ass"]]
		self.substantiveEnd = [["bag", "er", "head", "stain", "doodle"], ["shit"], ["air", "space"], ["-vaccum", "brush"]]
		self.nouns = ["in the name of god", "the hell", "the fuck"]
		self.adjective = ["fucking"]
		self.expression = ["I really hope", "you better not"]
		self.thing = ["dear", "lord", "my"]

	def subject(self):
		if random.randint(0, 2) == 0:
			return random.choice(self.substantive)
		else:
			index = random.randint(0, len(self.substantiveStart) - 1)
			return random.choice(self.substantiveStart[index]) + random.choice(self.substantiveEnd[index])
	
	def description(self):
		send = ""
		if random.randint(0, 2) == 0:
			send += random.choice(self.pre)
			send += " "
		
		for binder in self.binders:
			if random.randint(0,2) == 0:
				send += binder
				send += " "
		
		send += self.subject()
		return send
	
	def generate(self, dates, lines, optns, levls):
		realSend = ""
		description = self.description()
		if len(optns) <= 1:
			if random.randint(0, 2) == 0:
				realSend += f"This date formatting looks like the true work of a real {description}."
			elif random.randint(0, 1) == 0:
				realSend += f"I'm amazed by this {description}'s ability to mess up their date formatting this badly."
			else:
				realSend += f"Did you format this date all by yourself, you {description}?"
		else:
			realSend += f"Oh {random.choice(self.thing)}, there are many wrongly formatted dates here. WHY did you have to do this you {description}?"
		
		for i in range(len(optns)):
			send = "\n"
			if random.randint(0, 1) == 0:
				send += f"What {random.choice(self.nouns)} is \"**{useFormat(lines[i], dates[i])}**\" supposed to mean?"
			else:
				send += f"Something must've gone really {random.choice(self.adjective)} wrong when you decided to unleash \"**{useFormat(lines[i], dates[i])}**\" into this channel."
			for j in range(len(optns[i])):
				send += " "
				optnRead = readFormat(optns[i][j][0], dates[i])
				optnFormats = listFormats(optns[i][j], lines[i])
				if j <= 0:
					if random.randint(0, 1) == 0:
						send += f"Is it *{optnRead}* formatted as {optnFormats}?"
					else:
						send += f"Did you just format *{optnRead}* as {optnFormats}?"
				else:
					if random.randint(0, 2) == 0:
						send += f"Or were you trying to write *{optnRead}* and format it as {optnFormats}?"
					elif random.randint(0, 1) == 0:
						send += f"It could also mean *{optnRead}* formatted as {optnFormats}."
					else:
						send += f"It could also mean *{optnRead}* formatted as {optnFormats}."
				send += " "
				if random.randint(0, 2) == 0:
					send += f"This should be written as **{readFormat(optns[i][j][0], dates[i], True)}**!"
				elif random.randint(0, 1) == 0:
					send += f"Why {random.choice(self.nouns)} is it not written **{readFormat(optns[i][j][0], dates[i], True)}**?"
				else:
					send += f"Learn how to format dates you {description}, write **{readFormat(optns[i][j][0], dates[i], True)}** instead."
				send += "\n"
			if len(realSend) + len(send) <= 2000:
				realSend += send
			else:
				break
		return realSend

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
			if "iso bot" in message.content.lower():
				await message.reply(f"How dare you contaminate {message.channel.mention} by using the lord's name in vain? {Sentence().description().capitalize()}.")
			
			# Detects dates and finds out what's wrong with them.
			whole = re.findall("(?<!(\\+|\\*|=))(((\\/|\\\\|\\-|^) *)?(((year|month) *)?((\\d{2,4}|[1-9]) *((st|nd|rd|th) *)?|(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\\w* *)((month|year|of|,) *)*(\\/|\\\\|\\-|\\s) *){1,2}(((\\d{2,4}|[1-9])( *(st|nd|rd|th)(\\s|$))?|(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\\w*))( *(\\/|\\\\|\\-|$))?)(?!(\\d|\\+|\\*|=))", message.content, re.I)

			dates = [] # Will contain lists of lists of days, months or years. Example: [[2020, 12, 31], [1, "jan", 1970]], [10, 10, 12]
			types = [] # Same contents as list above, except that days, months or years are replaced with letters specifying what it can mean.
			# Same example as above: [[["YYYY"], ["YY", "MM", "DD"], ["YY", "DD"]], [["YY", "MM", "DD"], ["Mon"], ["YYYY"]], [["YY", "MM", "DD"], ["YY", "MM", "DD"], ["YY", "MM", "DD"]]]
			lines = [] # List of lists of strings that separate days, months and years.
			optns = [] # List of lists of possible date formats, organised by what the date means.
			# Same example as above: [[[["YYYY", "MM", "DD"]], [["YYYY", "DD", "MM"]]], [[["DD", "Mon", "YYYY"]]], [[["YY", "MM", "DD"], ["MM", "YY", "DD"]], [["YY", "DD", "MM"], ["DD", "YY", "MM"]], [["MM", "DD", "YY"], ["DD", "MM", "YY"]]]]
			levls = [] # List of words representing what's wrong with all diffrent dates.

			#print(whole)
			for i in range(len(whole)):
				#print(whole[i][1])
				separated = re.split("(\\d+|\\w+)", whole[i][1])
				#print(separated)
				
				index = 1
				while index < len(separated):
					if separated[index] == "st" or separated[index] == "nd" or separated[index] == "rd" or separated[index] == "th":
						separated[index] = "th"
						separated[(index - 1):(index + 2)] = ["".join(separated[(index - 1):(index + 2)])]
						#print(separated)
					elif  separated[index] == "of" or separated[index] == "year" or separated[index] == "month":
						separated[(index - 1):(index + 2)] = ["".join(separated[(index - 1):(index + 2)])]
						#print(separated)
					else:
						index += 2

				dates.append([])
				types.append([])
				lines.append([])

				# Saves all numbers/letters in right places.
				for k in range(len(separated)):
					if k % 2 == 1:
						j = len(dates[i])
						if separated[k].isnumeric():
							dates[i].append(separated[k])
							# Figures out what the numbers mean.
							types[i].append(["Y" * len(separated[k])])
							if len(separated[k]) <= 2:
								
								if int(dates[i][j]) <= 31:
									if int(dates[i][j]) <= 12:
										types[i][j].append("M" * len(dates[i][j]))
									types[i][j].append("D" * len(dates[i][j]))
							
						else:
							for l in range(len(months)):
								if months[l][:3].lower() == separated[k][:3].lower():
									dates[i].append(separated[k])
									if len(separated[k]) == 3:
										types[i].append(["Mon"])
									else:
										types[i].append(["Month"])
									break
							
					else:
						lines[i].append(separated[k])
				
				print(dates[i])
				print(lines[i])
				print(types[i])
				optns.append([])

				# Tests possible combinations.
				# To implement: Optimization that removes duplicates of arrays with only one possibility in them.
				if len(types[i]) > 1:
					for first in types[i][0]:
						for secnd in types[i][1]:
							if len(types[i]) > 2:
								for third in types[i][2]:
									if first[0] != secnd[0] and secnd[0] != third[0] and third[0] != first[0]:
										toAdd = [first, secnd, third]
										isInList = valueInList(toAdd, optns[i], dates[i])
										if not isInList is False:
											optns[i][isInList].append(toAdd)
										else:
											optns[i].append([toAdd])
							else:
								if first[0] != secnd[0] and (first[0] == "M" or secnd[0] == "M"):
									toAdd = [first, secnd]
									isInList = valueInList(toAdd, optns[i], dates[i])
									if not isInList is False:
										optns[i][isInList].append(toAdd)
									else:
										optns[i].append([toAdd])
					
				print(optns[i])
				levls.append(0)

				for j in range(len(optns[i])):
					for k in range(len(optns[i][j])):
						tokens = optns[i][j][k]
						letters = []
						for l in range(len(tokens)):
							letters.append(tokens[l][0])
						if letters == ["Y", "M", "D"] or letters == ["Y", "M"] or letters == ["M", "D"]:
							if tokens == ["YYYY", "MM", "DD"] or tokens == ["YYYY", "MM"] or tokens == ["MM", ["DD"]]:
								ISOLines = True
								for line in lines[i][1:-1]:
									if line.strip() != "-":
										ISOLines = False
										break
								if ISOLines:
									optns[i][j].pop(k)
									if len(optns[i][j]) == 0:
										optns[i].pop(j)
									levls[i] = max(levls[i], 3)
								else:
									levls[i] = max(levls[i], 2)
							else:
								levls[i] = max(levls[i], 1)
				
				print(levls[i])
			
			if len(dates) > 0:
				if len(optns) > 0:
					await message.reply(Sentence().generate(dates, lines, optns, levls))
				else:
					await message.add_reaction("✅")
					print(f"{datetime.utcnow()}, date is ISO-8601 compliant.")

client = MyClient()
client.run(TOKEN)

"""
Current bugs:
- Look for the, th, year and month written before and/or after numbers for more filtering.
- Clariy how to correctly format a non ISO-8601 compliant date and point out what's wrong when able to.
- If message contains several dates, only some of which aren't ISO-8601 compliant, it flags even the correct ones.
- Doesn't do roman numerals.
- first, second, third.
- Make DM's functional.
- Reformulate to make message shorter, maybe only list all date possibilities.
- Only ask what the date is supposed to mean if there is any ambiguity.
- Mark dates (or formats) with emotes and encourage a vote of what the date is supposed to mean.
- Space between +, * or = and number makes regex ignore the negative lookbehind.
- BC dates.
- Don't interpret dates between quotes.
- Add more safety checks for date lengths.
- Statistical analysis of dates.
"""