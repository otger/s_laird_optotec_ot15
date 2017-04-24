#!/usr/bin/python
# -*- coding: utf-8 -*-
from entropyfw import Callback, logger

"""
callbacks
Created by otger on 23/03/17.
All rights reserved.
"""


class UpdateV(Callback):
    name = 'updatev'
    description = "update applied v to thermoelectric"
    version = "0.1"

    def functionality(self):
        v = getattr(self.event.value, self.module.v_keyword, None)
        if v is None:
            logger.log.warning("UpdateV Callback event has no valid V value")
            return
        self.module.update_values(v=v)


class UpdateI(Callback):
    name = 'updatei'
    description = "update applied current to thermoelectric"
    version = "0.1"

    def functionality(self):
        i = getattr(self.event.value, self.module.i_keyword, None)
        if i is None:
            logger.log.warning("Updatei Callback event has no valid I value")
            return
        self.module.update_values(i=i)


class UpdateVI(Callback):
    name = 'updatevi'
    description = "update applied current and voltage to thermoelectric"
    version = "0.1"

    def functionality(self):
        i = self.event.value.get(self.module.i_keyword, None)
        v = self.event.value.get(self.module.v_keyword, None)
        if i is None or v is None:
            logger.log.warning("Updatevi Callback event has no valid I or V value. \
                                \nEvent value: {}".format(self.event.value))
            return
        if i < 0:
            i = 0
        if v < 0:
            v = 0
        self.module.update_values(i=i, v=v)


class UpdateTemperaturesConstantQc(Callback):
    name = 'updatetemperatures'
    description = "update temperatures of thermoelectric and publishes new values to apply"
    version = "0.1"

    def __init__(self, event, manager, module):
        Callback.__init__(self, event, manager, module)

    def functionality(self):
        tc = self.event.value.get(self.module.tc_keyword)
        th = self.event.value.get(self.module.th_keyword)
        self.module.update_values(tc=tc, th=th)
        d = self.module.calculate(self.module.target_qc)
        self.module.pub_event('constant_qc_vi', d)
