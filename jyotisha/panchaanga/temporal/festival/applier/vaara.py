import sys

from jyotisha.panchaanga.temporal import zodiac
from jyotisha.panchaanga.temporal.festival.applier import FestivalAssigner
from jyotisha.panchaanga.temporal.festival.applier import solar
from jyotisha.panchaanga.temporal.festival import FestivalInstance
from jyotisha.panchaanga.temporal.interval import Interval
from jyotisha.panchaanga.temporal.zodiac import NakshatraDivision, AngaType
from math import ceil
import logging
from sanskrit_data.schema import common


class VaraFestivalAssigner(FestivalAssigner):
  def assign_all(self):
    self.assign_bhriguvara_subrahmanya_vratam()
    self.assign_masa_vara_yoga_kaarttika()
    self.assign_masa_vara_yoga_fests_tn()
    self.assign_nakshatra_vara_yoga_vratam()
    self.assign_tithi_vara_yoga_mangala_angaaraka()
    self.assign_tithi_vara_yoga_kRSNAGgAraka()
    self.assign_vara_yoga_vratam()
    self.assign_tithi_vara_yoga_budhaaShTamii()


  def assign_bhriguvara_subrahmanya_vratam(self):
    festival_name = 'bhRguvAra-subrahmaNya-vratam'
    if festival_name not in self.rules_collection.name_to_rule:
      return 
    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      # BHRGUVARA SUBRAHMANYA VRATAM
      if self.daily_panchaangas[d].solar_sidereal_date_sunset.month == 7 and self.daily_panchaangas[d].date.get_weekday() == 5:
        if festival_name not in self.panchaanga.festival_id_to_days:
          # only the first bhRguvAra of tulA mAsa is considered (skAnda purANam)
          # https://youtu.be/rgXwyo0L3i8?t=222
          self.panchaanga.add_festival(fest_id=festival_name, date=self.daily_panchaangas[d].date)

  def assign_masa_vara_yoga_kaarttika(self):
    festival_name = 'kArttikA~sOmavAsaraH'
    if festival_name not in self.rules_collection.name_to_rule:
      return
    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):

      # KRTTIKA SOMAVASARA
      if self.daily_panchaangas[d].lunar_date.month.index == 8 and self.daily_panchaangas[d].date.get_weekday() == 1:
        self.panchaanga.add_festival(fest_id='kArttikA~sOmavAsaraH', date=self.daily_panchaangas[d].date)

  def assign_masa_vara_yoga_fests_tn(self):
    festival_name = 'AvaNi~JAyir2r2ukkizhamai'
    if festival_name not in self.rules_collection.name_to_rule:
      return
    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      # SOLAR MONTH-WEEKDAY FESTIVALS
      for (mwd_fest_m, mwd_fest_wd, mwd_fest_name) in ((5, 0, 'AvaNi~JAyir2r2ukkizhamai'),
                                                       (6, 6, 'puraTTAci~can2ikkizhamai'),
                                                       (8, 0, 'kArttigai~JAyir2r2ukkizhamai'),
                                                       (4, 5, 'ADi~veLLikkizhamai'),
                                                       (10, 5, 'tai~veLLikkizhamai'),
                                                       (11, 2, 'mAci~cevvAy')):
        if self.daily_panchaangas[d].solar_sidereal_date_sunset.month == mwd_fest_m and self.daily_panchaangas[d].date.get_weekday() == mwd_fest_wd:
          self.panchaanga.add_festival(fest_id=mwd_fest_name, date=self.daily_panchaangas[d].date)

  def assign_tithi_vara_yoga_mangala_angaaraka(self):
    if 'aGgArakI-caturthI' not in self.rules_collection.name_to_rule:
      return
    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      # MANGALA-CHATURTHI
      tithi_sunset = self.daily_panchaangas[d].sunrise_day_angas.get_anga_at_jd(jd=self.daily_panchaangas[d].jd_sunset, anga_type=AngaType.TITHI) % 15
      if self.daily_panchaangas[d].date.get_weekday() == 2 and (self.daily_panchaangas[d].sunrise_day_angas.tithi_at_sunrise.index % 15 == 4 or tithi_sunset == 4):
        festival_name = 'aGgArakI-caturthI'
        if self.daily_panchaangas[d].sunrise_day_angas.tithi_at_sunrise.index == 4 or tithi_sunset == 4:
          festival_name = 'sukhA' + '~' + festival_name
        self.panchaanga.add_festival(fest_id=festival_name, date=self.daily_panchaangas[d].date)

  def assign_tithi_vara_yoga_kRSNAGgAraka(self):
    if 'kRSNAGgAraka-caturdazI-puNyakAlaH_or_yamatarpaNam' not in self.rules_collection.name_to_rule:
      return
    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      # KRISHNA ANGARAKA CHATURDASHI
      if self.daily_panchaangas[d].date.get_weekday() == 2 and self.daily_panchaangas[d].sunrise_day_angas.tithi_at_sunrise.index == 29:
        # Double-check rule. When should the vyApti be?
        self.panchaanga.add_festival(fest_id='kRSNAGgAraka-caturdazI-puNyakAlaH or yamatarpaNam', date=self.daily_panchaangas[d].date)
        if self.daily_panchaangas[d].lunar_date.month.index == 1:
          self.panchaanga.add_festival(fest_id='pizAcamOcanam', date=self.daily_panchaangas[d].date)

  def assign_tithi_vara_yoga_budhaaShTamii(self):
    if 'budhASTamI' not in self.rules_collection.name_to_rule:
      return 
    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      # BUDHASHTAMI
      if self.daily_panchaangas[d].date.get_weekday() == 3 and self.daily_panchaangas[d].sunrise_day_angas.tithi_at_sunrise.index == 8:
        if self.daily_panchaangas[d].lunar_date.month.index == 10:
          # Pausha Shukla Ashtami + Budha vasara
          self.panchaanga.add_festival(fest_id='mahAbhadrA~budhASTamI', date=self.daily_panchaangas[d].date)
        elif ceil(self.daily_panchaangas[d].lunar_date.month.index) in [1, 5, 6, 7, 8]:
          # ceil above takes care of adhika maasas
          # 5, 6, 7, 8 takes care of श्रावणादिमासचतुष्टये
          # सायाह्नकाले चैत्रमासे श्रावणादिमासचतुष्टये कृष्णपक्षे च न ग्राह्या ॥
          pass
        else:
          self.panchaanga.add_festival(fest_id='budhASTamI', date=self.daily_panchaangas[d].date)


  def assign_nakshatra_vara_yoga_vratam(self):
    if 'Adityahasta-yOgaH' not in self.rules_collection.name_to_rule:
      return 

    AMRITA_SIDDHI_YOGAS = [(13, 0, 'Adityahasta-yOgaH'), (8, 0, 'ravipuSya-yOgaH'),
                 (22, 1, 'sOmazrAvaNI-yOgaH'), (5, 1, 'sOmamRgazIrSa-yOgaH'),
                 (1, 2, 'bhaumAzvinI-yOgaH'), 
                 (17, 3, 'budhAnurAdhA-yOgaH'), (8, 4, 'gurupuSya-yOgaH'),
                 (27, 5, 'bhRgurEvatI-yOgaH'), (4, 6, 'zanirOhiNI-yOgaH')]

    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      # NAKSHATRA-WEEKDAY FESTIVALS
      for (festival_nakshatra, festival_weekday, festival_name) in AMRITA_SIDDHI_YOGAS:
        if self.daily_panchaangas[d].date.get_weekday() == festival_weekday:
          nakshatram_praatah = self.daily_panchaangas[d].sunrise_day_angas.nakshatra_at_sunrise.index
          nakshatram_saayam = NakshatraDivision(jd=self.daily_panchaangas[d].jd_sunset, ayanaamsha_id=self.panchaanga.computation_system.ayanaamsha_id).get_anga(anga_type=AngaType.NAKSHATRA).index
          if festival_nakshatra in [nakshatram_praatah, nakshatram_saayam]:
            if festival_nakshatra == nakshatram_praatah == nakshatram_saayam:
              self.panchaanga.add_festival_instance(festival_instance=FestivalInstance(name=festival_name), date=self.daily_panchaangas[d].date)
            else:
              nakshatra_end_jd = self.daily_panchaangas[d].sunrise_day_angas.nakshatras_with_ends[0].jd_end

              if festival_nakshatra == nakshatram_praatah:
                interval = Interval(jd_start=None, jd_end=nakshatra_end_jd)
              elif festival_nakshatra == nakshatram_saayam:
                interval = Interval(jd_start=nakshatra_end_jd, jd_end=None)
              
              self.panchaanga.add_festival_instance(festival_instance=FestivalInstance(name=festival_name, interval=interval), date=self.daily_panchaangas[d].date)

  def assign_vara_yoga_vratam(self):
    if 'pAtArka-yOgaH' not in self.rules_collection.name_to_rule:
      return 
    PAATA_YOGA = 17 # vyatipAta
    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      if self.daily_panchaangas[d].date.get_weekday() == 0:
        d_yogas = self.daily_panchaangas[d].day_length_based_periods.dinamaana.get_boundary_angas(anga_type=AngaType.YOGA, ayanaamsha_id=self.ayanaamsha_id)
        if PAATA_YOGA in [d_yogas.start.index, d_yogas.end.index]:
          self.panchaanga.add_festival_instance(festival_instance=FestivalInstance(name='pAtArka-yOgaH'), date=self.daily_panchaangas[d].date)

# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
