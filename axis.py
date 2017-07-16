# -*- coding: utf-8 -*-

"""Axis object for experimenting with progbar"""

import time
import collections


Motion = collections.namedtuple('Motion', 'ipos fpos start_time end_time')


NAN = float('nan')


READY, MOVING = 'Ready', 'Moving'


class Axis(object):
    """A motor axis"""

    READY = READY
    MOVING = MOVING

    def __init__(self, name, unit='mm', position=0.0, speed=10.0):
        self.name = name
        self.__pos = NAN
        self.__speed = NAN
        self.__motion = None
        self.position = position
        self.speed = speed
        self.config = dict(unit=unit)

    def start_move(self, pos, start_time=None):
        """Start a new motion"""
        pos = float(pos)
        if self.state == self.MOVING:
            raise RuntimeError('cannot start another motion while moving')
        start_time = time.time() if start_time is None else start_time
        delta_pos = pos - self.__pos
        delta_time = delta_pos / self.speed
        end_time = start_time + delta_time
        self.__motion = Motion(self.__pos, pos, start_time, end_time)

    def stop(self):
        """Stop current motion (if any)"""
        self.__pos = self.__update()
        self.__motion = None

    def __update(self):
        if self.__motion is None:
            return self.__pos
        curr_time = time.time()
        ipos, fpos, start_time, end_time = self.__motion
        if curr_time >= end_time:
            self.__pos = fpos
            self.__motion = None
        else:
            self.__pos = ipos + self.speed * (curr_time - start_time)
        return self.__pos

    @property
    def speed(self):
        """Current motor speed"""
        return self.__speed

    @speed.setter
    def speed(self, new_speed):
        """Set new motor speed"""
        self.__speed = float(new_speed)

    @property
    def state(self):
        """Current motor state"""
        self.__update()
        return MOVING if self.__motion else READY

    @property
    def position(self):
        """Current motor position"""
        return self.__update()

    @position.setter
    def position(self, new_pos):
        """Sets current motor position"""
        if self.state == self.MOVING:
            raise RuntimeError('cannot set position while moving')
        self.__pos = float(new_pos)

    @property
    def motion(self):
        """Current motion in progress (if any)"""
        return self.__motion
