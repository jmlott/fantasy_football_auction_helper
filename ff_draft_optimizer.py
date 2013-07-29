#!/usr/bin/python
##########################################
# A tool to choose the optimal team to draft given a set of auction prices
# and projected point values.
##########################################


import csv
import itertools
import multiprocessing


# Total Salary Cap = 200
# Save $20 for backups
SALARY_CAP = 175  # Cap minus bench, k, def (can be adjusted)
FLEX_RB = ('qb', 'rb', 'rb', 'rb', 'te', 'wr', 'wr')
FLEX_WR = ('qb', 'rb', 'rb', 'te', 'wr', 'wr', 'wr')
CSV_FILE = '/home/jmlott/Downloads/FFL Draft Sheet - Sheet11.csv'
PRICES = []
QB_PRICES = {}
POINTS = {}
POSITIONS = {}
TEAMS = []
TOP_TEAMS = [(0, 0), (0, 0), (0, 0), (0, 0), (0, 0),
             (0, 0), (0, 0), (0, 0), (0, 0), (0, 0)]


def GetPlayersInPriceAndPosition(qb, top_teams):
  these_prices = PRICES
  these_prices.insert(0, QB_PRICES[qb])
  team_combos = itertools.combinations(these_prices, 7)
  for a, b, c, d, e, f, g in team_combos:
    price = a[1] + b[1] + c[1] + d[1] + e[1] + f[1] + g[1]
    names = (a[0], b[0], c[0], d[0], e[0], f[0], g[0])
    if (price <= SALARY_CAP and
        price > (SALARY_CAP - 10)):
      positions = []
      for player in names:
        positions.append(POSITIONS[player])
      if (tuple(sorted(positions)) == FLEX_RB or
          tuple(sorted(positions)) == FLEX_WR):
        top_teams = SortByPoints(top_teams, names, price)
  return top_teams


def SortByPoints(top_teams, names, price):
  points = GetPointsForTeam(names, price)
  top_teams = sorted(top_teams, key=lambda t: t[1], reverse=True)
  if points[1] > top_teams[9][1]:
    top_teams[9] = points
  return top_teams


def GetPointsForTeam(names, price):
  # (fred, james, matt, etc)
  choice_points = []
  for name in names:
    choice_points.append(POINTS[name])
  points = (names, sum(choice_points), price)
  return points


def PrintOptimalTeams():
  sorted_points = sorted(TEAMS, key=lambda t: t[1], reverse=True)
  if sorted_points:
    print 'Top Ten Teams To Draft'
    print '-----------------------'
    for i in range(9):
      print sorted_points[i]


def CollectResults(results):
  TEAMS.extend(results)


def ImportCSV():
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
  manager = multiprocessing.Manager()
  top_teams = manager.list(TOP_TEAMS)
  ImportCSV()
  pool = multiprocessing.Pool(processes=4, maxtasksperchild=1)
  potential_teams = []
  for qb in QB_PRICES.keys():
    pool.apply_async(GetPlayersInPriceAndPosition, args=(qb, top_teams), callback=CollectResults)
  pool.close()
  pool.join()
  PrintOptimalTeams()


if __name__ == "__main__":
  main()
