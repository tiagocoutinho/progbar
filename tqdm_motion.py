# -*- coding: utf-8 -*-

"""Experimental progbar for axis motions using tqdm"""

import sys
import time
import contextlib

import tqdm

from axis import Axis


import termios
class NoEcho(object):

    def __init__(self, stream=None):
        self.__stream = stream or sys.stdin

    def __enter__(self):
        fd = self.__stream.fileno()
        mode = termios.tcgetattr(fd)
        self.__orig_mode = mode[:]
        mode[3] &= ~termios.ECHO   # 3 == lflags
        termios.tcsetattr(fd, termios.TCSAFLUSH, mode)

    def __exit__(self, etype, evalue, etb):
        fd = self.__stream.fileno()
        termios.tcsetattr(fd, termios.TCSAFLUSH, self.__orig_mode)


class HandleCtrlC(object):

    def __init__(self, handler):
        self.__handler = handler
        self.ctrlc_hit = False

    def __enter__(self):
        return self

    def __exit__(self, etype, evalue, etb):
        if etype is KeyboardInterrupt:
            self.ctrlc_hit = True
            self.__handler()
            return True


class MotionBar(tqdm.tqdm):
    """A motion progress bar for an axis"""

    # disable threads
    monitor_interval = 0

    def __init__(self, axis, pos, label=None, **kwargs):
        label = axis.name if label is None else label
        ipos, tpos = axis.position, pos
        unit = axis.config.get('unit')
        unit = unit if unit else ''
        delta_pos = abs(tpos - ipos)
        self.__axis = axis
        self.__initial_position = ipos
        self.__target_position = tpos
        self.__total_displacement = delta_pos
        self.__unit = unit
        self.__finished = False
        self.__desc_format = u'{label}={{pos_fmt}}'.format(label=label)
        l_bar = u'{desc}|'
        r_bar = u'|{{percentage:=3.0f}}% \u0394p={{n:.02f}}/{{total:.02f}}{unit} \u0394t={{elapsed}} ETA:{{remaining}}, v:{{rate_fmt}}'.format(unit=unit)
        bar_format = u'{l_bar}{{bar}}{r_bar}'.format(l_bar=l_bar, r_bar=r_bar)
        kwargs.setdefault('miniters', 0)
        kwargs['bar_format'] = bar_format
        kwargs['total'] = delta_pos
        super(MotionBar, self).__init__(**kwargs)

    @property
    def axis(self):
        return self.__axis

    def axis_update(self, new_position=None, description=None):
        if self.__finished:
            return
        if new_position is None:
            new_position = self.__axis.position
        state = self.__axis.state
        if description is None:
            pos_fmt = self.position_format(new_position)
            description = self.__desc_format.format(pos_fmt=pos_fmt)
        self.set_description(description)
        displacement = abs(new_position - self.__initial_position)
        self.update(displacement - self.n)
        if state != Axis.MOVING:
            self.__finished = True

    def run(self):
        while self.__axis.state == Axis.MOVING:
            self.axis_update()

    def position_format(self, pos = None):
        if pos is None:
            pos = self.__axis.position
        return u'{0:.3f}{1}'.format(pos, self.__unit)


def motionmanager(*pbars, **kwargs):
    ctrlc_handler = kwargs.get('ctrlc_handler')
    if ctrlc_handler is None:
        def ctrlc_handler():
            for pbar in pbars:
                pbar.axis.stop()
    handler = HandleCtrlC(ctrlc_handler)
    managers = list(pbars) + [handler]
    return contextlib.nested(*managers)


def move_simple(axis, position):
    with MotionBar(axis, position) as pb:
        axis.start_move(position)
        try:
            pb.run()
        except KeyboardInterrupt:
            axis.stop()
            pb.write('motion aborted')


def move(*args, **kwargs):
    """
    Keyword args:
      file: specifies where to output the progress messages
            (default: None, meaning sys.stderr).

    """
    fobj = kwargs.setdefault('file', sys.stderr)
    axes, positions = args[::2], args[1::2]
    axis_positions = zip(axes, positions)

    pbars = [MotionBar(m, p, position=i)
             for i, (m, p) in enumerate(axis_positions)]

    try:
        with motionmanager(*pbars) as motion_manager:
            for axis, position, _ in axis_positions_labels:
                axis.start_move(position)
            motion = True
            while motion:
                motion = False
                for axis, pbar in zip(axes, pbars):
                    pbar.axis_update()
                    if axis.state == axis.MOVING:
                        motion = True
                time.sleep(0.05)
    finally:
        nb_lines = len(axes) - 1
        if nb_lines > 0:
            fobj.write(nb_lines*'\n')

    if motion_manager[-1].ctrlc_hit:
        print 'Motion aborted!'
    else:
        print 'Everything was fine!'


def demo0():
    theta = Axis('th', unit=u'deg')
    theta.position = 5.
    theta.speed = 10.

    move(theta, 50)


def demo1():
    theta = Axis('th', unit=u'deg')
    theta2 = Axis('tth', unit=u'deg')
    theta.position = 5.
    theta.speed = 10.
    theta2.position = 24
    theta2.speed = 5

    move(theta2, 30, theta, 40)


def demo2():
    theta = Axis('th', unit=u'deg')
    theta2 = Axis('tth', unit=u'deg')
    chi = Axis('chi', unit='deg')
    phi = Axis('phi', unit='deg')
    mu = Axis('mu', unit='deg')
    gam = Axis('gam', unit='deg')
    theta.position = 10.
    theta.speed = 9.
    theta2.position = 10.
    theta2.speed = 8.
    chi.position = 10.
    chi.speed = 7.
    phi.position = 10.
    phi.speed = 6.
    mu.position = 10.
    mu.speed = 5.
    gam.position = 10.
    gam.speed = 4.
    move(theta, 90.5, theta2, 45.5, chi, 55.2, phi, 35.5, mu, 27.9, gam, 12.40)


if __name__ == "__main__":
    with NoEcho():
        demo1()
