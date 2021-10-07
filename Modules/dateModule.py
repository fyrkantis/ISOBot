# External Libraries
import re

months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

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
		
		self.alternatives = []
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
		for i in range(len(self.alternatives)):
			if self.alternatives[i].date == date:
				self.alternatives[i].tags.append(tokens)
				self.alternatives[i].iso.checkTokens(tokens)
				self.iso.compareBools(self.alternatives[i].iso)
				return
		# Adds another dateAlt if one doesn't already exist.
		dateAlt = self.Alternative(date, tokens, self.Iso(tokens, self.lines))
		self.iso.compareBools(dateAlt.iso)
		self.alternatives.append(dateAlt)
	
	# Returns a string of lines with values (or tags if specified) inbetween.
	def writeFormat(self, tags = None):
		inputs = self.inputs
		# Allows inputs to be a class containing both arguments.
		if tags:
			inputs = tags
		send = self.lines[0]
		for i in range(len(inputs)):
			send += inputs[i]
			send += self.lines[i + 1]
		return send
	
	def __str__(self):
		return f"{self.writeFormat()}, with values {self.values} representing {self.tags}, thus all possible formats are {self.alternatives}. {self.iso}"
	
	def __repr__(self):
		return "\n" + str(self) + "\n"
	
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
	class Alternative():
		def __init__(self, date, tokens, iso):
			self.date = date
			self.tags = [tokens]
			self.iso = iso
		
		def __str__(self):
			return f"{self.date} (formatted as {self.tags}) {self.iso}"
		
		def __repr__(self):
			return str(self)