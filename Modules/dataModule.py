# External Libraries
import sqlite3

class Option():
	def __init__(self, name, description, choices = []):
		self.name = name
		self.description = description
		self.choices = choices
	
	def __str__(self):
		return f"{self.name}: {self.description} Choices: {self.choices}"
	
	def __repr__(self):
		return "\n" + str(self)

class OptionList():
	def __init__(self, option_type, options = [], required = False):
		self.option_type = option_type
		self.options = options
		self.required = required
	
	def option(self, name):
		for option in self.options:
			if option.name == name:
				return option
		return None

	def __str__(self):
		return f"Type: {self.option_type}, Required: {self.required}, Options: {self.options}."

class Word(): # Currently only used for organization in in inputModule.py.
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
		if not self.library is None:
			send += f"\nRow number {self.number} in library \"{self.library}\"."
		for key, value in self.parameters.items(): # TODO: Add more info about word here.
			print(key + ": " + str(value))
			send += "\n"
			send += key
			send += ": "
			send += str(value)
			if not value is None:
				option = dataModule.optionList.option(key)
				if not option is None:
					send += ", "
					send += option.choices[value]
		return send

optionList = OptionList(4, [
	Option(
		"adjective",
		"Input inflection IF this sentence works: \"You are the (word) person ever.\".",
		[
			"most (word). Example: Devoid.",
			"most (word)ic. Example: Idiot.",
			"most (word)ed up. Example: Mess.",
			"(word)est. Example: Stupid.",
			"(word + last letter, so wordd)iest. Example: Crap."
		]
	),
	Option(
		"binder",
		"Input inflection IF this sentence works: \"You are very (word) bad.\".",
		[
			"(word). Example: Damn.",
			"(word)ing. Example: Fuck."
		]
	),
	Option(
		"comment",
		"Input inflection IF this sentence works: \"What the (word) is this?\".",
		[
			"(word). Example: Hell."
		]
	),
	Option(
		"degree",
		"Input inflection IF this sentence works: \"You are (word) bad person.\".",
		[
			"a (word). Example: Very.",
			"a (word)ly. Example: Real.",
			"an (word)ly. Example: Extreme."
		]
	),
	Option(
		"insult",
		"Input inflection IF this sentence works: \"You are (word).\".",
		[
			"an (word). Example: Idiot.",
			"a (word). Example: Moron.",
			"a (word)er. Example: Fuck."
			"a piece of (word). Example: Shit.",
		]
	),
	Option(
		"object",
		"Input inflection IF this sentence works: \"What's this (word)?\".",
		[
			"(word). Example: Mess."
		]
	),
	Option(
		"state",
		"Input inflection IF this sentence works: \"You are (word) fucking idiot.\".",
		[
			"an (word). Example: Absolute.",
			"a (word). Example: Real.",
			"a (word)ed up. Example: Mess."
		]
	)
])

# Makes an ascii table out of data.
def writeTable(data, names = None, maxLengths = [None]):
	if not names is None:
		data.insert(0, names)
	lengths = []
	for r in range(len(data)):
		for c in range(len(data[r])):
			if c >= len(lengths):
				lengths.append(0)
			maxLength = maxLengths[min(c, len(maxLengths) - 1)]
			if data[r][c] is None: # Makes empty cells empty.
				data[r][c] = ""
			elif not maxLength is None and len(str(data[r][c])) > maxLength: # Cuts off too long cells.
				data[r][c] = str(data[r][c])[:(maxLength)] + "…"
				lengths[c] = maxLength
			elif len(str(data[r][c])) > lengths[c]:
				lengths[c] = len(str(data[r][c]))

	send = ""
	for r in range(len(data)): # TODO: Remove trailing spaces.
		for c in range(len(lengths)):
			send += "| "
			if c < len(data[r]):
				if isinstance(data[r][c], str) and data[r][c] != "#":
					send += data[r][c]
					send += " " * (lengths[c] - len(data[r][c]))
					if data[r][c] == "" or data[r][c][-1] != "…":
						send += " "
				else:
					send += " " * (lengths[c] - len(str(data[r][c])))
					send += str(data[r][c])
					send += " "
			else:
				send += " " * lengths[c]
			if c + 1 == len(lengths):
				send += "|"
				if r + 1 < len(data):
					send += "\n"
					if r == 0 and not names is None:
						for length in lengths:
							send += "| " + ("-" * length) + " "
						send += "|\n"
				else:
					send += " "
	return send

def findEntries(target, library = "customLibrary"):
	query = "WHERE "
	if target.isdigit():
		query += "word IN (SELECT word FROM " + library + " WHERE "
	if library == "customLibrary":
		query += "(server = @0"
	if target.isdigit():
		if library == "customLibrary":
			query += ") "
		query += "ORDER BY word LIMIT 1 OFFSET @1 - 1);"
	else:
		if library == "customLibrary":
			query += " AND "
		else:
			query += "("
		query += "word = @1);"
	return query

def countEntries(query, args = [], library = "customLibrary"):
	cursor = connection.cursor()
	cursor.execute("SELECT row_number() OVER (ORDER BY word), word, count(*) FROM " + library + " " + query, args)
	return cursor.fetchone()

connection = sqlite3.connect("database.sqlite")

# Gathers all column names.
cursor = connection.cursor()
cursor.execute("PRAGMA table_info(defaultLibrary)")
wordTypes = []
for wordType in cursor.fetchall()[2:]:
	wordTypes.append(wordType[1])