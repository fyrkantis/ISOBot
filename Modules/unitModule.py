from . import dataModule

# External libraries
import math

siUnits = {
	"length": "meter",
	"mass": "gram",
	"energy": "joule",
	"time": "second",
	"pressure": "pascal",
	"power": "watt"
}

siPrefixes = {
	 "kilo": 3,   "mega": 6,  "giga": 9,  "tera": 12,   "peta": 15,   "exa": 18,  "zetta": 21,  "yotta": 24,
	"milli": -3, "micro": -6, "nano": -9, "pico": -12, "femto": -15, "atto": -18, "zepto": -21, "yocto": -24
}

class UnitType():
	def __init__(self, whole):
		print(whole)
		self.name = whole[3]
		self.iso = self.Iso()
		self.iso.unit = False

		# Checks if the unit could be SI.
		for value in siUnits.values():
			if self.name == value or self.name == pluralUnit(value):
				self.iso.unit = True
				break

		# Gradually converts amount while checking how its formatted.
		self.input = whole[1] # "123,456.789"
		self.iso.punctuation = self.input.count(",") <= 0

		self.amount = self.input.replace(",", ".") # "123.456.789"
		self.iso.digitGrouping = self.amount.count(".") <= 1

		self.amount = self.amount.rsplit(".", 1) # ["123.456", "789"]
		self.amount = int(self.amount[0].replace(".", "")) + int(self.amount[-1]) / 10 ** len(self.amount[-1]) # 123456 + 0.789 = 123456.789
	
	def write(self):
		return f"{self.input} {self.name}"
	
	def isoString(self):
		if self.iso.unit:
			return f"{self.amount} {pluralUnit(self.name)}"
		else:
			cursor = dataModule.connection.cursor()
			cursor.execute(f"""SELECT type, conversion, base FROM defaultUnits
WHERE @0 IN (name, pluralUnit(name, inflection), prefix)
LIMIT 1;""", [self.name])
			result = cursor.fetchone()
			if result is None:
				print(f"ERROR: Couldn't find \"{self.name}\" in database.")
				return f"ERROR {self.name}"
			cursor.close()
			return f"{significantFigures(self.amount * result[1] * 10 ** result[2])} {pluralUnit(getSiUnit(result[0]))}"
	
	def __str__(self):
		return self.write()
	
	class Iso():
		def __init__(self):
			self.unit = False
			self.punctuation = False
			self.digitGrouping = False
		
		def __bool__(self):
			return self.unit and self.punctuation and self.digitGrouping
		
		def __str__(self):
			return f"Correct unit: {self.unit}, punctuation: {self.punctuation}, digit grouping: {self.digitGrouping}."

def generateCapture():
	cursor = dataModule.connection.cursor()
	cursor.execute("SELECT name, inflection, prefix FROM defaultUnits")
	inflections = [] # A list of lists of all unit names and prefixes, indexed by inflection.
	prefixes = [] # A list of all prefixes.
	for unit in cursor.fetchall():
		while len(inflections) <= unit[1]:
			inflections.append([])
		inflections[unit[1]].append(unit[0])
		if not unit[2] is None:
			for prefix in unit[2].split():
				prefixes.append(prefix)

	unitString = ""
	for inflection, units in enumerate(inflections):
		if len(units) > 0:
			if not unitString == "":
				unitString += r"|"
			unitString += r"("
			for i, unit in enumerate(units):
				if i > 0:
					unitString += r"|"
				unitString += unit
			unitString += r")"
			if inflection == 0:
				unitString += r"s?"
			elif inflection == 1:
				unitString += r"(es)?"
			elif inflection == 2:
				unitString += r"|("
				for i, unit in enumerate(units):
					if i > 0:
						unitString += r"|"
					unitString += unit.replace("o", "e").replace("O", "E")
				unitString += r")"

	return r"((\d+([\.\, ]\d+)*) *(((" + r"|".join(siUnits.values()) + r")s?)|(" + unitString + r")|(" + r"|".join(prefixes) + r")))"

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