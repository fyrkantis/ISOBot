import discord
from . import dataModule, textModule

# External Libraries
from datetime import datetime
from discord_slash import SlashCommand
from discord_slash.utils.manage_commands import create_choice, create_option

# TODO: Shorten and automatically pick examples.
wordParameters = [
create_option(
	name = "adjective",
	description = "Input inflection IF this sentence works: \"You are the (word) person ever.\".",
	option_type = 4,
	required = False,
	choices = [
		create_choice(name = "most (word). Example: Devoid.", value = 0),
		create_choice(name = "most (word)ic. Example: Idiot.", value = 1),
		create_choice(name = "most (word)ed up. Example: Mess.", value = 3),
		create_choice(name = "(word)est. Example: Stupid.", value = 4),
		create_choice(name = "(word + last letter, so wordd)iest. Example: Crap.", value = 5)
	]
),
create_option(
	name = "binder",
	description = "Input inflection IF this sentence works: \"You are very (word) bad.\".",
	option_type = 4,
	required = False,
	choices = [
		create_choice(name = "(word). Example: Damn.", value = 0),
		create_choice(name = "(word)ing. Example: Fuck.", value = 1)
	]
),
create_option(
	name = "comment",
	description = "Input inflection IF this sentence works: \"What the (word) is this?\".",
	option_type = 4,
	required = False,
	choices = [
		create_choice(name = "(word). Example: Hell.", value = 0)
	]
),
create_option(
	name = "degree",
	description = "Input inflection IF this sentence works: \"You are (word) bad person.\".",
	option_type = 4,
	required = False,
	choices = [
		create_choice(name = "a (word). Example: Very.", value = 0),
		create_choice(name = "a (word)ly. Example: Real.", value = 1),
		create_choice(name = "an (word)ly. Example: Extreme.", value = 2)
	]
),
create_option(
	name = "insult",
	description = "Input inflection IF this sentence works: \"You are (word).\".",
	option_type = 4,
	required = False,
	choices = [
		create_choice(name = "an (word). Example: Idiot.", value = 0),
		create_choice(name = "a (word). Example: Moron.", value = 1),
		create_choice(name = "a (word)er. Example: Fuck.", value = 2),
		create_choice(name = "a piece of (word). Example: Shit.", value = 2)
	]
),
create_option(
	name = "object",
	description = "Input inflection IF this sentence works: \"What's this (word)?\".",
	option_type = 4,
	required = False,
	choices = [
		create_choice(name = "(word). Example: Mess.", value = 0)
	]
),
create_option(
	name = "state",
	description = "Input inflection IF this sentence works: \"You are (word) fucking idiot.\".",
	option_type = 4,
	required = False,
	choices = [
		create_choice(name = "an (word). Example: Absolute.", value = 0),
		create_choice(name = "a (word). Example: Real.", value = 1),
		create_choice(name = "a (word)ed up. Example: Mess.", value = 2)
	]
)]

def addSlashCommands(client):
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
				name = "word",
				description = "Show a specific word from that library. Write the word, or it's row number #.",
				option_type = 3,
				required = False
			)
		],
		guild_ids = guild_ids
	)
	async def show(ctx, library = "server", word = None): # TODO: Separate libraries from collections (server x's custom library is a library, the default library is a library, 'everything' and 'connected' are collecitons of libraries).
		columns = ["word"] + dataModule.wordTypes

		# Selects query and arguments.
		target = "customLibrary WHERE server = @0"
		args = []
		send = "Showing "
		if not word is None: # Checks if a specific word is requested.
			send += "word "
			if word.isdigit():
				send += word + " "
			else:
				send += "\"" + word + "\" "
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
			target = "defaultLibrary"
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
			target = f"(SELECT word{columnString} FROM {target} UNION ALL SELECT word{columnString} FROM defaultLibrary)"
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
		query += " FROM " + target
		if not word is None and not word.isdigit(): # Changes query if a word is reqested.
			if library.isdigit() or library.lower() == "server":
				query += " AND"
			else:
				query += " WHERE"
			query += " word = @" + str(len(args))
			args.append(word)
		query += " ORDER BY word"
		if not word is None and word.isdigit(): # Changes query if a word number is reqested.
			query += " LIMIT 1 OFFSET (@" + str(len(args)) + " - 1)"
			args.append(int(word))
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
				if word is None:
					send += "There are no words in this library."
				else:
					send += "The word you're looking for could not be found."
				send += "```"
			await ctx.send(send)

	@slash.subcommand(
		base = "words",
		name = "add",
		description = "Add a new word to this server's custom word library, and I'll start using it.",
		options = [
			create_option(
				name = "word",
				description = "This is the base of the word. Use the other parameters to specify how the word should be used.",
				option_type = 3,
				required = True
			)] + wordParameters,
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

	"""@slash.subcommand(
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
			)] + wordParameters,
		guild_ids = guild_ids
	)
	async def update(ctx, target, **kwargs):
		await ctx.send("Not implemented.")"""

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
		query = "FROM customLibrary WHERE "
		if target.isdigit():
			query += "word IN (SELECT word FROM customLibrary WHERE "
		query += "(server = @0"
		if target.isdigit():
			query += ") ORDER BY word LIMIT 1 OFFSET @1 - 1);"
		else:
			query += " AND word = @1);"
		
		cursor = dataModule.connection.cursor()
		cursor.execute("SELECT row_number() OVER (ORDER BY word), word, count(*) " + query, [ctx.guild.id, target])
		check = cursor.fetchone()
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
			cursor.execute("DELETE " + query, [ctx.guild.id, target])
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