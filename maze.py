import requests
import json
import time



class Vertex:
    def __init__(self, x, y):
        self.incidents = {}
        self.pos = (x, y)
        self.fixed = False



# maze api
baseUrl = 'https://api.noopschallenge.com'

# make http request en return only maze map
def getMaze(size = 200):
    url = baseUrl + '/mazebot/random?minSize={0}&maxSize={0}'.format(size)
    print(url)
    result = requests.get(url)
    return result.json()


def isVertex(maze, x, y):
    '''
    returns true if position is a candidate for a vertex
        * the starting point
        * the end point
        * points which have paths more than two directions
        * corners

    '''
    if (maze[y][x] == 'A') or (maze[y][x] == 'B'):
        return True
    upBlocked = (y == 0) or (maze[y - 1][x] == 'X')
    downBlocked = (y == len(maze) - 1) or (maze[y + 1][x] == 'X')
    leftBlocked = (x == 0) or (maze[y][x - 1] == 'X')
    rightBlocked = (x == len(maze[y]) - 1) or (maze[y][x + 1] == 'X')

    return ((upBlocked != downBlocked) or (leftBlocked != rightBlocked) or
        not(rightBlocked or leftBlocked or upBlocked or downBlocked))

#called =  [0]
#def findPath(fromVertex, endVertex, preceedingVertices):
#    called[0] = called[0] + 1
#
#    if called[0] % 1000000 == 0:
#        print('called {0} times'.format(called))
#
#    newPreceedingVertices = list(preceedingVertices)
#    newPreceedingVertices.append(fromVertex)
#
#    if endVertex in fromVertex.incidents:
#        return fromVertex.incidents[endVertex]
#
#    for k, v in fromVertex.incidents.items():
#        if k in preceedingVertices:
#            continue
#
#        followingPath = findPath(k, endVertex, newPreceedingVertices)
#
#        if followingPath:
#            return v + followingPath
#
#    return None


def findPathDijkstra(graph, fromVertex, toVertex):
    # initialize dijkstra
    q = list(graph.values())
    distances = { v: 99999 for v in q }
    preceeding = { v: None for v in q }
    preceedingPath = { v: '' for v in q }
    distances[toVertex] = 0

    q.sort(key = lambda v: distances[v])

    while q[0] != fromVertex:
        v = q[0]
        d = distances[v]
        for incident, path in v.incidents.items():
            # use reversed Path because where searching from end to start
            reversedPath = incident.incidents[v]
            if distances[incident] > d + len(path):
                distances[incident] = d + len(path)
                preceeding[incident] = v
                preceedingPath[incident] = reversedPath

        q.remove(v)
        q.sort(key = lambda v: distances[v])


    joinedPath = ''
    nextVertex = fromVertex
    while nextVertex != None:
        joinedPath = joinedPath + preceedingPath[nextVertex]
        nextVertex = preceeding[nextVertex]

    print(len(joinedPath))

    return joinedPath


def solveMaze(maze):
    createGraph = time.time()
    vertices = dict()

    # start and end point
    start = None
    end = None

    for y, mazeRow in enumerate(maze):
        for x, element in enumerate(mazeRow):
            # dont do anything for walls
            if element == 'X':
                continue

            # check if it makes sense to place a vertex
            if not(isVertex(maze, x, y)):
                continue

            # create vertex and add to dict
            v = Vertex(x, y)
            vertices[(x, y)] = v

            # remember starting and end point
            # set the fixed flag so they dont get deleted while optimizing
            # graph
            if element == 'A':
                start = v
                v.fixed = True
            elif element == 'B':
                end = v
                v.fixed = True
                # mark vertex in map
                # maze[y][x] = 'O'

            # preceding incidents to the left
            for tx in range(x - 1, -1, -1):
                if maze[y][tx] == 'X':
                    break

                tv = vertices.get((tx, y))
                if tv:
                    v.incidents[tv] = 'W' * (x - tx)
                    tv.incidents[v] = 'E' * (x - tx)
                    break

            # preceding incidents upwards
            for ty in range(y - 1, -1, -1):
                if maze[ty][x] == 'X':
                    break

                tv = vertices.get((x, ty))
                if tv:
                    v.incidents[tv] = 'N' * (y - ty)
                    tv.incidents[v] = 'S' * (y - ty)
                    break


    # optimize graph
    # * if a vertex has only two incidents these two vertices can be connected
    # instead (if the vertex is not the start or endpoint, obviously)
    # reapeat as long as the graph gets smaller
    count = 0
    while count != len(vertices):
        count = len(vertices)
        print('trying to optimize vertices: {0}'.format(count) )

        for v in vertices.values():
            if v.fixed:
                # dont remove start/end
                continue
            elif len(v.incidents) == 1:
                v1, d1 = v.incidents.popitem()
                v1.incidents.pop(v)

            elif len(v.incidents) == 2:
                v1, d1 = v.incidents.popitem()
                v2, d2 = v.incidents.popitem()


                # sometimes the two adjacent vertices are already connected
                # choose shorter path if possible
                if v2 in v1.incidents.keys() and len(v1.incidents[v2]) <= len(d1 + d2):
                    #print('old path is shorter')
                    pass

                else:
                    # print('new path is shorter')
                    v1.incidents[v2] = v1.incidents[v] + d2
                    v2.incidents[v1] = v2.incidents[v] + d1

                #print('v1',v1)
                #print(v1.incidents)
                #print('v2',v2)
                #print(v2.incidents)

                v1.incidents.pop(v)
                v2.incidents.pop(v)

        # keep only vertices that have incidents left
        vertices = {k: v for k, v in vertices.items() if len(v.incidents) > 0}


    print('created graph in {0}ms'.format((time.time() - createGraph) * 1000))
    # print maze an highlight vertices
    for y, mazeRow in enumerate(maze):
        for x, mazeCol in enumerate(mazeRow):
            if (x, y) in vertices and not(vertices[x, y].fixed):
                maze[y][x] = 'O'
            elif maze[y][x] == ' ':
                maze[y][x] = '='
        # print(''.join(mazeRow))


    # list vertices and incidents)
    #for k, v in vertices.items():
    #    print("vertex {0} has {1} incidents".format(v.pos, len(v.incidents)))
    #    for ki, vi in v.incidents.items():
    #        print("\t{0}: {1}".format(ki.pos, vi))

    dijkstraTime = time.time()
    path = findPathDijkstra(vertices, start, end)
    print('found path {0}ms'.format((time.time() - dijkstraTime) * 1000))

    print(path)

    return path


def checkSolution(maze, path):
    result = requests.post(baseUrl + maze['mazePath'], json.dumps({'directions': path}))
    for k, v in result.json().items():
        print('{0}: {1}'.format(k, v))



import matplotlib.pyplot as plt
import numpy as np

def plotMaze(maze, path, ax = plt):

    grid = [[1 if e == 'X' else 0 for e in x] for x in maze['map']]

    pos = maze['startingPosition']
    grid[pos[1]][pos[0]] = 2

    for d in path:
        if d == 'N':
            pos[1] = pos[1] - 1
        if d == 'S':
            pos[1] = pos[1] + 1
        if d == 'W':
            pos[0] = pos[0] - 1
        if d == 'E':
            pos[0] = pos[0] + 1

        grid[pos[1]][pos[0]] = 2



    ax.imshow(grid)
    if ax == plt:
        ax.show()


def run():
    maze = getMaze(200)

    path = solveMaze(maze['map'])
    plotMaze(maze, path)

    checkSolution(maze, path)

def getRaceMaze(mazePath):
    url = baseUrl + mazePath
    print(url)
    result = requests.get(url)
    return result.json()

def checkRaceMaze(maze, path):

    result = requests.post(baseUrl + maze['mazePath'], json.dumps({'directions': path}))
    j = result.json()
    for k, v in j.items():
        print('{0}: {1}'.format(k, v))
    nextMaze = j.get('nextMaze')
    if nextMaze:
        return nextMaze
    else:
        certResult = requests.get(baseUrl + j.get('certificate'))
        print('-----')
        for k, v in certResult.json().items():
            print('{0}: {1}'.format(k, v))
        print('-----')

def race():
    # put login here to
    login = None
    raceUrl = baseUrl + '/mazebot/race/start'
    payload = {'login': login}
    print(raceUrl, payload)
    result = requests.post(raceUrl, json.dumps(payload))

    j = result.json()
    for k, v in j.items():
        print('{0}: {1}'.format(k, v))

    nextMaze = j.get('nextMaze')
    f, ax = plt.subplots(3, 4)
    i = 0
    while nextMaze:
        maze = getRaceMaze(nextMaze)
        path = solveMaze(maze['map'])
        plotMaze(maze, path, ax.flatten()[i])
        i = i + 1
        nextMaze = checkRaceMaze(maze, path)

    plt.show()


run()
# race()
