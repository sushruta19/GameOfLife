import copy
import time
import os

def clear():
  os.system("cls")

class Grid:
  def __init__(self, width, height, initial_state):
    self.width = width
    self.height = height
    self.grid_board = [[0]*width for _ in range(height)]
    for i, j in initial_state:
      self.grid_board[i][j] = 1

  def generation_step(self):
    r, c = self.height, self.width
    dir = [[-1, -1], [-1, 0], [-1, 1], [0, -1], [0, 1], [1, 1], [1, 0], [1, -1]]
    temp_grid = copy.deepcopy(self.grid_board)
    for i in range(r):
      for j in range(c):
        sum_alive = 0
        for k, l in dir:
          i_neigh = i+k
          j_neigh = j+l
          if 0 <= i_neigh < r and 0 <= j_neigh < c:
            sum_alive = sum_alive + self.grid_board[i_neigh][j_neigh]
        #Conway's Rules
        #Underpopulation
        if sum_alive < 2 and self.grid_board[i][j] == 1:
          temp_grid[i][j] = 0
        #Overpopulation
        if sum_alive > 3 and self.grid_board[i][j] == 1:
          temp_grid[i][j] = 0
        #reproduction
        if sum_alive == 3 and self.grid_board[i][j] == 0:
          temp_grid[i][j] = 1
    self.grid_board = copy.deepcopy(temp_grid)

  def run(self):
    for _ in range(100):
      clear()
      self.display()
      time.sleep(1)
      self.generation_step()
    self.display()
  
  def display(self):
    for i in range(self.height):
      for j in range(self.width):
        print(self.grid_board[i][j], end = " ")
      print()

if __name__ == "__main__":
  population = int(input())
  init_state = []
  for _ in range(population):
    init_state.append(list(map(int, input().split())))

  G = Grid(20, 20, init_state)
  G.run()
             