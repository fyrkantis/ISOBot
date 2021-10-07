from . import dataModule

class UnitType():
	def __init__(self, whole):
		self.whole = whole
		self.iso = False
	
	def write(self):
		return f"{self.whole[0]} {self.whole[2]}"

def generateCapture():
	cursor = dataModule.connection.cursor()
	cursor.execute("SELECT name, inflection FROM defaultUnits")
	inflections = []
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
	return "(\\d+([\\.\\,]\\d+)?) *(((meter|gram|joule|second|pascal)s?)|(" + unitString + "))"