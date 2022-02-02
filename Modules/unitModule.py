from . import dataModule

# External libraries
import math
import re

siUnits = {
	"length": "meter",
	"mass": "gram",
	"energy": "Joule",
	"time": "second",
	"force": "Newton",
	"power": "Watt"
}

siPrefixes = {
	 "kilo": 3,   "mega": 6,  "giga": 9,  "tera": 12,   "peta": 15,   "exa": 18,  "zetta": 21,  "yotta": 24,
	"milli": -3, "micro": -6, "nano": -9, "pico": -12, "femto": -15, "atto": -18, "zepto": -21, "yocto": -24
}

class BaseUnit():
	rawAmount = None # String of the amount as inputted.
	name = None # Name of the unit.
	dividents = [] # If there are many units, they are arranged as dividents / divisors.
	divisors = []
	amount = None # rawAmount as a number.
	conversion = 1 # This multiplied by the amount is the amount in the corresponding SI unit.
	unitType = None # Shorthand for if this is a unit of lenght, mass or other.
	
	def selectSelf(self):
		cursor = dataModule.connection.cursor()
		cursor.execute("""SELECT type, conversion, base FROM defaultUnits
WHERE @0 IN (name, pluralUnit(name, inflection), prefix, prefix + "s")
LIMIT 1;""", [self.name])
		result = cursor.fetchone()
		cursor.close()
		if not result is None:
			self.unitType = result[0]
			self.conversion = result[1] * 10 ** result[2]
		else:
			print(f"Couldn't find unit \"{self.name}\" in database.")

class Unit(BaseUnit):
	def __init__(self, whole):
		print(whole)
		self.rawAmount = whole[0] # Saves the unit amount.
		self.name = whole[2]
		self.iso = self.Iso()
		self.iso.convertAmount(self) # Creates self.amount from self.rawAmount, and checks if its iso.
		self.secondUnit = None # This is a special case for 5'6'' and similar.

		if whole[2] in ["\'", "\'\'"]:
			self.iso.unit = False
			if self.name == "\'":
				self.dividents.append("foot")
			elif self.name in ["\'\'", "\""]:
				self.dividents.append("inch")

			self.secondUnit = self.iso.convertAmount(self.SecondUnit(whole[3], whole[4]))
			if self.secondUnit.name == "":
				if self.name == "foot":
					self.secondUnit.dividents.append("inch")
				else:
					self.secondUnit.dividents.append("foot")
			self.secondUnit.selectSelf()
		else:
			# Adds all dates.
			for parts in re.findall(r"(?:(?: *(square|cubic))? *(" + getUnitMatch() + r")(?: *(squared|cube)|( *\^ *)?(2|3))?(?: *(\*|\/|times|(?:p|div|mult)\w*))?)", self.name, re.IGNORECASE):
				print(parts)
			# Checks if the unit could be SI.
			self.iso.unit = False
			for key, value in siUnits.items():
				if self.name == value or self.name == pluralUnit(value):
					self.iso.unit = True
					self.unitType = key
					break
		
		if self.unitType is None:
			self.selectSelf()
	
	def isoString(self):
		total = self.amount * self.conversion
		if not self.secondUnit is None:
			total += self.secondUnit.amount * self.secondUnit.conversion
		return f"{significantFigures(total)} {siUnits[self.unitType]}s"
	
	def write(self):
		if self.secondUnit is None:
			return f"{self.rawAmount} {self.name}"
		else:
			return f"{self.rawAmount} {self.name} {self.secondUnit.write()}"
	
	def __str__(self):
		return f"\"{self.write()}\" {self.amount} {self.unitType} unit(s) with conversion {self.conversion}.\nSecond unit: {self.secondUnit}\n{self.iso}"
	
	class SecondUnit(BaseUnit):
		def __init__(self, rawAmount, name):
			self.rawAmount = rawAmount
			self.name = name
			self.dividents = []
			if self.name == "\'":
				self.dividents.append("foot")
			elif self.name in ["\'\'", "\""]:
				self.dividents.append("inch")
		
		def write(self):
			return f"{self.rawAmount} {self.name}"
		
		def __str__(self):
			return f"\"{self.write()}\" {self.amount} {self.unitType} sub unit(s) with conversion {self.conversion}."
	
	class Iso():
		unit = None
		punctuation = None
		separators = None
		digitGrouping = None
		
		# Converts rawAmount to amount while checking how its formatted.
		def convertAmount(self, target): # "123,456.789"
			self.punctuation = target.rawAmount.count(",") <= 0
			
			parts = target.rawAmount.replace(",", ".") # "123.456.789"
			self.separators = parts.count(".") <= 1

			parts = parts.rsplit(".", 1) # ["123.456", "789"]
			if "." in parts[0]:
				self.separators = False
			
			self.digitGrouping = True
			parts[0] = parts[0].replace(".", " ") # ["123 456", "789"]
			for i, part in enumerate(parts[0].split(" ")):
				if i > 0 and not len(part) == 3:
					self.digitGrouping = False
					break
			
			target.amount = int(parts[0].replace(" ", "").replace(" ", "")) # 123456
			if len(parts) > 1:
				target.amount += int(parts[-1]) / 10 ** len(parts[-1]) # 123456 + 0.789 = 123456.789
			return target

		def __bool__(self):
			return self.unit and self.punctuation and self.separators and self.digitGrouping
		
		def __str__(self):
			return f"Correct unit: {self.unit}, punctuation: {self.punctuation}, separators: {self.separators}, digit grouping: {self.digitGrouping}."

def getUnitMatch():
	cursor = dataModule.connection.cursor()
	cursor.execute("SELECT name, inflection, prefix FROM defaultUnits")
	inflections = [[]] # A list of lists of all unit names and prefixes, indexed by inflection.
	prefixString = r""
	for unit in siUnits.values():
		inflections[0].append(unit)
		prefixString += r"|" + re.escape(unit[0])
	for unit in cursor.fetchall():
		while len(inflections) <= unit[1]:
			inflections.append([])
		inflections[unit[1]].append(unit[0])
		if not unit[2] is None:
			prefixString += r"|" + re.escape(unit[2])
	
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
	# (?<!\w)(\d+(?:[\.\, ]\d+)*) *(square|cubic)? *() *(squared|cube|(?:\^ *)?(2|3))?( *(\*|\/|times|(p|div|mult)\w*) *())?(?!\w)
	# (?<!\w)(\d+(?:[\.\, ]\d+)*)(( *(''?)(?: *(\d+(?:[\.\, ]\d+)*)(?: *(''?))?)?)|(?:(?: *(?:square|cubic))? *(?:meters?)(?: *(?:squared|cube|\^? *(?:2|3)))?(?: *(?:\*|\/|times|(?:p|div|mult)\w*))?)+)(?!\w)
	#final = r"(?<!\w)(\d+(?:[\.\, ]\d+)*) *(square|cubic)? *(''?|" + unitString + prefixString + r") *((\d+(?:[\.\, ]\d+)*) *(''?)|(squared|cube|(?:\^ *)?(2|3))?"
	#amount = 2
	#unitPart = r" *((\*|\/|times|(p|div|mult)\w* *)(square|cubic)? *(" + unitString + prefixString + r") *(squared|cube|(?:\^ *)?(2|3)"
	#final += unitPart * (amount - 1) + r")?" * (amount) + r")(?!\w)"
	#return re.compile(r"(?<!\w)(\d+(?:[\.\, ]\d+)*) *(" + unitString + prefixString + r"|(''?)(?: *(\d+(?:[\.\, ]\d+)*) *(''?)?)?)(?!\w)", re.IGNORECASE)
	return unitString + prefixString

def getFindPattern():
	return re.compile(r"(?<!\w)(\d+(?:[\.\, ]\d+)*)( *(''?)(?: *(\d+(?:[\.\, ]\d+)*)(?: *(''?))?)?|(?:(?: *(?:square|cubic))? *(?:" + getUnitMatch() + r")(?: *(?:squared|cube)|( *\^ *)?(?:2|3))?(?: *(?:\*|\/|times|(?:p|div|mult)\w*))?)+)(?!\w)", re.IGNORECASE)

def getSiUnit(unitType):
	if unitType == "area":
		return "square " + siUnits["length"]
	elif unitType == "volume":
		return "cubic " + siUnits["length"]
	return siUnits[unitType]

# Temporary solution, should be replaced with base 10 ground equation.
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

# Probably unnecessary.
#def matchAny(checkString, target):
#	if not checkString is None:
#		for element in checkString.split():
#			if element == target:
#				return True
#	return False
#dataModule.connection.create_function("matchAny", 2, matchAny)