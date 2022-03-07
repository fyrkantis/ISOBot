import enum
from . import dataModule

# External libraries
import math
import re

siParts = {
	"length": {"name": "meter", "inflection": 0, "symbol": "m"},
	"mass": {"name": "gram", "inflection": 0, "symbol": "g"},
	"energy": {"name": "joule", "inflection": 0, "symbol": "J"},
	"time": {"name": "second", "inflection": 0, "symbol": "s"},
	"force": {"name": "newton", "inflection": 0, "symbol": "N"},
	"effect": {"name": "watt", "inflection": 0, "symbol": "W"},
	"pressure": {"name": "pascal", "inflection": 0, "symbol": "Pa"},
	"frequence": {"name": "hertz", "inflection": 3, "symbol": "Hz"}
}

# Non case-sensitive prefixes.
siPrefixes = {
	"deka": 1, "hecto": 2, "kilo": 3, "mega": 6, "giga": 9, "tera": 12, "peta": 15, "exa": 18, "zetta": 21, "yotta": 24,
	"deci": -1, "centi": -2, "milli": -3, "micro": -6, "nano": -9, "pico": -12, "femto": -15, "atto": -18, "zepto": -21, "yocto": -24
}

# Non case-sensitive prefix symbols.
siSymbols = {
	"da": 1, "h": 2, "k": 3, "g": 9, "t": 12, "e": 18,
	"d": -1, "c": -2, "m": -3, "u": -6, "μ": -6, "n": -9, "n": -9, "f": -15#, "a": -18 TODO: Improve regex capture to handle gal as the gallon symbol, and not gram plus atto liter.
}

# Case-sensitive prefix symbols. TODO: Fix case-sensitive prefix symbols.
#siCaseSymbols = {
#	"M": 6, "P": 15, "Z": 21, "Y": 24,
#	"m": -3, "p": -12, "z": -21, "y": -24
#}

class BaseUnit():
	def __init__(self, factors, divisors): # Only used when creating temporary units.
		self.factors = factors
		self.divisors = divisors
	
	def convert(self):
		self.conversion = 1
		for factor in self.factors:
			self.conversion *= (factor.conversion * 10 ** factor.base) ** factor.exponent
		for divisor in self.divisors:
			self.conversion /= (divisor.conversion * 10 ** divisor.base) ** divisor.exponent
	
	def stringParts(self):
		send = ""
		for i, factor in enumerate(self.factors):
			if i > 0:
				send += " "
			if True:
				send += pluralUnit(factor.name, factor.inflection)
			else:
				send += factor.name
			if factor.exponent != 1:
				send += "^" + str(factor.exponent)
			if factor.base != 0:
				send += "\*10^" + str(factor.base)
				
		if len(self.divisors) > 0:
			send += " per "
			for i, divisor in enumerate(self.divisors):
				if i > 0:
					send += " "
				if i > 0:
					send += pluralUnit(divisor.name, divisor.inflection)
				else:
					send += divisor.name
				if divisor.exponent != 1:
					send += "^" + str(divisor.exponent)
				if divisor.base != 0:
					send += "\*10^" + str(divisor.base)
		return send
	
	class Part():
		def __init__(self, rawInput):
			self.rawInput = rawInput
			self.name = ""
			self.inflection = 0
			self.unitType = None
			self.conversion = 1
			self.exponent = 1
			self.base = 0
			self.si = False

			for siType, siPart in siParts.items():
				if self.rawInput.lower() in [siPart["name"], siPart["symbol"], pluralUnit(siPart["name"], siPart["inflection"])]:
					#print("SI unit.")
					self.name = siPart["name"]
					self.unitType = siType
					self.si = True
					return

			cursor = dataModule.connection.cursor()
			cursor.execute("""SELECT name, inflection, type, conversion, base FROM defaultUnits
WHERE @0 IN (name, pluralUnit(name, inflection), symbol, symbol + "s")
LIMIT 1;""", [self.rawInput])
			result = cursor.fetchone()
			cursor.close()
			if not result is None:
				#print(result)
				self.name = result[0]
				self.inflection = result[1]
				types = result[2].strip().split()
				if len(types) >= 2 and types[1].isdigit(): # I'm not trusting that goddamn database!
					self.unitType = types[0]
					self.exponent *= int(types[1])
				elif len(types) >= 2 and types[0].isdigit():
					self.unitType = types[1]
					self.exponent *= int(types[0])
				elif len(types) >= 1:
					self.unitType = types[0]
				self.conversion = (result[3] * 10 ** result[4]) ** (1 / self.exponent) # Raised to power of 1 divided by exponent because exponent is already included in conversion number.
			else:
				print(f"Couldn't find unit \"{self.rawInput}\" in database.")
		
		def __eq__(self, other):
			return isinstance(other, BaseUnit.Part) and self.unitType == other.unitType and self.exponent == other.exponent
		
		def __str__(self):
			return f"\"{self.rawInput}\" {self.name}^{self.exponent} * 10^{self.base}. Type: {self.unitType}. Conversion: {self.conversion}. SI: {self.si}"
		
		def __repr__(self):
			return f"{self.name}^{self.exponent} * 10^{self.base}. {self.unitType} {self.conversion} {self.si}"

	class Iso():
		def __init__(self):
			self.unit = True
			self.punctuation = True
			self.separators = True
			self.digitGrouping = True

		def __bool__(self):
			return self.unit and self.punctuation and self.separators and self.digitGrouping
		
		def __add__(self, other):
			send = BaseUnit.Iso()
			send.unit = self.unit and other.unit
			send.punctuation = self.punctuation and other.punctuation
			send.separators = self.separators and other.separators
			send.digitGrouping = self.digitGrouping and other.digitGrouping
			return send
		
		def __str__(self):
			return f"Correct unit: {self.unit}, punctuation: {self.punctuation}, separators: {self.separators}, digit grouping: {self.digitGrouping}."

class Unit(BaseUnit):
	def __init__(self, rawInput):
		self.rawInput = rawInput # The full unit as entered.
		self.subUnits = []
		self.iso = self.Iso()
		self.factors = [] # (subUnit1 + subUnit2) * factor1 * factor2 / (divisor1 * divisor2)
		self.divisors = []

		# Goes through all parts of the unit and adds sub-units accordingly.
		capture = r"(?:(?<!\w)(\d+(?:[\.\, ]\d+)*)|(?:\+|plus|and)|(?:\*|a|times|mult\w*)|(\/|\\|per|p|div\w*)|(''?|\")|(?:(?:(sq)|(cub))\w* *)?(?:(?:(" + r"|".join(list(siPrefixes.keys())) + r")|(" + r"|".join(list(siSymbols.keys())) + r")) *)??((?:" + getUnitMatch() + r"))(?:( *squared|(?: *\^ *)?2)|( *cube|(?: *\^ *)?3))?)"
		print(capture)
		dividing = False
		subUnit = None
		for parts in re.findall(capture, self.rawInput, re.IGNORECASE):
			print(parts)
			if parts[0] != "": # Number.
				subUnit = SubUnit(parts[0])
				self.subUnits.append(subUnit)
				dividing = False
			elif subUnit is None:
				continue
			elif parts[2] or parts[7] != "": # Apostrophe(s) or Unit.
				if parts[2] != "": # Apostrophe(s).
					if parts[2] == "'":
						part = subUnit.Part("foot")
					else:# parts[1] == "''" or parts[1] == "\"":
						part = subUnit.Part("inch")
				else: # Unit
					part = subUnit.Part(parts[7])
				self.addDuring(part, subUnit, dividing) # TODO: 5 square inches and 7 feet per second.
				if not part.si:
					subUnit.iso.unit = False

				# Prefix			
				if parts[5].lower() in siPrefixes:
					part.base += siPrefixes[parts[5].lower()]
				elif parts[6].lower() in siSymbols:
					part.base += siSymbols[parts[6].lower()]

				if parts[3] != "" or parts[8] != "": # Squared.
					part.exponent *= 2
				elif parts[4] != "" or parts[9] != "": # Cubed.
					part.exponent *= 3
			elif parts[1] != "": # Divsion.
				dividing = not dividing
			# Addition and multiplication do not matter.
		
		for subUnit in self.subUnits: # TODO: Optimize.
			self.iso += subUnit.iso
			for mainFactor in self.factors:
				while mainFactor in subUnit.factors:
					subUnit.factors.remove(mainFactor)
			for mainDivisor in self.divisors:
				while mainDivisor in subUnit.divisors:
					subUnit.divisors.remove(mainDivisor)
			subUnit.convert()
		self.convert()
	
	# Adds a part to a sub unit and handles the shared lists as well.
	def addDuring(self, part, subUnit, dividing = False):
		if not dividing:
			mainParts = self.factors
			subUnit.factors.append(part)
		else:
			mainParts = self.divisors
			subUnit.divisors.append(part)
		foundInMain = False
		for mainPart in mainParts:
			if part == mainPart:
				foundInMain = True
				if part.conversion != mainPart.conversion or part.base != mainPart.base:
					foundInMain = mainPart
				break
		
		#print(f"foundInMain: {foundInMain}")
		# Values of foundInMain:
		# False, not found in main list and should be added if it's not already in a sub unit.
		# True, found in main list with the same type, nothing needs to be done here.
		# Part instance, found in main list with different type, should be added to sub units and removed from main list.
		
		if not foundInMain is True:
			foundInAny = False
			for unit in self.subUnits:
				if subUnit is unit:
					break
				if not dividing:
					subParts = unit.factors
				else:
					subParts = unit.divisors
				print(subParts)
				found = part in subParts
				if not foundInMain is False:
					if not found:
						subParts.append(mainPart)
				else:
					if found:
						foundInAny = True
						break
			
			#print(f"foundInAny: {foundInAny}")
			if foundInMain is False:
				if not foundInAny:
					mainParts.append(part)
			else:
				mainParts.remove(mainPart)
	
	def isoString(self):
		converted = 0
		for subUnit in self.subUnits:
			converted += subUnit.amount * subUnit.conversion * self.conversion
		return significantFigures(converted)
	
	def __str__(self):
		return f"{self.rawInput}, parts: {self.factors} / {self.divisors}, sub-units: {self.subUnits}\nISO: {self.iso}"

class SubUnit(BaseUnit):
		def __init__(self, rawAmount):
			self.rawAmount = rawAmount
			self.factors = [] # (subUnit1 + subUnit2) * factor1 * factor2 / (divisor1 * divisor2)
			self.divisors = []
			self.iso = self.Iso()

			# Creates self.amount from self.rawAmount, and checks if its iso.
			self.punctuation = self.rawAmount.count(",") <= 0 # "123,456.789"
			
			parts = self.rawAmount.replace(",", ".") # "123.456.789"
			self.separators = parts.count(".") <= 1

			parts = parts.rsplit(".", 1) # ["123.456", "789"]
			if "." in parts[0]:
				self.separators = False
			
			parts[0] = parts[0].replace(".", " ") # ["123 456", "789"]
			for i, part in enumerate(parts[0].split(" ")):
				if i > 0 and not len(part) == 3:
					self.digitGrouping = False
					break
			
			self.amount = int(parts[0].replace(" ", "").replace(" ", "")) # 123456
			if len(parts) > 1:
				self.amount += int(parts[-1]) / 10 ** len(parts[-1]) # 123456 + 0.789 = 123456.789

		def __str__(self):
			return f"\"{self.rawAmount}\", {self.amount} * {self.factors} / {self.divisors}."
		
		def __repr__(self):
			return "\n" + str(self)

def getUnitMatch():
	cursor = dataModule.connection.cursor()
	cursor.execute("SELECT name, inflection, symbol FROM defaultUnits")
	inflections = [[]] # A list of lists of all unit names and prefixes, indexed by inflection.
	symbolString = r""
	siPartsList = []
	for siPart in siParts.values():
		siPartsList.append(list(siPart.values()))
	for unit in cursor.fetchall() + siPartsList:
		while len(inflections) <= unit[1]:
			inflections.append([])
		inflections[unit[1]].append(unit[0])
		if not unit[2] is None:
			symbolString += r"|" + re.escape(unit[2])
	
	unitString = r""
	for inflection, units in enumerate(inflections):
		if len(units) > 0:
			if not unitString == r"":
				unitString += r"|"
			if inflection < 2:
				unitString += r"(?:"
			for i, unit in enumerate(units):
				if i > 0:
					unitString += r"|"
				unitString += re.escape(unit)
			if inflection < 2:
				unitString += r")"
				
			if inflection == 0:
				unitString += r"s?"
			elif inflection == 1:
				unitString += r"(?:es)?"
			elif inflection == 2:
				unitString += r"|"
				for i, unit in enumerate(units):
					if i > 0:
						unitString += r"|"
					unitString += re.escape(unit.replace("o", "e").replace("O", "E"))
	return unitString + symbolString

def getPrefixMatch():
	return r"(?:" + r"|".join(list(siPrefixes.keys()) + list(siSymbols.keys())) + r")"

def getFindPattern():
	return re.compile(r"(?<!\w)((?:\d+(?:[\.\, ]\d+)* *(?:''?|(?:(?:(?:\*|\/|\\|times|a|per|p|(?:div|mult)\w*) *)?(?:(?:square|cubic) *)?(?:" + getPrefixMatch() + r" *)?(?:" + getUnitMatch() + r")(?: *(?:squared?|cubed?)|(?: *\^ *)?(?:2|3))? *)+)(?:\+|plus|and)? *)+)(?!\w)", re.IGNORECASE)

# TODO: Replaced with base 10 ground equation.
# https://www.kite.com/python/answers/how-to-round-a-number-to-significant-digits-in-python
# https://stackoverflow.com/a/55975216/13347795
def significantFigures(value, figures = 3):
	if value == 0:
		return 0
	return f"{round(value, figures - int(math.floor(math.log10(abs(value)))) - 1):g}"

def pluralUnit(name, inflection = 0):
	if inflection == 0 and not name.endswith("s"):
		return name + "s"
	if inflection == 1 and not name.endswith("es"):
		return name + "es"
	if inflection == 2:
		return name.replace("o", "e").replace("O", "E")
	return name
dataModule.connection.create_function("pluralUnit", 2, pluralUnit)