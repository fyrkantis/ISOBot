from . import dataModule

# External Libraries
import random
from datetime import datetime, timedelta

class Word():
	def __init__(self, parameters, library = None):
		print(parameters)
		self.library = library
		self.number = None
		self.severity = None
		self.server = None

		parameters = list(parameters)

		if not self.library is None: # If the library is provided, then the number is the first parameter.
			self.number = parameters[0]
			self.word = parameters[1]
			if self.library == "default":
				self.severity = parameters[2]
			else:
				self.server = parameters[2]
			parameters = parameters[2:]
		else:
			self.word = parameters[0]
			parameters = parameters[1:]

		self.parameters = {}
		for i in range(len(dataModule.wordTypes)):
			if i >= len(parameters):
				parameters.append(None)
			self.parameters.update({dataModule.wordTypes[i]: parameters[i]})

	def __str__(self):
		send = self.word
		print(send)
		if not self.library is None:
			send += f"\nRow number {self.number} in library \"{self.library}\"."
		for name, value in self.parameters.items(): # TODO: Add more info about word here.
			send += "\n"
			send += name
			send += ": "
			send += str(value)
		return send

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
		cursor = dataModule.connection.cursor()
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
				send += dateFormat.writeFormat(dateAlt.tags[k])
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