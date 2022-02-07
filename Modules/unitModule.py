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
	factors = [] # (subUnit1 + subUnit2) * factor1 * factor2 / (divisor1 * divisor2)
	divisors = []
	iso = None

	class Part():
		def __init__(self, name):
			self.name = name
			self.exponent = 1
			self.si = False
		
		def __str__(self):
			if self.exponent == 1:
				return self.name
			else:
				return self.name + f"^{self.exponent}"
		def __repr__(self):
			return str(self)

	class Iso():
		unit = True
		punctuation = True
		separators = True
		digitGrouping = True
		
		# Converts rawAmount to amount while checking how its formatted.
		def convertAmount(self, target): # "123,456.789"
			self.punctuation = target.rawAmount.count(",") <= 0
			
			parts = target.rawAmount.replace(",", ".") # "123.456.789"
			self.separators = parts.count(".") <= 1

			parts = parts.rsplit(".", 1) # ["123.456", "789"]
			if "." in parts[0]:
				self.separators = False
			
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

class Unit(BaseUnit):
	def __init__(self, rawInput):
		self.rawInput = rawInput # The full unit as entered.
		self.subUnits = []
		self.iso = self.Iso()

		capture = r"(?<!\w)(\d+(?:[\.\, ]\d+)*)|(''?|\")|(?:(?:(sq)|(cub))\w* *)?((?:" + getUnitMatch() + r"))(?:( *squared|(?: *\^ *)?2)|( *cube|(?: *\^ *)?3))?|(\+|plus|and)|(?:\*|a|times|mult\w*)|(\/|\\|(?:div|p)\w*)(?!\w)"
		subUnit = None
		dividing = False
		for parts in re.findall(capture, self.rawInput, re.IGNORECASE):
			if parts[0] != "": # Number.
				subUnit = SubUnit(parts[0])
				self.subUnits.append(subUnit)
				dividing = False
			elif subUnit is None:
				continue
			elif parts[1] != "": # Apostrophe(s).
				if parts[1] == "'":
					subUnit.factors.append(self.Part("foot"))
				elif parts[1] == "''" or parts[1] == "\"":
					subUnit.factors.append(self.Part("inch"))
			elif parts[4] != "": # Unit.
				part = self.Part(parts[4])
				if parts[2] != "" or parts[5] != "": # Squared.
					part.exponent = 2
				elif parts[3] != "" or parts[6] != "": # Cubed.
					part.exponent = 3
				if not dividing:
					subUnit.factors.append(part)
				else:
					subUnit.divisors.append(part)
			elif parts[7] != "": # Addition.
				subUnit = None
			elif parts[8] != "": # Divsion.
				dividing = True
	
	def __str__(self):
		return f"{self.rawInput}, sub-units: {self.subUnits}.\nISO: {self.iso}"

class SubUnit(BaseUnit):
		def __init__(self, rawAmount):
			self.rawAmount = rawAmount
			self.iso = self.Iso()
			self.iso.convertAmount(self) # Creates self.amount from self.rawAmount, and checks if its iso.
			
#			cursor = dataModule.connection.cursor()
#			cursor.execute("""SELECT type, conversion, base FROM defaultUnits
#WHERE @0 IN (name, pluralUnit(name, inflection), prefix, prefix + "s")
#LIMIT 1;""", [self.name])
#			result = cursor.fetchone()
#			cursor.close()
#			if not result is None:
#				print(result)
#				self.unitType = result[0]
#				self.conversion = (result[1] * 10 ** result[2]) ** self.exponent
#			else:
#				print(f"Couldn't find unit \"{self.name}\" in database.")
		
		def __str__(self):
			return f"\"{self.rawAmount}\", {self.amount} * {self.factors} / {self.divisors}."
		
		def __repr__(self):
			return "\n" + str(self)

class UnitX():
	def __init__(self, whole):
		self.rawAmount = whole[0] # Saves the unit amount.
		self.name = whole[1]
		self.iso = self.Iso()
		self.iso.convertAmount(self) # Creates self.amount from self.rawAmount, and checks if its iso.
		self.secondUnit = None # This is a special case for 5'6'' and similar.
		print(self.name)

		if whole[2] in ["\'", "\'\'"]: # TODO: Double check this.
			self.iso.unit = False
			#if self.name == "\'":
			#	self.dividents.append("foot")
			#elif self.name in ["\'\'", "\""]:
			#	self.dividents.append("inch")

			self.secondUnit = self.iso.convertAmount(self.SecondUnit(whole[3], whole[4]))
			if self.secondUnit.name == "":
				if self.name == "foot":
					self.secondUnit.dividents.append("inch")
				else:
					self.secondUnit.dividents.append("foot")
			self.secondUnit.selectSelf()
		
		dividing = False
		for parts in re.findall(r"(?<!\w)(?:(\d+(?:[\.\, ]\d+)*)|(''?|\")|((?:" + getUnitMatch() + r")|(squared?|\^ *2)|(cube(?:d|ic)?|\^ *3)|(\+|plus|and)|(\*|a|times|mult\w*)|(\/|\\|(?:div|p)\w*))(?!\w)", self.name, re.IGNORECASE):
			print(f"Parts{parts}")

			unitPart = self.UnitPart(parts)
			self.conversion *= unitPart.conversion
			print(unitPart)
			if self.iso.unit is None and unitPart.si:
				self.iso.unit = True
			elif not unitPart.si:
				self.iso.unit = False
			if not dividing:
				
				self.dividents.append(unitPart)
			else:
				self.divisors.append(unitPart)
			if not dividing and parts[5].startswith(("p", "div", "/", "\\")):
				dividing = True
	
	def isoString(self):
		total = self.amount * self.conversion
		if not self.secondUnit is None:
			total += self.secondUnit.amount * self.secondUnit.conversion
		return f"{significantFigures(total)} things"
	
	def unitTypeString(self):
		return "Somethin"
	
	def write(self):
		if self.secondUnit is None:
			return f"{self.rawAmount} {self.name}"
		else:
			return f"{self.rawAmount} {self.name} {self.secondUnit.write()}"
	
	def __str__(self):
		return f"\"{self.write()}\" {self.amount} unit with conversion {self.conversion}.\nDividents: {self.dividents}.\nDivisors: {self.divisors}.\nSecond unit: {self.secondUnit}\n{self.iso}"
	
	class SecondUnitX():
		def __init__(self, rawAmount, name):
			self.rawAmount = rawAmount
			self.name = name
			self.dividents = []
			#if self.name == "\'":
			#	self.dividents.append("foot")
			#elif self.name in ["\'\'", "\""]:
			#	self.dividents.append("inch")
		
		def write(self):
			return f"{self.rawAmount} {self.name}"
		
		def __str__(self):
			return f"\"{self.write()}\" {self.amount} {self.unitType} sub unit(s) with conversion {self.conversion}."

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
	capture = r"(?<!\w)((?:\d+(?:[\.\, ]\d+)* *(?:''?|(?:(?:(?:square|cubic) *)?(?:" + getUnitMatch() + r")(?: *(?:squared?|cubed?)|(?: *\^ *)?(?:2|3))?(?: *(?:\*|\/|\\|\+|times|plus|and|a|(?:p|div|mult)\w*))? *)+) *)+)(?!\w)"
	print(capture)
	return re.compile(capture, re.IGNORECASE)

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