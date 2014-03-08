#!/usr/bin/env python

import curses
import math
import os
import sys
import time

class EndGame(Exception):
  pass

class Bird:
  def __init__(self, nlines, ncols):
    # Set up the bird
    self.x_coord = ncols / 2 - 5
    self.y_coord = nlines / 2
    self.bird = curses.newwin(3, 7, self.y_coord, self.x_coord)

    # Set up some state information and initial settings
    self.flap_up()
    self.was_flap_up = True
    self.fly_frame = 0  # Start as falling

    # Window Conditions
    self.bottom = nlines

  def flap_up(self):
    self.bird.clear()
    self.bird.addstr(0,0, "00 --")
    self.bird.addstr(1,0, "  0  o.")
    self.bird.addstr(2,0, "  \--/")

  def flap_down(self):
    self.bird.clear()
    self.bird.addstr(0,0, "   --")
    self.bird.addstr(1,0, "000  o.")
    self.bird.addstr(2,0, "  \--/")

  def toggle(self):
    if self.was_flap_up:
      self.flap_down()
    else:
      self.flap_up()

    self.was_flap_up = not self.was_flap_up

  def refresh(self):
    self.bird.refresh()

  def up(self):
    self.fly_frame = 5

  def animate(self):
    if self.fly_frame > 0:
      # We are flying
      if self.y_coord > 1: # Only move up if we aren't at top yet
        self.y_coord -= 1  
      self.fly_frame -= 1  # Reduce frame count
    else:
      self.y_coord += 1    # Fall

    self.bird.erase()
    self.bird.refresh()
    self.bird.mvwin(self.y_coord, self.x_coord)
    self.toggle()
    self.bird.refresh()

    if self.y_coord + 3 == self.bottom:
      raise EndGame()


class Pipe:
  def __init__(self, delay, nlines, ncols, is_bottom, height, x, y):
    """
      TODO: Use window.resize(nlines, ncols) to resize the window
            Use window.mvwin(y, x) to move window
    """
    self.x_coord = x
    self.y_coord = y

    self.pipe = curses.newwin(height, 9, self.y_coord, self.x_coord)
    self.is_bottom = is_bottom
    self.height = height  # The height of the pipe
    self.draw()

  def draw(self):
    self.pipe.clear()
    row = 0
    end = self.height
    if self.is_bottom:
      self.pipe.addstr(0,0, "+------+")
      self.pipe.addstr(1,0, "|      |")
      self.pipe.addstr(2,0, "++    ++")
      row = 3
    else:
      end = self.height - 3

    while row < end:
      self.pipe.addstr(row,0, " |    |")
      row += 1

    if not self.is_bottom:
      self.pipe.addstr(end,0,     "++    ++")
      self.pipe.addstr(end + 1,0, "|      |")
      self.pipe.addstr(end + 2,0, "+------+")

  def refresh(self):
    self.pipe.refresh()

class Flappy:
  def __init__(self):
    curses.initscr()   # Init screen
    curses.noecho()    # Don't echo prints
    curses.cbreak()    # Don't wit for enter for input
    curses.curs_set(0) # Don't show cursor

    # Set up the game window
    self.nlines = 40
    self.ncols = 50
    self.window = curses.newwin(self.nlines, self.ncols, 0, 0)

  def run(self):
    self.window.box()
    self.window.refresh()

    self.window.addstr(self.nlines / 2, self.ncols / 2 - 13, "Click n to start new game.")

    while True:
      key = self.window.getch()
      if key == ord('q'):   # Actually quit the game
        break
      elif key == ord('n'): # New game
        self.round()

    curses.endwin()

  def round(self):
    self.window.nodelay(1)
    self.window.erase()
    self.window.box()
    self.window.refresh()

    # Init bird
    bird = Bird(self.nlines, self.ncols)
    pipe = Pipe(0, 40, 50, True, 10, 2, 2)
    pipe2 = Pipe(0, 40, 50, False, 10, 10, 2)
    while True:
      bird.refresh()
      pipe.refresh()
      pipe2.refresh()
      key = self.window.getch()
      if key == ord('q'):
        break
      elif key == ord(' '):
        bird.up()

      # Refresh the loop at 0.2 seconds
      try:
        bird.animate()
      except EndGame:
        self.window.addstr(self.nlines / 2,self.ncols / 2 - 4, "You Lose")
        break
      # ERROR HANDLE

      time.sleep(0.2)

    self.window.nodelay(0)

# Run actual Flappy Game
flap = Flappy()
flap.run()