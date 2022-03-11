from . import dataModule

# External libraries
from copy import deepcopy
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
	def __init__(self, factors = [], divisors = []): # Only used when creating temporary units.
		self.factors = factors
		self.divisors = divisors
	
	def convert(self):
		self.conversion = 1
		for factor in self.factors:
			self.conversion *= factor.conversion
		for divisor in self.divisors:
			self.conversion /= divisor.conversion
	
	def stringParts(self):
		send = ""
		for i, factor in enumerate(self.factors):
			exponent = factor.exponent / factor.internalExponent
			if i > 0:
				send += " "
			if exponent == 2:
				send += "square "
			elif exponent == 3:
				send += "cubic "
			if factor.base != 0:
				foundPrefix = False
				for prefix, value in siPrefixes.items():
					if factor.base == value:
						send += prefix
						foundPrefix = True
						break
			send += pluralUnit(factor.name, factor.inflection)
			if exponent < 1 or exponent > 3:
				send += "^" + str(exponent)
			if factor.base != 0 and not foundPrefix:
				send += "\*10^" + str(factor.base)
				
		if len(self.divisors) > 0:
			if len(self.factors) > 0:
				send += " per "
			else:
				send += "inverse "
			for i, divisor in enumerate(self.divisors):
				exponent = divisor.exponent / divisor.internalExponent
				if i > 0:
					send += " "
				if exponent == 2:
					send += "square "
				elif exponent == 3:
					send += "cubic "
				if i > 0:
					send += pluralUnit(divisor.name, divisor.inflection)
				else:
					send += divisor.name
				if exponent < 1 or exponent > 3:
					send += "^" + str(exponent)
				if divisor.base != 0:
					send += "\*10^" + str(divisor.base)
		return send
	
	class BasePart():
		def __eq__(self, other):
			return self.unitType == other.unitType and self.exponent == other.exponent
		
		def __str__(self):
			return f"{self.name}^({self.exponent}/{self.internalExponent}) * 10^{self.base} {self.unitType}."
		
		def __repr__(self):
			return str(self)
	
	class Part(BasePart):
		def __init__(self, rawInput, base = 0):
			self.rawInput = rawInput
			self.name = ""
			self.inflection = 0
			self.unitType = None
			self.conversion = 1
			self.internalExponent = 1
			self.exponent = 1
			self.base = base
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
					self.internalExponent *= int(types[1])
				elif len(types) >= 2 and types[0].isdigit():
					self.unitType = types[1]
					self.internalExponent *= int(types[0])
				elif len(types) >= 1:
					self.unitType = types[0]
				self.exponent *= self.internalExponent
				self.conversion = result[3] * 10 ** (self.base * self.exponent + result[4]) # Raised to power of 1 divided by exponent because exponent is already included in conversion number.
			else:
				print(f"Couldn't find unit \"{self.rawInput}\" in database.")
	
	class IsoPart(BasePart):
		def __init__(self, part, siPart = {}):
			self.name = siPart["name"]
			self.unitType = part.unitType
			self.inflection = siPart["inflection"]
			self.internalExponent = 1
			self.exponent = part.exponent
			self.base = part.base

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

		# Goes through all parts of the unit and adds sub-units accordingly. TODO: Make 1 meter^-1 and 1 meter * 10^3 possible.
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
					base = 0
					# Prefix			
					if parts[5].lower() in siPrefixes:
						base += siPrefixes[parts[5].lower()]
					elif parts[6].lower() in siSymbols:
						base += siSymbols[parts[6].lower()]
					part = subUnit.Part(parts[7], base)
				self.addSubPart(part, subUnit, dividing)
				if not part.si:
					subUnit.iso.unit = False

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
		self.isoUnit = IsoUnit(unit = self)
	
	# Adds a part to a sub unit and handles the shared lists as well.
	def addSubPart(self, part, subUnit, dividing = False):
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
		return f"{significantFigures(converted)} {self.isoUnit.stringParts()}"
	
	def __str__(self):
		return f"{self.rawInput}, parts: {self.factors} / {self.divisors}, subUnits: {self.subUnits}\nisoUnit: {self.isoUnit}\niso: {self.iso}"

class SubUnit(BaseUnit):
		def __init__(self, rawAmount):
			self.rawAmount = rawAmount
			self.iso = self.Iso()
			self.factors = [] # (subUnit1 + subUnit2) * factor1 * factor2 / (divisor1 * divisor2)
			self.divisors = []

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

class IsoUnit(BaseUnit):
	def __init__(self, factors = [], divisors = [], unit = None):
		self.factors = []
		self.divisors = []
		if not unit is None:
			factors = unit.factors
			divisors = unit.divisors
		for factor in factors:
			self.addIsoPart(factor)
		for divisor in divisors:
			self.addIsoPart(divisor, dividing = True)
	
	def addIsoPart(self, part, dividing = False):
		siPart = siParts.get(part.unitType)
		if part.unitType is None or siPart is None:
			print("ERROR: Unit is missing type.")
			return
		if part.si:
			print("Already SI.")
			isoPart = part
		else:
			isoPart = self.IsoPart(part, siPart)
		
		if not dividing:
			self.factors.append(isoPart)
		else:
			self.divisors.append(isoPart)
	
	def __str__(self):
		return f"{self.factors} / {self.divisors}"

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

#def getPrefix