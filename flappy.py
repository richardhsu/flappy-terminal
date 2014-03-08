#!/usr/bin/env python

import curses
import math
import os
import random
import sys
import time

PIPE_MIN_HT = 4
PIPE_WIDTH = 8
BIRD_WIDTH = 7
BIRD_HEIGHT = 3
BIRD_FRAMES = 5
PIPE_OPEN = 10

class EndGame(Exception):
  """End Game Exception to notify when game ends."""
  pass

class Bird:
  def __init__(self, win_nlines, win_ncols):
    """Initialize the Bird object for positioning."""
    self.x_coord = win_ncols / 2 - (BIRD_WIDTH / 2)
    self.y_coord = win_nlines / 2
    self.bird = curses.newwin(BIRD_HEIGHT, BIRD_WIDTH,
                              self.y_coord, self.x_coord)
    self.bird.scrollok(1)

    # Set up some state information and initial settings
    self.flap_up()
    self.was_flap_up = True
    self.fly_frame = 0  # Start as falling

    # Window Conditions
    self.bottom = win_nlines

  def flap_up(self):
    """Draws the bird with flaps up."""
    self.bird.addstr(0,0, "00 --")
    self.bird.addstr(1,0, "  0  o.")
    self.bird.addstr(2,0, "  \--/")

  def flap_down(self):
    """Draws the bird with flaps down."""
    self.bird.addstr(0,0, "   --")
    self.bird.addstr(1,0, "000  o.")
    self.bird.addstr(2,0, "  \--/")

  def toggle(self):
    """Toggle from flapping up to flapping down."""
    if self.was_flap_up:
      self.flap_down()
    else:
      self.flap_up()

    self.was_flap_up = not self.was_flap_up

  def refresh(self):
    """Refresh the curses window."""
    self.bird.refresh()

  def up(self):
    """Initiate flying up."""
    self.fly_frame = BIRD_FRAMES

  def animate(self):
    """Animate the bird flying up.
    The fly_frame is increased when up() is called and decreases from
    there telling the bird to animate as if flying up.
    """
    if self.fly_frame > 0:
      if self.y_coord > 1: # Only move up if we aren't at top yet
        self.y_coord -= 1  
      self.fly_frame -= 1  # Reduce frame count
    else:
      self.y_coord += 1    # Fall to the ground

    self.bird.erase()
    self.bird.refresh()
    self.bird.mvwin(self.y_coord, self.x_coord)
    self.toggle()
    self.bird.refresh()

    # If we hit the bottom, we lose :(
    if self.y_coord + BIRD_HEIGHT == self.bottom:
      raise EndGame()

  def get_box(self):
    """Return the bounding box coordinates.
    Returns tuple of x coordinates and another tuple of y coordinates.
    """
    return ((self.x_coord, self.x_coord + BIRD_WIDTH - 1),
            (self.y_coord, self.y_coord + BIRD_HEIGHT - 1))

class Pipe:
  def __init__(self, is_bottom, height, countdown, win_nlines, win_ncols):
    """Initialize the Pipe object given initial state."""
    self.x_orig = win_ncols - 8 - 1  # Written this way to remember win edge
    self.x_coord = self.x_orig
    self.win_nlines = win_nlines
    self.height = height  # The height of the pipe
    self.is_bottom = is_bottom

    if self.is_bottom:
      self.y_coord = self.win_nlines - self.height - 1 # Again win edge
    else:
      self.y_coord = 1 # Top

    self.pipe = curses.newwin(self.height, PIPE_WIDTH,
                              self.y_coord, self.x_coord)
    self.pipe.scrollok(1)
    
    # Countdown and delay information
    self.delay = win_ncols + PIPE_WIDTH
    self.countdown = countdown

  def draw(self):
    """Draws the pipe whether it's a top or bottom pipe."""
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
    """Refresh the curses window."""
    self.pipe.refresh()

  def animate(self):
    """Animate the pipe moving to the left.
    Pipe will have a countdown phase which is before it should appear on the
    screen. Once countdown hits 0 we'll reset it to beginning of right side of
    the window.
    """
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

  def set_height(self, height):
    """Change the height of the pipe.
    This will erase the pipes, move it to 1,1 for delay until it is redrawn at
    new position.
    """
    self.pipe.erase()
    self.pipe.refresh()
    self.height = height
    if self.is_bottom:
      self.y_coord = self.win_nlines - self.height - 1 # Again win edge
    else:
      self.y_coord = 1 # Top
    self.pipe.mvwin(1, 1)
    self.pipe.refresh()
    self.pipe.resize(self.height, PIPE_WIDTH)

  def get_box(self):
    """Return the bounding box coordinates.
    Returns tuple of x coordinates and another tuple of y coordinates.
    Note: Curses seems to draw height of pipe off by one so subtract 2 rather
    than 1 for max y coordinate.
    """
    return ((self.x_coord, self.x_coord + PIPE_WIDTH - 1),
            (self.y_coord, self.y_coord + self.height - 2))

class Pipes:
  def __init__(self, win_nlines, win_ncols, bird):
    """Initialize the Pipes object which holds all pipes.
    Calculates how many pipes to use for a good continuous level generation.
    Initializes the pipes and coordinates delay.
    """
    self.win_nlines = win_nlines
    self.win_ncols = win_ncols
    self.bird = bird

    # Calculate the number of pipes to use
    self.num_pipes = self.win_ncols / (int) (PIPE_WIDTH * 1.5)

    self.pipes = []

    init_delay = 0
    for i in range(0, self.num_pipes):
      top_height = random.randint(PIPE_MIN_HT,
                                  self.win_nlines - PIPE_OPEN - PIPE_MIN_HT)
      bot_height = self.win_nlines - PIPE_OPEN - top_height
      self.pipes.append([Pipe(False, top_height, init_delay,
                              self.win_nlines, self.win_ncols),
                         Pipe(True, bot_height, init_delay,
                              self.win_nlines, self.win_ncols)])
      init_delay += PIPE_WIDTH * 3

  def animate(self):
    """Animate all the pipes.
    Also checks boundary conditions against the bird.
    Returns if a point was scored or not for passing pipe.
    """
    point = 0
    for top_pipe, bot_pipe in self.pipes:
      top_pipe.animate()
      bot_pipe.animate()

      if top_pipe.countdown == top_pipe.delay:
        # At edge so redraw and resize
        top_height = random.randint(PIPE_MIN_HT,
                                    self.win_nlines - PIPE_OPEN - PIPE_MIN_HT)
        bot_height = self.win_nlines - PIPE_OPEN - top_height
        top_pipe.set_height(top_height)
        bot_pipe.set_height(bot_height)
      else:
        # Check if pipes collided with bird
        bird_xs, bird_ys = self.bird.get_box()
        tpipe_xs, tpipe_ys = top_pipe.get_box()

        if (((bird_xs[0] <= tpipe_xs[1]) and (bird_xs[1] >= tpipe_xs[0])) or
            ((tpipe_xs[0] <= bird_xs[1]) and (tpipe_xs[1] >= bird_xs[0]))):
          # Within range so check if collided
          if (bird_ys[0] <= tpipe_ys[1] and bird_ys[1] >= tpipe_ys[0]):
            raise EndGame()
        elif (bird_xs[0] == tpipe_xs[1] + 1):
          # Just passed this pipe so add a point
          point = 1

        bpipe_xs, bpipe_ys = bot_pipe.get_box()
        if (((bird_xs[0] <= bpipe_xs[1]) and (bird_xs[1] >= bpipe_xs[0])) or
            ((bpipe_xs[0] <= bird_xs[1]) and (bpipe_xs[1] >= bird_xs[0]))):
          # Within range so check if collided
          if (bird_ys[0] <= bpipe_ys[1] and bird_ys[1] >= bpipe_ys[0]):
            raise EndGame()
    return point

  def refresh(self):
    """"Refresh the curses window by going through each pipe to refresh."""
    for pipe_set in self.pipes:
      pipe_set[0].refresh()
      pipe_set[1].refresh()

class Flappy:
  def __init__(self):
    """Initialize Flappy Game Object."""
    curses.initscr()   # Init screen
    curses.noecho()    # Don't echo prints
    curses.cbreak()    # Don't wit for enter for input
    curses.curs_set(0) # Don't show cursor

    # Set up the game window
    self.nlines = 40
    self.ncols = PIPE_WIDTH * 9
    self.window = curses.newwin(self.nlines, self.ncols, 0, 0)

  def run(self):
    """Run the Flappy Bird Game.
    This loop will also control entrance and exit of a round.
    """
    self.window.box()
    self.window.refresh()

    # Status box for beginning of game (disappears later)
    status = curses.newwin(4, 28, self.nlines / 2 - 4, self.ncols / 2 - 13)
    status.box()
    status.addstr(1,1, "Tap the space bar to fly.")
    status.addstr(2,1, "Hit n to start game.")
    status.refresh()

    while True:
      key = self.window.getch()
      if key == ord('q'):   # Actually quit the game
        break
      elif key == ord('n'): # New game
        status.erase()
        status.refresh()
        self.round()

    curses.endwin()

  def round(self):
    """Run a round of the game.
    This will show end game results and return to the run loop after.
    """
    self.window.nodelay(1)
    self.window.erase()
    self.window.box()
    self.window.refresh()

    # Init bird and pipes
    bird = Bird(self.nlines, self.ncols)
    pipes = Pipes(self.nlines, self.ncols, bird)

    score = 0
    paused = False
    while True:
      self.window.refresh()
      bird.refresh()
      pipes.refresh()
      key = self.window.getch()

      # Handle controls
      if not paused:
        if key == ord('q'):
          break
        elif key == ord(' '):
          bird.up()
        elif key == ord('p'):
          self.window.addstr(1,1, "Press p to resume.")
          self.window.refresh()
          self.window.nodelay(0)
          paused = True
          continue
      else:
        if key == ord('p'):
          self.window.nodelay(1)
          paused = False
        if key == ord('q'):
          break
        continue

      # Animate and check end conditions
      try:
        bird.animate()
        score += pipes.animate()
        self.window.addstr(1,1, "Press p to pause. ")
        self.window.addstr(2,1, "Score: {0}".format(score))
      except EndGame:
        break

      time.sleep(0.2)

    gameover = curses.newwin(8, 26, self.nlines / 2 - 4, self.ncols / 2 - 13)
    gameover.box()
    gameover.addstr(1,1, "You Lose")
    gameover.addstr(2,1, "Score: {0}".format(score))
    gameover.addstr(5,1, "Hit q to quit.")
    gameover.addstr(6,1, "Hit n to try again.")
    gameover.refresh()

    self.window.nodelay(0)

"""
FLAPPY BIRD TERMINAL EDITION
RUN THE GAME
"""
flap = Flappy()
flap.run()