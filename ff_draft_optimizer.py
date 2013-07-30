#!/usr/bin/python
##########################################
# A tool to choose the optimal team to
# draft given a set of auction prices and
# projected point values.
##########################################

import csv
import itertools
import logging
import multiprocessing


# User Configurable Variables
# Based on total salary cap of $200
SALARY_CAP = 175  # Cap minus bench, k, def (can be adjusted)
CSV_FILE = '/home/jmlott/Downloads/FFL Draft Sheet - Sheet11.csv'
MUST_HAVES = ('Jamaal Charles')
# End User Configurable Variables


# DO NOT EDIT BELOW THIS LINE
#################################################################
PRICES = []
QB_PRICES = {}
POINTS = {}
POSITIONS = {}
TEAMS = []
FLEX_RB = ('qb', 'rb', 'rb', 'rb', 'te', 'wr', 'wr')
FLEX_WR = ('qb', 'rb', 'rb', 'te', 'wr', 'wr', 'wr')
TOP_TEAMS = [(0, 0), (0, 0), (0, 0), (0, 0), (0, 0),
             (0, 0), (0, 0), (0, 0), (0, 0), (0, 0)]


def CalculatePlayers(qb, top_teams):
  """Calculates the top 10 teams.

  This function is called once for each quarterback in the CSV file.
  It is run simultaneously on all available CPU cores until the list
  of quarterbacks is exhausted. Each cycle can take an extremely long
  time depending on the total number of players in the CSV. Adding
  players to the list has an exponential effect on the run time.

  Args:
    qb: str, quarterback to run calcs against.
    top_teams: list, template of a list of two-tuples.

  Returns:
    A list of ten 7-tuples for the top 10 teams.
  """
  these_prices = PRICES
  these_prices.insert(0, QB_PRICES[qb])
  if len(FLEX_RB) != len(FLEX_WR):
    logging.fatal('ERROR: Number of lineup positions do not match')
  team_combos = itertools.combinations(these_prices, len(FLEX_RB))
  for combo in team_combos:
    price = sum([x[1] for x in combo])
    names = [x[0] for x in combo]
    if price <= SALARY_CAP:
      positions = []
      for player in names:
        positions.append(POSITIONS[player])
      positions = tuple(sorted(positions))
      if (positions == FLEX_RB or positions == FLEX_WR):
        if set(MUST_HAVES).issubset(set(names)):
          top_teams = SortByPoints(top_teams, names, price)
  print top_teams
  return top_teams


def SortByPoints(top_teams, names, price):
  """Sort out top ten potential teams.

  Args:
    top_teams: list, template of a list of two-tuples.
    names: list, string names of each player on "team".
    price: int, total summed auction value of each player.

  Returns:
    A list of ten 7-tuples for the top 10 teams.
  """
  points = GetPointsForTeam(names, price)
  top_teams = sorted(top_teams, key=lambda t: t[1], reverse=True)
  if points[1] > top_teams[9][1]:
    top_teams[9] = points
  return top_teams


def GetPointsForTeam(names, price):
  """Calculates the total points for a team.

  Args:
    names: list, string names of each player on "team".
    price: int, total summed auction value of each player.

  Returns:
    A tuple containing the team, total points, and total price.
  """
  choice_points = []
  for name in names:
    choice_points.append(POINTS[name])
  points = (names, sum(choice_points), price)
  return points


def PrintOptimalTeams():
  """Displays final output."""
  sorted_points = sorted(TEAMS, key=lambda t: t[1], reverse=True)
  if sorted_points:
    print 'Top Ten Teams To Draft'
    print '-----------------------'
    for i in range(9):
      names = ', '.join(sorted_points[i][0])
      points = sorted_points[i][1]
      price = sorted_points[i][2]
      print '%s\t\t%dpts\t\t$%d' % (names, points, price)


def CollectResults(results):
  """Callback function that collects teams from workers.

  Args:
    results: list, top 10 teams from each worker.
  """
  TEAMS.extend(results)


def ImportCSV():
  """Reads the CSV file and sets global vars with the data."""
  with open(CSV_FILE, 'rb') as csvfile:
    fantasy_list = csv.reader(csvfile, delimiter=',', quotechar='|')
    for row in fantasy_list:
      POSITIONS.setdefault(row[0], row[1])
      POINTS.setdefault(row[0], int(row[3]))
      if POSITIONS[row[0]] == 'qb':
        QB_PRICES.setdefault(row[0], (row[0], int(row[2])))
      else:
        PRICES.append((row[0], int(row[2])))


def main():
  """Calculates the top 10 teams for an auction based FF draft."""
  manager = multiprocessing.Manager()
  top_teams = manager.list(TOP_TEAMS)
  ImportCSV()
  pool = multiprocessing.Pool(processes=multiprocessing.cpu_count(),
                              maxtasksperchild=1)
  potential_teams = []
  for qb in QB_PRICES.keys():
    pool.apply_async(CalculatePlayers, args=(qb, top_teams),
                     callback=CollectResults)
  pool.close()
  pool.join()
  PrintOptimalTeams()


if __name__ == "__main__":
  main()
