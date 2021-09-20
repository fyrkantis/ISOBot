import discord
from . import dataModule, textModule

# External Libraries
from datetime import datetime
from discord_slash import SlashCommand
from discord_slash.utils.manage_commands import create_choice, create_option

def exportOptions(optionList, extraChoice = None):
	send = []
	for option in optionList.options:
		choices = option.choices.copy()
		if extraChoice:
			choices.insert(0, "None (remove parameter).")
		for i in range(len(choices)):
			choices[i] = create_choice(i, choices[i])
		send.append(create_option(
			name = option.name,
			description = option.description,
			option_type = optionList.option_type,
			required = optionList.required,
			choices = choices))
	return send

def addSlashCommands(client, guild_ids):
	guild_ids = [732240720487776356, 746842558180622396]
	slash = SlashCommand(client, sync_commands = True)

	@slash.subcommand(
		base = "words",
		name = "show",
		description = "I'll show all words, or one specific, from a word library.",
		options = [
			create_option(
				name = "library",
				description = "This \"server\"'s, the \"default\", other \"connected\" server's, \"everything\" combined, or a server's ID.",
				option_type = 3,
				required = True
			),
			create_option(
				name = "target",
				description = "Show a specific word from that library. Write the word, or it's row number #.",
				option_type = 3,
				required = False
			)
		],
		guild_ids = guild_ids
	)
	async def show(ctx, library = "server", target = None): # TODO: Separate libraries from collections (server x's custom library is a library, the default library is a library, 'everything' and 'connected' are collecitons of libraries).
		columns = ["word"] + dataModule.wordTypes

		# Selects query and arguments.
		targetX = "customLibrary WHERE server = @0"
		args = []
		send = "Showing "
		if not target is None: # Checks if a specific word is requested.
			send += "word "
			if target.isdigit():
				send += target + " "
			else:
				send += "\"" + target + "\" "
			send += "from "
		if library.isdigit():
			server = client.get_guild(int(library))
			if server is None:
				await ctx.send("**Invalid server ID**, use the number found when right-clicking a server's icon and selecting the last option.")
				return
			args = [int(library)]
			send += library
			send += " \""
			send += server.name
			send += "\"'s "
		elif library.lower() == "default":
			targetX = "defaultLibrary"
			columns.insert(1, "severity")
			send += "the **default** "
		elif library.lower() == "connected":
			send += "every other **connected** server's "
			await ctx.send("**Error**, not implemented yet.")
			return
		elif library.lower() == "everything": # TODO: Add column for the word's source library and server/severity.
			args = [ctx.guild.id]

			columnString = ""
			for wordType in dataModule.wordTypes:
				columnString += ", "
				columnString += wordType
			targetX = f"(SELECT word{columnString} FROM {targetX} UNION ALL SELECT word{columnString} FROM defaultLibrary)"
			send += "this **server**'s word library, the **default** word library *and* every other **connected** server's "
		elif library == "server":
			args = [ctx.guild.id]
			send += "this **server**'s "
		else:
			await ctx.send("""**Invalid library**, input either:
- *\"server\"* for this server's custom word library.
- *\"default\"* for the default word library.
- *\"connected\"* for all other connected server's custom libraries.
- *\"everything\"* for everything combined.
- Paste a *server ID* for that server's custom word library.""")
			return
		send += "word library:"

		# Generates query.
		query = "SELECT row_number() OVER (ORDER BY word)"
		for column in columns:
			query += ", "
			query += column
		query += " FROM " + targetX
		if not target is None and not target.isdigit(): # Changes query if a word is reqested.
			if library.isdigit() or library.lower() == "server":
				query += " AND"
			else:
				query += " WHERE"
			query += " word = @" + str(len(args))
			args.append(target)
		query += " ORDER BY word"
		if not target is None and target.isdigit(): # Changes query if a word number is reqested.
			query += " LIMIT 1 OFFSET (@" + str(len(args)) + " - 1)"
			args.append(int(target))
		query += ";"
		columns.insert(0, "#")
		
		# Executes query.
		cursor = dataModule.connection.cursor()
		cursor.execute(query, args)
		words = []
		for word in cursor.fetchall():
			words.append(list(word))
		
		# Formats results.
		if len(words) > 1:
			with open("results.txt", "w") as file:
				file.write(f"Contents of library \"{library.lower()}\", as of {str(datetime.utcnow())[:19]} UTC:\n{dataModule.writeTable(words, columns)}")
			with open("results.txt", "rb") as file:
				await ctx.send(send, file = discord.File(file, "libraryContents.txt"))
		else:
			if len(words) > 0:
				send += "\n```\n" + str(textModule.Word(words[0], library.lower())) + "```"
			else:
				send += "\n```\n"
				if target is None:
					send += "There are no words in this library."
				else:
					send += "The word you're looking for could not be found."
				send += "```"
			await ctx.send(send)

	@slash.subcommand(
		base = "words",
		name = "add",
		description = "Add a new word to this server's custom word library, and I'll start using it.",
		options = ([
			create_option(
				name = "word",
				description = "This is the base of the word. Use the other parameters to specify how the word should be used.",
				option_type = 3,
				required = True
			)] + exportOptions(dataModule.optionList)),
		guild_ids = guild_ids
	)
	async def add(ctx, word, **kwargs):
		if len(kwargs) <= 0:
			await ctx.send("""**Too few parameters**, select an option on *at least* one of the parameters after *word*.
Check the parameter descriptions and select all options that fit your word.""")
			return
		
		query = "INSERT INTO customLibrary (word, server"
		for key in kwargs.keys():
			query += ", "
			query += key
		query += ") VALUES (@0, @1"
		for value in kwargs.values():
			query += ", "
			query += str(value)
		query += ");"
		cursor = dataModule.connection.cursor()
		cursor.execute(query, [word, ctx.guild.id])
		cursor.close()
		dataModule.connection.commit()

		send = "Successfully added the word \""
		send += word
		send += "\" to this **server**'s custom word library."
		
		await ctx.send(send)

	@slash.subcommand(
		base = "words",
		name = "update",
		description = "Change the parameters of an already existing word by entering new ones.",
		options = [
			create_option(
				name = "target",
				description = "Either write the word or its row number # in this server's custom word library.",
				option_type = 3,
				required = True
			),
			create_option(
				name = "word",
				description = "This is the base of the word. Use the other parameters to specify how the word should be used.",
				option_type = 3,
				required = False
			)] + exportOptions(dataModule.optionList, True),
		guild_ids = guild_ids
	)
	async def update(ctx, target, **kwargs):
		query = dataModule.findEntries(target)
		check = dataModule.countEntries(query, [ctx.guild.id, target])
		if check[2] == 0:
			send = "**Update aborted**, "
			if target.isdigit():
				send += "word number " + target
			else:
				send += "the word \"" + target + "\""
			send += " doesn't exist in this **server**'s custom word library."
		else:
			send = "Successfully updated word number " + str(check[0]) + " \"" + check[1] + "\" from this **server**'s custom word library to the following values:\n```"
			values = ""
			for index, (key, value) in enumerate(kwargs.items()):
				send += "\n" + key + ": "
				if index > 0:
					values += ", "
				values += key + " = "
				if key == "word":
					values += "\"" + value + "\""
					send += value
				else:
					if value == 0:
						values += "NULL"
						send += "None"
					else:
						values += str(value - 1)
						send += str(value - 1)
			cursor = dataModule.connection.cursor()
			cursor.execute("UPDATE customLibrary SET " + values + " " + query, [ctx.guild.id, target])
			send += "\n```"
		await ctx.send(send)

	@slash.subcommand(
		base = "words",
		name = "delete",
		description = "Delete a word from this server's custom word library, and I'll stop using it.",
		options = [
			create_option(
				name = "target",
				description = "Either write the word or its row number # in this server's custom word library.",
				option_type = 3,
				required = True
			)],
		guild_ids = guild_ids
	)
	async def delete(ctx, target):
		query = dataModule.findEntries(target)
		check = dataModule.countEntries(query, [ctx.guild.id, target])
		if check[2] == 0:
			send = "**Deletion aborted**, "
			if target.isdigit():
				send += "word number " + target
			else:
				send += "the word \"" + target + "\""
			send += " doesn't exist in "
		else:
			send = "Successfully deleted word number " + str(check[0]) + " \"" + check[1] + "\" from "
			cursor = dataModule.connection.cursor()
			cursor.execute("DELETE FROM customLibrary " + query, [ctx.guild.id, target])
			dataModule.connection.commit()
		send += "this **server**'s custom word library."
		await ctx.send(send)

	@slash.subcommand(
		base = "words",
		name = "help",
		description = "AAA! What are theese \"words\" commands, and what do they do?",
		guild_ids = guild_ids
	)
	async def help(ctx):
		await ctx.send("""My messages contain some randomly selected cursewords and insults from my word libraries. If you add your own cursewords and insults to this server's custom word library, I'll start using them in this server. When adding words, make sure to fill in the parameters so I know when to use them and how they should be inflected gramatically.
All current commands are as follows:
- **/words show**, shows the content of a word library (or a single word in it). Write either *\"server\"* for this server's custom word library, *\"default\"* for the default word library, *\"connected\"* for all other connected server's custom word libraries, *\"everything\"* for everything combined, or paste a *server id* for thar server's custom word library. For a specific word, either write the word or its row number # in the selected word library.
- **/words add**, add a new word to this server's custom word library, and I'll start using it. Check the parameter descriptions and select all options that fit your word.
- **/words delete**, delete a word from this server's custom word library, and I'll stop using it. Either write the word or its row number # in this server's custom word library.""")