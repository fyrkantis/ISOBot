from . import dataModule

# External Libraries
from random import randint, choice
from datetime import datetime, timedelta

def grammaticList(elements, last = "and"):
	send = ""
	for i, element in enumerate(elements):
		send += element
		if i + 2 < len(elements):
			send += ", "
		elif i + 2 == len(elements):
			send += " " + last + " "
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
				joinOn += f" t{i - 1}.word != t{i}.word"
			query += f"\n	(SELECT word, {wordList[i]} FROM t WHERE {wordList[i]} NOT NULL LIMIT 1) AS t{i}"
		query += joinOn

		words = None
		while words is None:
			# Executes query.
			cursor = dataModule.connection.cursor()
			cursor.execute(query, [self.message.guild.id])
			words = cursor.fetchone()
		words = list(words)

		# Inflects fetched words.
		send = ""
		for i in range(len(wordList)): # TODO: Clean up this mess.
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

	# Analysis of single date.
	def dateAnalysis(self, date):#, shorten = False):
		alternatives = date.alternatives
		send = ""
		#feedback = self.isoFeedback(date.iso)
		#if not feedback == "":
		#	send += f"You should fix this date by {feedback}.\n\n"
		if len(alternatives) == 1:
			send += "This must mean "
		else:
			send += f"This could mean {self.word(['binder', randint(0, 1)])}anything between:\n"
		for j in range(len(alternatives)):
			dateAlt = alternatives[j]
			if len(alternatives) != 1:
				send += "- "
			send += f"**{dateAlt.date}** ("
			if randint(0, 1) == 0:
				send += "for some reason "
			send += "formatted as "
			for k in range(len(dateAlt.tags)):
				send += f"*{date.write(dateAlt.tags[k])}*"
				if k + 2 < len(dateAlt.tags):
					send += ", "
				elif k + 2 == len(dateAlt.tags):
					send += " or "
			send += "), "
			if len(alternatives) == 1:
				send += "but it"
			else:
				send += "which"
			send += f" should be written *{dateAlt.date.isoString()}*"
			if randint(0, 5) != 0:
				send += ", "
				if randint(0, 2) == 0:
					send += "you " + self.word(["state", randint(0, 1), "binder", randint(0, 1), "insult"]).rstrip()
				elif randint(0, 1) == 0:
					send += "unlike your " + self.word(["binder", randint(0, 1), "object"]).rstrip()
				else:
					send += self.word(["degree", randint(0, 1), "binder", randint(0, 1), "adjective"]).rstrip()
			send += ".\n"
			#if not shorten:
			#	altFeedback = self.isoFeedback(dateAlt.iso, date.iso)
			#	if not altFeedback == "":
			#		start = ""
			#		if randint(0, 1) == 0:
			#			start += "You should "
			#		start += self.word(["binder", randint(0, 1)]) + "fix this date by "
			#		send += start[0].upper() + start[1:] + altFeedback + ".\n"
		
		# Shortens message if it's too long.
		if len(send) > 1024:
			send = send[:1020] + "..."
			#if shorten:
			#	send = send[:1020] + "..."
			#else:
			#	send = self.dateAnalysis(date, True)
		return send
	
	def isoFeedback(self, iso):
		# Lists everything wrong with the date.
		fixes = []
		if not iso.order:
			if randint(0, 1) == 0:
				fixes.append(f"ordering the numbers {self.word(['binder', randint(0, 1)])}correctly (as in *year-month-day*)")
			else:
				fixes.append(f"ordering the numbers less {self.word(['binder', randint(0, 1), 'adjective'])}(as in *year-month-day*)")
		if not iso.lines:
			fixes.append("only using lines - as separators (as in *YYYY-MM-DD*)")
		if not iso.types:
			fixes.append(f"writing the years, months and days as numbers with {self.word(['binder', randint(0, 1)])}leading zeros (as in *1970-01-01* or *2021-02-28*)")
		if not iso.spaces:
			fixes.append(f"not using any {self.word('binder', randint(0, 1))} spaces whatsoever")
		return fixes
	
	def title(self):
		send = ""
		if randint(0, 2) != 0:
			send += choice(["Detected ", "I see ", "How DARE you unleash theese "])
			send += self.word(["degree", randint(0, 1), "binder", randint(0, 1), "adjective"])
			send += "non ISO compliant "
		else:
			send += "My "
			send += self.word(["binder", randint(0, 1)])
			send += choice(["aperture blades ", "lenses ", "light sensors "])
			send += choice(["bring me nothing but pain", "are cracking", "have never hurt more"])
			send += " from seeing your "
			send += self.word(["adjective", randint(0, 1)])
		send += "units:"
		send = send[0].upper() + send[1:]
		return send
	
	def subtitle(self, dateIso):
		send = ""
		if randint(0, 3) == 0:
			send += "You dun messed up, "
			send += self.word(["binder", randint(0, 1), "adjective", randint(0, 1), "insult"]).rstrip()
			send += "!"
		elif randint(0, 2) == 0:
			send += "Only "
			send += self.word(["state", randint(0, 1), "binder", randint(0, 1), "insult"], amount = 2)
			send += "write like this!"
		elif randint(0, 1) == 0:
			if randint(0, 1) == 0:
				send += "What the "
			else:
				send += "What in the "
				send += self.word(["state", "binder", randint(0, 1)])
			
			send += self.word(["comment"])
			send += choice(["is this?", "do you call this?"])
		else:
			send += "This is the "
			send += self.word(["adjective", "binder", randint(0, 1), "object"], grade = 2)
			send += "I've "
			send += choice(["ever seen!", "laid my eyes upon!"])
		send += f"\nYou could fix this date by {grammaticList(self.isoFeedback(dateIso))}."
		
		return send
	
	def footer(self):
		send = ""
		if randint(0, 1) == 0:
			send += "My name is ISO Bot and I hate you!"
		else:
			send += "Here's an important date to remember: "
			send += (datetime.today() + timedelta(days=1)).isoformat()[:10]
			send += " at 1:59 AM, because that's when I'll be outside your house with a "
			send += self.word(["binder"])
			send += choice(["tazer", "pair of scissors", "rusty spoon", "brick"])
			send += "!"
		return send

	def insult(self) -> str:
		words = []
		if randint(0, 2) == 0:
			words.append("Eat ")
			words.append(self.word(["object"]))
		elif randint(0, 1) == 0:
			words.append("Nobody likes you, ")
		else:
			words.append("Shut ")
			if randint(0, 1) == 0:
				words.append("the fuck ")
			words.append("up ")
		words.append("you ")
		words.append(self.word(["state", randint(0, 1), "binder", randint(0, 1), "adjective", "binder", randint(0, 1), "insult", randint(0, 1)]))
		words.append(choice(["robot vacuum ", "garbled python script ", "tin can "]))
		if randint(0, 1) == 0:
			words.append(self.word(["insult"]))
		return "".join(words)[:-1] + "."