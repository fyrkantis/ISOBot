from . import dataModule

def printUnits():
	cursor = dataModule.connection.cursor()
	cursor.execute("SELECT * FROM defaultUnits")
	send = dataModule.writeTable(cursor.fetchall())
	cursor.close()
	return send