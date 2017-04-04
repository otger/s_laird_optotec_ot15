#!/usr/bin/python
# -*- coding: utf-8 -*-
from entropyfw import Module
from entropyfw.common import get_utc_ts

# from .actions import StartTempLoop, EnableChannel, StopTempLoop
# from .web.api.resources import get_api_resources
# from .web.blueprints import get_blueprint
"""
module
Created by otger on 04/04/17.
All rights reserved.
"""


class EntropyLairdOT15(Module):
    name = 'lairdot15'
    description = "Thermoelectric operating values calculator"

    def __init__(self, name=None):
        Module.__init__(self, name=name)


class TEDevices(object):
    ot08xx05="ot08xx05"
    ot12xx06 = "ot12xx06"
    ot15xx05 = "ot15xx05"
    ot20xx04 = "ot20xx04"

GEOMETRY_FACTORS = {TEDevices.ot08xx05: 0.016,
                    TEDevices.ot12xx06: 0.024,
                    TEDevices.ot15xx05: 0.030,
                    TEDevices.ot20xx04: 0.040
                    }

class ThermoElectric(object):

    def __init__(self):
        self._last_tc = 295
        self._last_th = 295
        self._last_tc_update = get_utc_ts()
        self._last_th_update = get_utc_ts()
        self.device = TEDevices.ot15xx05
        self._geom_factors = GEOMETRY_FACTORS
        self._cached = {'tavg': None,
                        'rho': None,
                        'kappa': None,
                        'zetta': None,
                        'alpha': None}

    def _get_geom(self):
        return self._geom_factors[self.device]
    G = property(_get_geom)

    def _set_th(self, value):
        self._cached = {'tavg': None,
                        'rho': None,
                        'kappa': None,
                        'zetta': None,
                        'alpha': None}
        self._last_th = value
        self._last_th_update = get_utc_ts()

    def _get_th(self):
        return self._last_th
    th = property(_get_th, _set_th)

    def _set_tc(self, value):
        self._cached = {'tavg': None,
                        'rho': None,
                        'kappa': None,
                        'zetta': None,
                        'alpha': None}
        self._last_tc = value
        self._last_tc_update = get_utc_ts()

    def _get_tc(self):
        return self._last_tc
    tc = property(_get_tc, _set_tc)

    def _get_t_avg(self):
        if self._cached['tavg'] is None:
            self._cached['tavg'] = (self._last_tc + self._last_th)/2
        return self._cached['tavg']
    t_avg = property(_get_t_avg)

    def _get_rho(self):
        """Values have been calculated using values on Laird Technologies document
        and made a fit
        Temperatures: [273, 300, 325, 350, 375, 400, 425, 450, 475]
        rho: [9.20E-04, 1.01E-03, 1.15E-03, 1.28E-03, 1.37E-03, 1.48E-03,
                1.58E-03, 1.68E-03, 1.76E-03]
        rho = a*T + b *T*T + c*T*T*T + d

        a = -3.49762867e-06
        b = 2.46967391e-08
        c = -2.50719921e-11
        d = 5.35273806e-04

        """
        a = -3.49762867e-06
        b = 2.46967391e-08
        c = -2.50719921e-11
        d = 5.35273806e-04

        return a*

    def _get_kappa(self):
        """Values have been calculated using values on Laird Technologies document
        and made a fit
        Temperatures: [273, 300, 325, 350, 375, 400, 425, 450, 475]
        kappa: [ 0.0161,  0.0151,  0.0153,  0.0155,  0.0158,  0.0163,  0.0173,
                0.0188,  0.0209]
        kappa = a*T + b *T*T + c*T*T*T + d

        a = 6.06270280e-06
        b = -2.30792066e-07
        c = 4.43869633e-10
        d = 2.24397747e-02

        """
        a = 6.06270280e-06
        b = -2.30792066e-07
        c = 4.43869633e-10
        d = 2.24397747e-02

        return a*

    def _get_zetta(self):
        """Values have been calculated using values on Laird Technologies document
        and made a fit
        Temperatures: [273, 300, 325, 350, 375, 400, 425, 450, 475]
        zetta: [0.00254,  0.00268,  0.00244,  0.00222,  0.00185,  0.00159,
                0.00132,  0.00108,  0.00087]
        zetta = a*T + b *T*T + c*T*T*T + d

        a = 1.82845995e-04
        b = -5.04512226e-07
        c = 4.33203649e-10
        d = -1.85492384e-02

        """
        a = 1.82845995e-04
        b = -5.04512226e-07
        c = 4.33203649e-10
        d = -1.85492384e-02

        return a*