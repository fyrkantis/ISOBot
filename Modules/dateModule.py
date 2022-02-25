# External Libraries
import re

months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
#(?<!(?P<look>(?P<line>[\/\\\-])|[\d\w\+\*=]))(?P<first>(?P<value>(?P<number>\d{1,4})|(?P<month>jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*))(?P<second>(?P<middle> *(?:\g<line>|(?:st|nd|rd|th)?(?: *(,|of|month|year)?)*) *)\g<value>)(?P<third>\g<middle>\g<value>)?(?!\g<look>)
pattern = re.compile(r"(?<!(?:[\/\\\-\d\w\+\*=]))(?:(?P<number1>\d{1,4})|(?P<month1>(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*))(?P<middle1> *(?:[\/\\\-]|(?:st|nd|rd|th)?(?: +(?:,|of|the|month|year)?)*) *)(?:(?P<number2>\d{1,4})|(?P<month2>(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*))(?P<middle2> *(?:[\/\\\-]|(?:st|nd|rd|th)?(?: +(?:,|of|the|month|year)?)*) *)(?:(?P<number3>\d{1,4})|(?P<month3>(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*))?(?!(?:[\/\\\-\d\w\+\*=]))", re.IGNORECASE)

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
	def __init__(self, raw):
		self.inputs = [] # Years, months and days saved as strings.
		self.values = [] # Years, months and days saved as numbers.
		self.tags = [] # Tags consist of tokens, ["YYYY", "MM", "DD"] is a tag, "YYYY" is a token.
		self.lines = [] # Everything between the numbers or month names.
		self.definetlyDate = None

		for i, parts in enumerate([raw[:2], raw[3:5], raw[6:]]):
			if parts[0] != "":
				self.addNumber(parts[0])
			elif parts[1] != "":
				self.addText(parts[1])
			else:
				break
			if i == 1:
				self.lines.append(raw[2])
			elif i == 2:
				self.lines.append(raw[5])
		
		if len(self.inputs) >= 3:
			self.definetlyDate = True
		
		self.alternatives = []
		self.iso = self.Iso(lines = self.lines) # Everything that's wrong with all alternatives no matter what.

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
		
		if len(self.alternatives) <= 0:
			self.definetlyDate = False
	
	def addNumber(self, part):
		self.inputs.append(part)
		value = int(part)
		self.values.append(value)
		tag = ["Y" * len(part)] # List of possible meanings, could always be a year.

		# Looks for other fitting tags.
		if len(part) <= 2:
			if value <= 31:
				if value <= 12:
					tag.append("M" * len(part))
				tag.append("D" * len(part))
		else:
			self.definetlyDate = True
		self.tags.append(tag)
	
	def addText(self, part):
		self.inputs.append(part)
		for i, month in enumerate(months): # TODO: Add case for written "first", "second", and so on. (frst, scnd)
			if part[:3].lower() == month[:3].lower():
				self.values.append(i + 1)
				if len(part) <= 3:
					self.tags.append(["Mon"])
				else:
					self.tags.append(["Month"])
				self.definetlyDate = True
				return
		self.values.append(0) # TODO: Better error handling.
		self.tags.append([])

	def addAlt(self, tokens): # TODO: Rethink how incorrect lines are handled.
		date = Date(tokens, self.values, self.inputs)
		if date.valid is False:
			return

		# Tries to find a fitting alternative for the tag to be sorted into.
		for alternative in self.alternatives:
			if alternative.date == date:
				alternative.tags.append(tokens)
				alternative.iso.checkTokens(tokens)
				self.iso += alternative.iso
				self.iso.order = self.iso.order or alternative.iso.order
				return
		
		# Adds another alternative if one doesn't already exist.
		alternative = self.Alternative(date, tokens, self.Iso(tokens, self.lines))
		self.iso += alternative.iso
		self.iso.order = self.iso.order or alternative.iso.order
		self.alternatives.append(alternative)
	
	# Returns a string of how the date was originally written.
	def write(self, tags = None):
		inputs = self.inputs
		# Allows inputs to be a class containing both arguments.
		if tags:
			inputs = tags
		send = ""
		for i, input in enumerate(inputs):
			send += input
			if i < len(self.lines):
				send += self.lines[i]
		return send
	
	def __str__(self):
		return f"{self.write()}, with values {self.values} representing {self.tags}, thus all possible formats are {self.alternatives}. {self.iso}"
	
	def __repr__(self):
		return "\n" + str(self) + "\n"
	
	# An analysis of how iso-8601 compliant a date format could be.
	class Iso():
		def __init__(self, tokens = None, lines = None):
			self.order = False # Assumes the order is wrong.
			self.types = True
			self.lines = True
			self.spaces = True

			if not tokens is None:
				self.checkTokens(tokens)
			if not lines is None:
				self.checkLines(lines)

		def checkTokens(self, tokens):
			# Checks if the tag order is correct.
			if not self.order and (len(tokens) == 3 and tokens[0][0] == "Y" and tokens[1][0] == "M" and tokens[2][0] == "D") or (len(tokens) == 2 and (tokens[0][0] == "Y" and tokens[1][0] == "M") or (tokens[0][0] == "M" and tokens[0][0] == "D")):
				self.order = True
			
			# Checks if the tag lengths are correct. TODO: Fix detection for written months.
			if self.types:
				for token in tokens:
					if (token[0] == "Y" and len(token) != 4) or ((token[0] == "M" or token[0] == "D") and len(token) != 2):
						self.types = False
						break

		def checkLines(self, lines):
			# Checks if all the lines are correct.
			if self.lines or self.spaces:
				for line in lines:
					if line.strip() == "-":
						if line != "-":
							self.spaces = False
					else:
						self.lines = False
		
		# Updates self so that it also applies to other iso. Order is omitted.
		def __add__(self, other):
			send = DateFormat.Iso()
			send.order = self.order
			send.types = self.types and other.types
			send.lines = self.lines and other.lines
			send.spaces = self.spaces and other.spaces
			return send
		
		# Returns if iso is possible
		def __bool__(self):
			return self.order and self.types and self.lines and self.spaces
		
		def __str__(self):
			return f"Correct order: {self.order}, types: {self.types}, lines: {self.lines} and spaces: {self.spaces}."
	
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