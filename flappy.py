#!/usr/bin/env python

import curses
import math
import os
import random
import sys
import time

PIPE_WIDTH = 8
BIRD_WIDTH = 7
BIRD_HEIGHT = 3
BIRD_FRAMES = 5

class EndGame(Exception):
  pass

class Bird:
  def __init__(self, win_nlines, win_ncols):
    # Set up the bird
    self.x_coord = win_ncols / 2 - (BIRD_WIDTH / 2)
    self.y_coord = win_nlines / 2
    self.bird = curses.newwin(BIRD_HEIGHT, BIRD_WIDTH, self.y_coord, self.x_coord)
    self.bird.scrollok(1)
    # Set up some state information and initial settings
    self.flap_up()
    self.was_flap_up = True
    self.fly_frame = 0  # Start as falling

    # Window Conditions
    self.bottom = win_nlines

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
    self.fly_frame = BIRD_FRAMES

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

    if self.y_coord + BIRD_HEIGHT == self.bottom:
      raise EndGame()


class Pipe:
  def __init__(self, is_bottom, height, countdown, win_nlines, win_ncols):
    """
      TODO: Use window.resize(nlines, ncols) to resize the window
            Use window.mvwin(y, x) to move window
    """
    self.x_orig = win_ncols - 8 - 1  # Written this way to remember win edge
    self.x_coord = self.x_orig
    if is_bottom:
      self.y_coord = win_nlines - height - 1 # Again win edge
    else:
      self.y_coord = 1 # Top

    self.pipe = curses.newwin(height, PIPE_WIDTH, self.y_coord, self.x_coord)
    self.pipe.scrollok(1)
    self.is_bottom = is_bottom
    self.height = height  # The height of the pipe

    self.delay = win_ncols
    self.countdown = countdown

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

  def animate(self):
    if self.countdown <= 0:
      self.x_coord -= 1

      self.pipe.erase()
      self.pipe.refresh()
      self.pipe.mvwin(self.y_coord, self.x_coord)
      self.draw()
      self.pipe.refresh()

      if self.x_coord == 1:
        self.pipe.erase()
        self.pipe.refresh()
        self.countdown = self.delay
    else:
      self.countdown -= 1

      if self.countdown == 0:
        self.x_coord = self.x_orig

class Pipes:
  def __init__(self, win_nlines, win_ncols):
    # Pipes will always be 8 in width (PIPE_WIDTH)
    self.win_nlines = win_nlines
    self.win_ncols = win_ncols

    # Calculate the number of pipes to use
    self.num_pipes = self.win_ncols / (int) (PIPE_WIDTH * 1.5)

    self.pipes = []

    init_delay = 0
    for i in range(0, self.num_pipes):
      top_height = random.randint(4, self.win_nlines - 10 - 4)
      bot_height = self.win_nlines - 10 - top_height
      self.pipes.append([Pipe(False, top_height, init_delay,
                              self.win_nlines, self.win_ncols),
                         Pipe(True, bot_height, init_delay,
                              self.win_nlines, self.win_ncols)])
      init_delay += PIPE_WIDTH * 3

  def animate(self):
    for pipe_set in self.pipes:
      pipe_set[0].animate()
      pipe_set[1].animate()

  def refresh(self):
    for pipe_set in self.pipes:
      pipe_set[0].refresh()
      pipe_set[1].refresh()

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
    pipes = Pipes(self.nlines, self.ncols)

    while True:
      bird.refresh()
      pipes.refresh()
      key = self.window.getch()
      if key == ord('q'):
        break
      elif key == ord(' '):
        bird.up()

      pipes.animate()

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