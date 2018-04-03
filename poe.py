#!/usr/bin/env python3

import time

import requests

rs = requests.Session()

league = None

def price(cmd):
	global league

	if league is None:
		league = _get_league_name()

	names, lines = _search(league, cmd.args)
	if len(names) == 0:
		cmd.reply("couldn't find " + cmd.args)
	elif len(names) > 1:
		cmd.reply(', '.join(names))
	else:
		for line in lines:
			name = line['name']
			if line['links'] > 0:
				name += ' (%d link)' % line['links']
			response = '%s: %.1f chaos' % (name, line['chaosValue'])
			if line['exaltedValue'] > 1.0:
				response += ', %.1f exalted' % line['exaltedValue']
			cmd.reply(response)

def _get_league_name():
	html = rs.get('https://cdn.poe.ninja/')
	for line in html.text.split('\n'):
		if '<script type="text/javascript" src="/dist/' in line:
			prefix = '<script type="text/javascript" src="'
			start = line.index(prefix) + len(prefix)
			path = line[start:]
			path = path[:path.find('"')]
			break

	url = 'https://cdn.poe.ninja' + path
	js = rs.get(url).text
	start = js.index('getLeagueName')
	league = js[start:start+256]
	league = league[league.index('tmpStandardLeagueId'):]
	league = league[league.index('"')+1:]
	league = league[:league.index('"')]
	return league

pages = [
	'GetUniqueArmourOverview',
	'GetUniqueWeaponOverview',
	'GetUniqueAccessoryOverview',
	'GetUniqueJewelOverview',
	'GetUniqueFlaskOverview',
	'GetUniqueMapOverview',
	'GetDivinationCardsOverview',
]

def _search(league, q):
	q = q.casefold()
	names = set()
	matches = []
	for page in pages:
		data = _query(page, league)
		lines = data['lines']
		for line in lines:
			if q in line['name'].casefold():
				names.add(line['name'])
				name = line['name']
				matches.append(line)
		if len(names) > 0:
			# there may be other matches on other pages, but we won't bother finding them
			break
	return names, matches

cache = {}

def _query(page, league):
	cached = cache.get((page, league))
	now = time.time()
	if cached is not None:
		ts, data = cached
		if ts > now - 60 * 60: # cache for 1 hour
			return data

	data = rs.get('https://cdn.poe.ninja/api/Data/%s?league=%s' % (page, league)).json()
	cache[(page, league)] = now, data
	return data