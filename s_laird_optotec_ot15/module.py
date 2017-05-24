#!/usr/bin/python
# -*- coding: utf-8 -*-
from entropyfw import Module
from entropyfw.common import get_utc_ts

from .callbacks import UpdateV, UpdateI, UpdateVI, UpdateTemperaturesConstantQc
from .logger import log
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
        self.te = ThermoElectric()
        self.v_keyword = None
        self.i_keyword = None

    def pub_status(self):
        self.pub_event('status', self.te.status)

    @staticmethod
    def list_device_names():
        return GEOMETRY_FACTORS.keys()

    def select_device(self, dev_name):
        if getattr(TEDevices, dev_name, None) is None:
            raise Exception("Device {0} not a valid".format(dev_name))
        self.te.device = getattr(TEDevices, dev_name)

    def get_status(self):
        return self.te.status

    def calculate(self, heat_c):
        """Return values of Voltage and Current to input at TE to have 'heat_c' pumped from cold side"""
        d = self.te.calc_V_I(heat_c)
        return {'voltage': d[0],
                'current': d[1]}

    def register_event_v_applied(self, pattern, v_keyword, flags=0):
        if self.v_keyword is None:
            self.v_keyword = v_keyword
            self.register_callback(callback=UpdateV, pattern=pattern, flags=flags)
        else:
            raise Exception('Only one event for V values can be registered')

    def register_event_i_applied(self, pattern, i_keyword, flags=0):
        if self.i_keyword is None:
            self.i_keyword = i_keyword
            self.register_callback(callback=UpdateI, pattern=pattern, flags=flags)
        else:
            raise Exception('Only one event for I values can be registered')

    def register_event_iv_applied(self, pattern, v_keyword, i_keyword, flags=0):
        if self.i_keyword is None and self.v_keyword is None:
            self.i_keyword = i_keyword
            self.v_keyword = v_keyword
            self.register_callback(callback=UpdateVI, pattern=pattern, flags=flags)
        else:
            raise Exception('Only one event for I values can be registered')

    def update_values(self, tc=None, th=None, v=None, i=None):
        if tc:
            self.te.tc = tc
        if th:
            self.te.th = th
        if v:
            self.te.V = v
        if i:
            self.te.I = i
        self.pub_status()


class EntropyLairdOT15ConstantQc(EntropyLairdOT15):
    name = 'lairdot15'
    description = "Entropy module to keep a TE OT15 constantly pumping heat"

    def __init__(self, name=None, qc=1):
        EntropyLairdOT15.__init__(self, name)
        self.tc_keyword = None
        self.th_keyword = None
        self.target_qc = qc

    def register_temp_event(self, event_name, tc_keyword, th_keyword, flags=0):
        if self.tc_keyword is None and self.th_keyword is None:
            self.tc_keyword = tc_keyword
            self.th_keyword = th_keyword
            self.register_callback(callback=UpdateTemperaturesConstantQc, pattern=event_name, flags=flags)
        else:
            raise Exception('Only one event for tc, th values can be registered')


class TEDevices(object):
    ot08xx05 = "ot08xx05"
    ot12xx06 = "ot12xx06"
    ot15xx05 = "ot15xx05"
    ot20xx04 = "ot20xx04"

GEOMETRY_FACTORS = {TEDevices.ot08xx05: 0.016,
                    TEDevices.ot12xx06: 0.024,
                    TEDevices.ot15xx05: 0.030,
                    TEDevices.ot20xx04: 0.040
                    }


class ThermoElectric(object):

    def __init__(self, N=30, device=TEDevices.ot15xx05):
        self.N = N
        self.I = 0  # real applied current
        self.V = 0  # real applied voltage
        self.calculated_Qc = 0
        self.calculated_I_roots = (0, 0)  # There is a second grade eq to find I, both solutions
        self.calculated_V = 0
        self.calculated_I = 0  # selected solution of the two roots

        self._last_tc = 295
        self._last_th = 295
        self._tavg = 295
        self._t_delta = 0
        self._last_tc_update = get_utc_ts()
        self._last_th_update = get_utc_ts()
        self.device = device
        self._geom_factors = GEOMETRY_FACTORS

    def _get_geom(self):
        return self._geom_factors[self.device]
    G = property(_get_geom)

    def _set_th(self, value):
        self._last_th = value
        self._tavg = (self._last_tc + self._last_th)/2
        self._t_delta = self._last_th - self._last_tc
        self._last_th_update = get_utc_ts()

    def _get_th(self):
        return self._last_th
    th = property(_get_th, _set_th)

    def _set_tc(self, value):
        self._last_tc = value
        self._tavg = (self._last_tc + self._last_th) / 2
        self._t_delta = self._last_th - self._last_tc
        self._last_tc_update = get_utc_ts()

    def _get_tc(self):
        return self._last_tc
    tc = property(_get_tc, _set_tc)

    def _get_t_avg(self):
        return self._tavg
    t_avg = property(_get_t_avg)

    def _get_t_delta(self):
        return self._t_delta
    t_delta = property(_get_t_delta)

    def _get_rho(self):
        """Values have been calculated using values on Laird Technologies document
        and made a fit
        Temperatures: [273, 300, 325, 350, 375, 400, 425, 450, 475]
        rho: [9.20E-04, 1.01E-03, 1.15E-03, 1.28E-03, 1.37E-03, 1.48E-03,
                1.58E-03, 1.68E-03, 1.76E-03]
        rho = a*T + b *T² + c*T³ + d

        a = -3.49762867e-06
        b = 2.46967391e-08
        c = -2.50719921e-11
        d = 5.35273806e-04

        """

        a = -3.49762867e-06
        b = 2.46967391e-08
        c = -2.50719921e-11
        d = 5.35273806e-04

        return a*self._tavg + b*self._tavg**2 + c*self._tavg**3 + d
    rho = property(_get_rho)

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

        return a * self._tavg + b * self._tavg ** 2 + c * self._tavg ** 3 + d
    kappa = property(_get_kappa)

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

        return a * self._tavg + b * self._tavg ** 2 + c * self._tavg ** 3 + d
    zetta = property(_get_zetta)

    def _get_alpha(self):
        return (self.rho * self.kappa * self.zetta)**0.5
    alpha = property(_get_alpha)

    def _get_heatc(self):
        """Heat pumped at the cold side"""
        return 2*self.N*(self.alpha*self.I*self.tc - ((self.rho*self.I**2)/(2*self.G)) - self.kappa*self.t_delta*self.G)
    Qc = property(_get_heatc)

    def _calc_I(self, qc):
        """Return value of I to get an specific heat pumped at the cold side"""
        a = self.rho/(2*self.G)
        b = -self.alpha*self.tc
        c = self.kappa*self.t_delta*self.G + qc/(2*self.N)

        Ip = (-b + (b ** 2 - 4 * a * c) ** 0.5) / (2 * a)
        In = (-b - (b ** 2 - 4 * a * c) ** 0.5) / (2 * a)

        self.calculated_I_roots = (Ip, In)
        self.calculated_Qc = qc

        return (Ip, In)

    def calc_V_I(self, qc):
        """Return value of V to get an specific heat pumped at the cold side"""

        Ip, In = self._calc_I(qc)
        # log.debug('Calculated current values: {}, {} for status: {}'.format(Ip, In, self.status))
        if Ip > 0 and In > 0:
            I = min(Ip, In)
        elif Ip > 0:
            I = Ip
        elif In > 0:
            I = In
        else:
            raise Exception("Current should be positive. Calculated current values (Ip, In): {0}".format((Ip, In)))

        self.calculated_V = 2*self.N*(((I*self.rho)/self.G) + self.alpha*self.t_delta)
        self.calculated_I = I

        return self.calculated_V, I

    def _get_I_max(self):
        return (self.kappa*self.G/self.alpha)*((1+2*self.zetta*self.th)**0.5-1)
    Imax = property(_get_I_max)

    def _get_I_opt(self):
        return (self.kappa*self.G*self.t_delta*(1+(1+self.zetta*self.t_avg)**0.5))/(self.alpha*self.t_avg)
    Iopt = property(_get_I_opt)

    def _get_status(self):
        return {'N': self.N,
                'I_applied': self.I,
                'V_applied': self.V,
                'Imax': self.Imax,
                'I_optimum': self.Iopt,
                'calc_desired_qc': self.calculated_Qc,
                # 'calc_I_roots': self.calculated_I_roots,
                'calc_I': self.calculated_I,
                'calc_V': self.calculated_V,
                't_hot': self.th,
                't_cold': self.tc,
                't_avg': self.t_avg,
                't_delta': self.t_delta,
                'device': self.device,
                'geometry': self.G,
                'resistivity' : self.rho,
                'seebeck' : self.alpha,
                'thermal_cond': self.kappa,
                'figure_of_merit': self.zetta,
                'heat_pumped_at_cold_side': self.Qc,
                'heat_dissipated': self.I*self.V+self.Qc
                }
    status = property(_get_status)
