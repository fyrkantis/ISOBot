# External Libraries
import sqlite3

print("Hello from dataModule.py")

# Makes an ascii table out of data.
def writeTable(data, names = None, maxLengths = None):
	if not names is None:
		data.insert(0, names)
	lengths = []
	for r in range(len(data)):
		for c in range(len(data[r])):
			if c >= len(lengths):
				lengths.append(0)
			
			if data[r][c] is None: # Makes empty cells empty.
				data[r][c] = ""
			elif not maxLengths is None and len(str(data[r][c])) > maxLengths[min(c, len(maxLengths) - 1)]: # Cuts off too long cells.
				data[r][c] = str(data[r][c])[:(maxLengths[(min(c, len(maxLengths) - 1))] - 1)] + "…"
			
			if len(str(data[r][c])) > lengths[c]:
				lengths[c] = len(str(data[r][c]))
	send = ""
	for r in range(len(data)):
		for c in range(len(lengths)):
			send += "|"
			if c < len(data[r]):
				if isinstance(data[r][c], str):
					send += data[r][c]
				send += " " * (lengths[c] - len(str(data[r][c])))
				if not isinstance(data[r][c], str):
					send += str(data[r][c])
			else:
				send += " " * lengths[c]
			#send += " "
			if c + 1 == len(lengths):
				send += "|"
				if r + 1 < len(data):
					send += "\n"
					if r == 0 and not names is None:
						for length in lengths:
							send += "|" + ("-" * length)
						send += "|\n"
	return send

connection = sqlite3.connect("database.sqlite")