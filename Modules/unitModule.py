from . import dataModule

class UnitType():
	def __init__(self, whole):
		print(whole)
		self.name = whole[3]
		self.iso = self.Iso()

		# Gradually converts amount while checking how its formatted.
		self.amount = whole[1] # "123,456.789"
		self.iso.punctuation = self.amount.count(",") <= 0

		self.amount = self.amount.replace(",", ".") # "123.456.789"
		self.iso.digitGrouping = self.amount.count(".") <= 1

		self.amount = self.amount.rsplit(".", 1) # ["123.456", "789"]
		self.amount = int(self.amount[0].replace(".", "")) + int(self.amount[-1]) / 10 ** len(self.amount[-1]) # 123456 + 0.789 = 123456.789
	
	def write(self):
		return f"{self.amount} {self.name}"
	
	class Iso():
		def __init__(self):
			self.punctuation = False
			self.digitGrouping = False
		
		def __bool__(self):
			return self.punctuation and self.digitGrouping
		
		def __str__(self):
			return f"Correct punctuation: {self.punctuation}, digit grouping: {self.digitGrouping}."

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
	return "((\\d+([\\.\\, ]\\d+)*) *(((meter|gram|joule|second|pascal)s?)|(" + unitString + ")))"