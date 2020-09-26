
import logging
import sys

from jyotisha.panchaanga.temporal import time
from jyotisha.panchaanga import temporal
from jyotisha.panchaanga.temporal import PanchaangaApplier, interval
from sanskrit_data.schema import common


def get_tithi(jd):
  """Returns the tithi prevailing at a given moment

  Tithi is computed as the difference in the longitudes of the moon
  and sun at any given point of time. Therefore, even the ayanaamsha
  does not matter, as it gets cancelled out.

  Returns:
    int tithi, where 1 stands for ShuklapakshaPrathama, ..., 15 stands
    for Paurnamasi, ..., 23 stands for KrishnapakshaAshtami, 30 stands
    for Amavasya

  """
  from jyotisha.panchaanga.temporal.zodiac import NakshatraDivision, Ayanamsha, AngaType
  # VERNAL_EQUINOX_AT_0 does not involve lookups, hence sending it - though ayanAmsha does not matter.
  return NakshatraDivision(julday=jd, ayanaamsha_id=Ayanamsha.VERNAL_EQUINOX_AT_0).get_anga(AngaType.TITHI)


class TithiAssigner(PanchaangaApplier):
  def assign_shraaddha_tithi(self, debug_shraaddha_tithi=False):
    tithi_days = [{z: [] for z in range(0, 32)} for _x in range(13)]
    lunar_tithi_days = {}
    def _assign(self, fday, tithi):
      if self.panchaanga.daily_panchaangas[fday].shraaddha_tithi == [None] or self.panchaanga.daily_panchaangas[fday].shraaddha_tithi == [tithi]:
        self.panchaanga.daily_panchaangas[fday].shraaddha_tithi = [tithi]
      else:
        self.panchaanga.daily_panchaangas[fday].shraaddha_tithi.append(tithi)
        if self.panchaanga.daily_panchaangas[fday - 1].shraaddha_tithi.count(tithi) == 1:
          self.panchaanga.daily_panchaangas[fday - 1].shraaddha_tithi.remove(tithi)
  
    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = time.jd_to_utc_gregorian(self.panchaanga.jd_start + d - 1).to_date_fractional_hour_tuple()
  
      angas = self.panchaanga.get_angas_for_interval_boundaries(d, get_tithi, 'aparaahna')
      angam_start = angas[0]
      next_anga = (angam_start % 30) + 1
      nnext_anga = (next_anga % 30) + 1
  
      # Calc vyaaptis
      t_start_d, t_end_d = interval.get_interval(self.panchaanga.daily_panchaangas[d].jd_sunrise, self.panchaanga.daily_panchaangas[d].jd_sunset, 3, 5).to_tuple()
      span_1 = t_end_d - t_start_d
      span_2 = 0
      for [tithi, tithi_end] in self.panchaanga.daily_panchaangas[d].tithi_data:
        if tithi_end is None:
          pass
        elif t_start_d < tithi_end < t_end_d:
          span_1 = tithi_end - t_start_d
          span_2 = t_end_d - tithi_end
  
      t_start_d1, t_end_d1 = interval.get_interval(self.panchaanga.daily_panchaangas[d + 1].jd_sunrise, self.panchaanga.daily_panchaangas[d + 1].jd_sunset, 3, 5).to_tuple()
      vyapti_3 = t_end_d1 - t_start_d1
      for [tithi, tithi_end] in self.panchaanga.daily_panchaangas[d + 1].tithi_data:
        if tithi_end is None:
          pass
        elif t_start_d1 < tithi_end < t_end_d1:
          vyapti_3 = tithi_end - t_start_d1
  
      # Combinations
      # <a> 1 1 1 1 - d + 1: 1
      # <b> 1 1 2 2 - d: 1
      # <f> 1 1 2 3 - d: 1, d+1: 2
      # <e> 1 1 1 2 - d, or vyApti (just in case next day aparahna is slightly longer): 1
      # <d> 1 1 3 3 - d: 1, 2
      # <h> 1 2 3 3 - d: 2
      # <c> 1 2 2 2 - d + 1: 2
      # <g> 1 2 2 3 - vyApti: 2
      fday = -1
      reason = '?'
      # if angas[1] == angam_start:
      #     logging.debug('Pre-emptively assign %2d to %3d, can be removed tomorrow if need be.' % (angam_start, d))
      #     _assign(self, d, angam_start)
      if angas[3] == angam_start:  # <a>
        # Full aparaahnas on both days, so second day
        fday = d + 1
        s_tithi = angam_start
        reason = '%2d incident on consecutive days; paraviddhA' % s_tithi
      elif (angas[1] == angam_start) and (angas[2] == next_anga):  # <b>/<f>
        fday = d
        s_tithi = angas[0]
        reason = '%2d not incident on %3d' % (s_tithi, d + 1)
        if angas[3] == nnext_anga:  # <f>
          if debug_shraaddha_tithi:
            logging.debug('%03d [%4d-%02d-%02d]: %s' % (d, y, m, dt,
                                                        'Need to assign %2d to %3d as it is present only at start of aparAhna tomorrow!)' % (
                                                          next_anga, d + 1)))
          _assign(self, d + 1, next_anga)
      elif angas[2] == angam_start:  # <e>
        if span_1 > vyapti_3:
          # Most likely
          fday = d
          s_tithi = angas[2]
          reason = '%2d has more vyApti on day %3d (%f ghatikAs; full?) compared to day %3d (%f ghatikAs)' % (
            s_tithi, d, span_1 * 60, d + 1, vyapti_3 * 60)
        else:
          fday = d + 1
          s_tithi = angas[2]
          reason = '%2d has more vyApti on day %3d (%f ghatikAs) compared to day %3d (%f ghatikAs) --- unusual!' % (
            s_tithi, d + 1, vyapti_3 * 60, d, span_1 * 60)
      elif angas[2] == nnext_anga:  # <d>/<h>
        if angas[1] == next_anga:  # <h>
          fday = d
          s_tithi = angas[1]
          reason = '%2d has some vyApti on day %3d; not incident on day %3d at all' % (s_tithi, d, d + 1)
        else:  # <d>
          s_tithi = angam_start
          fday = d
          reason = '%2d is incident fully at aparAhna today (%3d), and not incident tomorrow (%3d)!' % (
            s_tithi, d, d + 1)
          # Need to check vyApti of next_anga in sAyaMkAla: if it's nearly entire sAyaMkAla ie 5-59-30 or more!
          if debug_shraaddha_tithi:
            logging.debug('%03d [%4d-%02d-%02d]: %s' % (d, y, m, dt,
                                                        '%2d not incident at aparAhna on either day (%3d/%3d); picking second day %3d!' % (
                                                          next_anga, d, d + 1, d + 1)))
          _assign(self, d + 1, next_anga)
          # logging.debug(reason)
      elif angas[1] == angas[2] == angas[3] == next_anga:  # <c>
        s_tithi = next_anga
        fday = d + 1
        reason = '%2d has more vyApti on %3d (full) compared to %3d (part)' % (s_tithi, d + 1, d)
      elif angas[1] == angas[2] == next_anga:  # <g>
        s_tithi = angas[2]
        if span_2 > vyapti_3:
          # Most likely
          fday = d
          reason = '%2d has more vyApti on day %3d (%f ghatikAs) compared to day %3d (%f ghatikAs)' % (
            s_tithi, d, span_2 * 60, d + 1, vyapti_3 * 60)
        else:
          fday = d + 1
          reason = '%2d has more vyApti on day %3d (%f ghatikAs) compared to day %3d (%f ghatikAs)' % (
            s_tithi, d + 1, vyapti_3 * 60, d, span_2 * 60)  # Examine for greater vyApti
      else:
        logging.error('Should not reach here ever! %s' % str(angas))
        reason = '?'
      if debug_shraaddha_tithi:
        logging.debug(
          '%03d [%4d-%02d-%02d]: Assigning tithi %2d to %3d (%s).' % (d, y, m, dt, s_tithi, fday, reason))
      _assign(self, fday, s_tithi)
  
    if debug_shraaddha_tithi:
      logging.debug(self.panchaanga.shraaddha_tithi)
  
    
    for z in set([x.lunar_month for x in self.panchaanga.daily_panchaangas]):
      lunar_tithi_days[z] = {}
    for d in range(1, self.panchaanga.duration + 1):
      for t in self.panchaanga.daily_panchaangas[d].shraaddha_tithi:
        lunar_tithi_days[self.panchaanga.daily_panchaangas[d].lunar_month][t] = d
  
    # Following this primary assignment, we must now "clean" for Sankranti, and repetitions
    # If there are two tithis, take second. However, if the second has sankrAnti dushtam, take
    # first. If both have sankrAnti dushtam, take second.
    for d in range(1, self.panchaanga.duration + 1):
      if self.panchaanga.daily_panchaangas[d].shraaddha_tithi != [None]:
        if self.panchaanga.daily_panchaangas[d].solar_sidereal_date_sunset.month_transition is not None:
          if debug_shraaddha_tithi:
            logging.debug((d, self.panchaanga.daily_panchaangas[d].solar_sidereal_date_sunset.month_transition))
          aparaahna_start, aparaahna_end = interval.get_interval(self.panchaanga.daily_panchaangas[d].jd_sunrise, self.panchaanga.daily_panchaangas[d].jd_sunset, 3, 5).to_tuple()
          m1 = self.panchaanga.daily_panchaangas[d - 1].solar_sidereal_date_sunset.month  # Previous month
          m2 = self.panchaanga.daily_panchaangas[d].solar_sidereal_date_sunset.month  # Current month
          if aparaahna_start < self.panchaanga.daily_panchaangas[d].solar_sidereal_date_sunset.month_transition < aparaahna_end:
            if debug_shraaddha_tithi:
              logging.debug('Sankranti in aparaahna! Assigning to both months!')
            assert self.panchaanga.daily_panchaangas[d].solar_sidereal_date_sunset.day == 1
            for t in self.panchaanga.daily_panchaangas[d].shraaddha_tithi:
              # Assigning to both months --- should get eliminated because of a second occurrence
              tithi_days[m1][t].extend([d, '*'])
              tithi_days[m2][t].extend([d, '*'])
          if self.panchaanga.daily_panchaangas[d].solar_sidereal_date_sunset.month_transition < aparaahna_start:
            if debug_shraaddha_tithi:
              logging.debug('Sankranti before aparaahna!')
            assert self.panchaanga.daily_panchaangas[d].solar_sidereal_date_sunset.day == 1
            for t in self.panchaanga.daily_panchaangas[d].shraaddha_tithi:
              tithi_days[m2][t].extend([d, '*'])
          if aparaahna_end < self.panchaanga.daily_panchaangas[d].solar_sidereal_date_sunset.month_transition:
            if debug_shraaddha_tithi:
              logging.debug('Sankranti after aparaahna!')
            # Depending on whether sankranti is before or after sunset, m2 may or may not be equal to m1
            # In any case, we wish to assign this tithi to the previous month, where it really occurs.
            for t in self.panchaanga.daily_panchaangas[d].shraaddha_tithi:
              tithi_days[m1][t].extend([d, '*'])
        else:
          for t in self.panchaanga.daily_panchaangas[d].shraaddha_tithi:
            tithi_days[self.panchaanga.daily_panchaangas[d].solar_sidereal_date_sunset.month][t].append(d)
  
    # We have now assigned all tithis. Now, remove duplicates based on the above-mentioned rules.
    # TODO: This is not the best way to clean. Need to examine one month at a time.
    for m in range(1, 13):
      for t in range(1, 31):
        if len(tithi_days[m][t]) == 1:
          continue
        elif len(tithi_days[m][t]) == 2:
          if tithi_days[m][t][1] == '*':
            # Only one tithi available!
            if debug_shraaddha_tithi:
              logging.debug('Only one %2d tithi in month %2d, on day %3d, despite sankrAnti dushtam!' % (
                t, m, tithi_days[m][t][0]))
            del tithi_days[m][t][1]
            tithi_days[m][t][0] = '%d::%d' % (tithi_days[m][t][0], m)
            if debug_shraaddha_tithi:
              logging.debug('Note %s' % str(tithi_days[m][t]))
          else:
            self.panchaanga.daily_panchaangas[tithi_days[m][t][0]].shraaddha_tithi = [0]  # Shunya
            if debug_shraaddha_tithi:
              logging.debug('Removed %d' % tithi_days[m][t][0])
            del tithi_days[m][t][0]
            if debug_shraaddha_tithi:
              logging.debug('Two %2d tithis in month %2d: retaining second on %2d!' % (
                t, m, tithi_days[m][t][0]))
        elif len(tithi_days[m][t]) == 3:
          if debug_shraaddha_tithi:
            logging.debug('Two %2d tithis in month %2d: %s' % (t, m, str(tithi_days[m][t])))
          if tithi_days[m][t][1] == '*':
            self.panchaanga.daily_panchaangas[tithi_days[m][t][0]].shraaddha_tithi = [0]  # Shunya
            if debug_shraaddha_tithi:
              logging.debug('Removed %d' % tithi_days[m][t][0])
            del tithi_days[m][t][:2]
          elif tithi_days[m][t][2] == '*':
            self.panchaanga.daily_panchaangas[tithi_days[m][t][1]].shraaddha_tithi = [0]  # Shunya
            if debug_shraaddha_tithi:
              logging.debug('Removed %d' % tithi_days[m][t][1])
            del tithi_days[m][t][1:]
            if debug_shraaddha_tithi:
              logging.debug('     Retaining non-dushta: %s' % (str(tithi_days[m][t])))
        elif len(tithi_days[m][t]) == 4:
          if debug_shraaddha_tithi:
            logging.debug('Two dushta %2d tithis in month %2d: %s' % (t, m, str(tithi_days[m][t])))
          self.panchaanga.daily_panchaangas[tithi_days[m][t][0]].shraaddha_tithi = [0]  # Shunya
          if debug_shraaddha_tithi:
            logging.debug('Removed %d' % tithi_days[m][t][0])
          tithi_days[m][t][3] = str(m)
          del tithi_days[m][t][:2]
          if debug_shraaddha_tithi:
            logging.debug('                    Retaining: %s' % (str(tithi_days[m][t])))
          tithi_days[m][t][0] = '%d::%d' % (tithi_days[m][t][0], m)
          if debug_shraaddha_tithi:
            logging.debug('Note %s' % str(tithi_days[m][t]))
        elif len(tithi_days[m][t]) == 0:
          logging.warning(
            'Rare issue. No tithi %d in this solar month (%d). Therefore use lunar tithi.' % (t, m))
          # सौरमासे तिथ्यलाभे चान्द्रमानेन कारयेत्
          # tithi_days[m][t] = lunar_tithi_days[m][t]
        else:
          logging.error('Something weird. len(tithi_days[m][t]) is not in 1:4!! : %s (m=%d, t=%d)',
                        str(tithi_days[m][t]), m, t)
  
      if debug_shraaddha_tithi:
        logging.debug(tithi_days)


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
