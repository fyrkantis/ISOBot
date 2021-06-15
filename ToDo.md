# To do
## Improvments
- [ ] Look for th, year and month written before and/or after numbers for more filtering.
- [x] Make message shorter.

## Bugs
- [x] Month length check is missing.
- [x] Only ask what the date is supposed to mean if there is any ambiguity.
- [x] If message contains several dates, only some of which aren't ISO-8601 compliant, correct ones are flagged.

## Design
- [ ] Recolor warning image.

## Support
- [ ] BC dates.
- [ ] Roman numerals.
- [ ] first, second, third.
- [ ] Direct Messages.
- [ ] Weeks and weekdays.
- [ ] Monthless dates.

## New Features
- [ ] Statistical analysis of dates.
- [ ] Mark dates (or formats) with emotes and encourage a vote of what the date is supposed to mean.
- [x] Clariy how to correctly format a non ISO-8601 compliant date and point out what's wrong when able to.

## Regex Improvments
- [ ] Don't enterpret dates between quotes.
- [ ] Space between +, * or = and number makes regex ignore negative lookbehind.
- [x] Don't enterpret th saved at beginning of the, this or that.
- [x] Don't enterpret math with + or = at beginning or end.

## SQLite Database Functions
- [ ] Add ability to, with a single number, change the general severity of swear words selected.
- [ ] Add separate tables for: server specific words, preferences, units and shared word servers.
- [ ] Request several word types at a time, to avoid duplicates of same word used diffrently.
- [x] RE-ORGANIZE WORDS, use venn diagram style system beyond the simple types.
- [x] Make sure there are always default tables.

## Word Organization
### Example Query
```sql
WITH t AS
	(SELECT word, degree, binder, adjective, random() as r FROM
		(SELECT * FROM defaultLibrary
		UNION ALL
		SELECT * FROM customLibrary)
	ORDER BY r)

SELECT * FROM
	(SELECT word, degree FROM t WHERE degree NOT NULL LIMIT 1) AS t1
JOIN
	(SELECT word, binder FROM t WHERE binder NOT NULL LIMIT 1) AS t2
JOIN
	(SELECT word, adjective FROM t WHERE adjective NOT NULL LIMIT 1) AS t3
ON t1.word != t2.word and t2.word != t3.word;
ON t1.word != t2.word and t2.word != t3.word;
```

### Example Sentences
You're an (state)? (binder)? (insult).

You're (degree)? (binder)? (adjective).

What's this (adjective)? (object).

What the (comment) is this (object).

### Adjective (TODO: Add "ily/ally" form)
- a Crap-py, Crap-pier, Crap-piest (5)
- a Dumb, Dumb-er, Dumb-est (4)
- a Shit-ty, Shit-tier, Shit-tiest (5)
- a Stupid, Stupid-er, Stupid-est (4)
- an Idiot-ic, more Idiot-ic, most Idiot-ic (1)
- a Mess-ed up, more Mess-ed up, most Mess-ed up (3)
- a Fuck-ed up, more Fuck-ed up, most Fuck-ed up (3)
- a Dreadfulentasvariasticdiabolitrocious, more -||-, most -||- (0)
- a Dick-ish, more Dick-ish, most Dick-ish (2)

### Binder
- Fuck-ing (1)
- Heck-ing (1)
- Damn (0)

### Comment
- Fuck (0)
- Heck (0)
- Damn (0)
- Shit (0)
- Crap (0)
- Hell (0)

### Degree
- a Very (0)
- an Extreme-ly (2)
- a Real-ly (1)
- a Complete-ly (1)
- an Impressive-ly (2)
- an Utter-ly (2)
- a Truly (0)

### Insult
- an Arse (0)
- a Fuck-er (2)
- an Idiot (0)
- a Moron (1)
- a piece of Shit (3)
- a piece of Crap (3)
- a Dick (1)

### Object
- Crap (0)
- Shit (0)
- Mess (0)

### State
- an Absolute (0)
- a Complete (1)
- an Utter (0)
- a Mess-ed up (2)
- a Real (1)