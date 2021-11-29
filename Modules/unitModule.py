from . import dataModule

siUnits = {
	"length": "meter",
	"mass": "gram",
	"energy": "joule",
	"time": "second",
	"pressure": "pascal"
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
		return f"{self.input} {pluralUnit(self.name, 0)}"
	
	def isoString(self):
		if self.iso.unit:
			return f"{self.amount} {pluralUnit(self.name)}"
		else:
			cursor = dataModule.connection.cursor()
			cursor.execute(f"""SELECT type, conversion, base FROM defaultUnits WHERE (name = @0 OR pluralUnit(name, inflection) = @0) LIMIT 1;""", [self.name])
			result = cursor.fetchone()
			if result is None:
				print(f"ERROR: Couldn't find \"{self.name}\" in database.")
				return f"ERROR {self.name}"
			cursor.close()
			return f"{self.amount * result[1] * 10 ** result[2]} {pluralUnit(siUnits[result[0]])}"
	
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
	cursor.execute("SELECT name, inflection FROM defaultUnits")
	inflections = [] # A list of lists of all unit names, indexed by inflection.
	for unit in cursor.fetchall():
		while len(inflections) <= unit[1]:
			inflections.append([])
		inflections[unit[1]].append(unit[0])
	unitString = ""
	for inflection, units in enumerate(inflections):
		if len(units) > 0:
			if not unitString == "":
				unitString += "|"
			unitString += "("
			for i, unit in enumerate(units):
				if i > 0:
					unitString += "|"
				unitString += unit
			unitString += ")"
			if inflection == 0:
				unitString += "s?"
			elif inflection == 1:
				unitString += "(es)?"
			elif inflection == 2:
				unitString += "|("
				for i, unit in enumerate(units):
					if i > 0:
						unitString += "|"
					unitString += unit.replace("o", "e").replace("O", "E")
				unitString += ")"
	return f"((\\d+([\\.\\, ]\\d+)*) *((({'|'.join(siUnits.values())})s?)|({unitString})))"

def pluralUnit(name, inflection = 0):
	if inflection == 0 and not name.endswith("s"):
		return name + "s"
	elif inflection == 1 and not name.endswith("es"):
		return name + "es"
	elif inflection == 2:
		return name.replace("o", "e").replace("O", "E")
	else:
		return name

dataModule.connection.create_function("pluralUnit", 2, pluralUnit)