import sys

from jyotisha.panchaanga.temporal import zodiac, tithi, time
from jyotisha.panchaanga.temporal.zodiac import NakshatraDivision, AngaSpanFinder, Ayanamsha
from jyotisha.panchaanga.temporal.zodiac.angas import AngaType, Anga, Tithi
from sanskrit_data.schema import common
from sanskrit_data.schema.common import JsonObject


class LunarMonthAssigner(JsonObject):
  MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA = "MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA"
  MULTI_FULL_MOON_SIDEREAL_MONTH_ADHIKA = "MULTI_FULL_MOON_SIDEREAL_MONTH_ADHIKA"
  SOLSTICE_POST_DARK_10_ADHIKA = "SOLSTICE_POST_DARK_10_ADHIKA"
  
  def __init__(self, ayanaamsha_id):
    super().__init__()
    self.ayanaamsha_id = ayanaamsha_id

  def _get_month(self, daily_panchaanga):
    pass

  def set_date(self, daily_panchaanga, previous_day_panchaanga=None):
    pass

  @classmethod
  def get_assigner(cls, computation_system):
    if computation_system.lunar_month_assigner_type == LunarMonthAssigner.MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA:
      return MultiNewmoonSolarMonthAdhikaAssigner(ayanaamsha_id=computation_system.ayanaamsha_id)
    elif computation_system.lunar_month_assigner_type == LunarMonthAssigner.MULTI_FULL_MOON_SIDEREAL_MONTH_ADHIKA:
      return MultiFullmoonSolarMonthAdhikaAssigner(ayanaamsha_id=computation_system.ayanaamsha_id)
    elif computation_system.lunar_month_assigner_type == LunarMonthAssigner.SOLSTICE_POST_DARK_10_ADHIKA:
      return SolsticePostDark10AdhikaAssigner(ayanaamsha_id=computation_system.ayanaamsha_id)
    else:
      raise ValueError("Invalid assigner_id " + computation_system.lunar_month_assigner_type)


class MultiLunarPhaseSolarMonthAdhikaAssigner(LunarMonthAssigner):
  """Let us consider a lunar month defined as ending with a particular lunar tithi. This assigner marks a month as adhika iff that month does not have a solar sankrAnti."""

  def __init__(self, ayanaamsha_id, month_end_tithi):
    super(MultiLunarPhaseSolarMonthAdhikaAssigner, self).__init__(ayanaamsha_id=ayanaamsha_id)
    self.month_end_tithi = month_end_tithi

  """
  
  प्रचलितायाम् अर्वाचीनायां पद्धतौ अर्वाचीनस्य राशिविभाजने आधृतस्य सौरमासस्य सङ्क्रान्तिं स्वीकृत्य “असङ्क्रान्ति-मासो ऽधिमास” इति परिभाषया अधिकमासगणना क्रियते ।
  """
  def _get_month(self, daily_panchaanga):
    """ Assigns Lunar months to days in the period
    
    Implementation note: Works by looking at solar months and month-end tithis (which makes it easy to deduce adhika-mAsa-s.)
    
    :return: 
    """
    # tithi_at_sunrise gives a rough indication of the number of days since last new moon. We now find a more precise interval below.
    anga_finder = zodiac.AngaSpanFinder.get_cached(ayanaamsha_id=Ayanamsha.ASHVINI_STARTING_0, anga_type=zodiac.AngaType.TITHI)

    if self.month_end_tithi < daily_panchaanga.sunrise_day_angas.tithi_at_sunrise.index:
      approx_days_since_last_end_tithi =  daily_panchaanga.sunrise_day_angas.tithi_at_sunrise.index - self.month_end_tithi
    else:
      approx_days_since_last_end_tithi = daily_panchaanga.sunrise_day_angas.tithi_at_sunrise.index + (30 - self.month_end_tithi)

    last_lunar_phase = anga_finder.find(
      jd1=daily_panchaanga.jd_sunrise - approx_days_since_last_end_tithi - 3, jd2=daily_panchaanga.jd_sunrise - approx_days_since_last_end_tithi + 3, target_anga_id=self.month_end_tithi)
    this_new_moon = anga_finder.find(
      jd1=last_lunar_phase.jd_start + 24, jd2=last_lunar_phase.jd_start + 32,
      target_anga_id=self.month_end_tithi)
    last_new_moon_solar_raashi = NakshatraDivision(last_lunar_phase.jd_end, ayanaamsha_id=self.ayanaamsha_id).get_solar_raashi()
    this_new_moon_solar_raashi = NakshatraDivision(this_new_moon.jd_end, ayanaamsha_id=self.ayanaamsha_id).get_solar_raashi()
    is_adhika = last_new_moon_solar_raashi == this_new_moon_solar_raashi

    if is_adhika:
      return this_new_moon_solar_raashi + .5
    else:
      return this_new_moon_solar_raashi

  def set_date(self, daily_panchaanga, previous_day_panchaanga=None):
    if previous_day_panchaanga is not None:
      span = previous_day_panchaanga.sunrise_day_angas.find_anga_span(Anga.get_cached(anga_type_id=AngaType.TITHI.name, index=1))

      # If a prathamA tithi has started post-sunrise yesterday (and has potentially ended before today's sunrise), or if today we have a prathamA at sunrise
      if (span is not None and span.jd_start is not None) or previous_day_panchaanga.sunrise_day_angas.tithi_at_sunrise.index == 1:
        self.set_date(daily_panchaanga=daily_panchaanga, previous_day_panchaanga=None)
      else:
        daily_panchaanga.lunar_date = Tithi(month=previous_day_panchaanga.lunar_date.month, index=daily_panchaanga.sunrise_day_angas.tithi_at_sunrise.index)
    else:
      daily_panchaanga.lunar_date = Tithi(month=self._get_month(daily_panchaanga=daily_panchaanga), index=daily_panchaanga.sunrise_day_angas.tithi_at_sunrise.index)


class MultiNewmoonSolarMonthAdhikaAssigner(MultiLunarPhaseSolarMonthAdhikaAssigner):
  def __init__(self, ayanaamsha_id):
    super(MultiNewmoonSolarMonthAdhikaAssigner, self).__init__(ayanaamsha_id=ayanaamsha_id, month_end_tithi=30)


class MultiFullmoonSolarMonthAdhikaAssigner(MultiLunarPhaseSolarMonthAdhikaAssigner):
  def __init__(self, ayanaamsha_id):
    super(MultiFullmoonSolarMonthAdhikaAssigner, self).__init__(ayanaamsha_id=ayanaamsha_id, month_end_tithi=15)


class SolsticePostDark10AdhikaAssigner(LunarMonthAssigner):
  """
  
  द्व्यूनं द्वि-षष्टि-भागेन दिनं सौराच् च पार्वणम् । यत्-कृताव् उपजायेते मध्येऽन्ते चाऽधिमासकौ ।। इति वेदाङ्गज्योतिषे।
  केषुचिद् एव युगेषु, यथापेक्षम् अधिमासयोजनं स्यात्। किन्तु यदायदाऽधिकमासो योज्यते तदातदाऽयनान्ते एव शुचौ मासे (आषाढे) वा सहस्ये मासे (पौषे) वा द्वितीयशुचिमासरूपेण (द्वितीयाषाढरूपेण) वा द्वितीयसहस्यमासरूपेण (द्वितीयपौषरूपेण) वैवाऽधिकमासो योज्यते। वेदाङ्गज्योतिषानुरूपाया गणनाया प्रयोगः काष्ठमण्डपनगरे मल्लानां शासनकालपर्यन्तमासीदिति शिलालेखेभ्य एव ज्ञायते।

  एतादृशी व्यवस्था च - यदा दृक्-सिद्ध-सौरायनारम्भ-दिने (दक्षिणायनस्य वोत्तरायणस्य वापि) कृष्ण-पक्षस्य दशमी, ततः परा वा तिथिर् भवति तदैव तेन कृष्ण-पक्षेण युक्तोऽमावास्यान्तो मासोऽधिको मास इति स्वीक्रियते, -यदा तु दृक्-सिद्ध-सौरायनारम्भ-दिने कृष्ण-पक्षस्य नवमी वा ततः पूर्वा वा तिथिर् भवति तदा तु तेन कृष्ण-पक्षेण युक्तोऽमावास्यान्तो मासोऽधिको मास इति न स्वीक्रियते।

  Since the day's tithi varies by location,  
  adhika-mAsa decision too can potentially vary by location.  
  Instead, we use the actual (sphuTa) tithi  
  independent of location  
  for our adhika-mAsa computation here.  
  
  The day-number is exactly set to be 1 if tithi at noon is 1,  
  with the previous day's number set exactly to 30 (potentially skipping 29).
  This gels with the ancient tradition of marking parva-boundaries,  
  when the fall in pUrvAhNa,  
  by darsha-pUrNamAseShTi-s (or sthAlIpAka-s),  
  preceeded by a preparatory day.  
  (Ref. Apastamba shrauta sUtra - parishiShTa chapters with commentaries.)  
  This is also followed by the kauNDinyAyana-s.  
  On other days, it can just one greater than the previous day's number.

  So, this approximates the nepAli-kauNDinyAyana-family system.  
  Solstice vs tithi data for the latter: See https://vishvasa.github.io/jyotiSham/history/kauNDinyAyana/
  """

  @classmethod
  def _is_tithi_post_dark10(cls, jd):
    if tithi.get_tithi(jd=jd).index > 15 + 9:
      return True
    else:
      return False

  @classmethod
  def _month_from_previous_jd_month_provisional(cls, jd, prev_jd, prev_jd_month):
    """Deduce (provisional) month from a previous known day's month."""
    span_finder = AngaSpanFinder.get_cached(anga_type=AngaType.TITHI, ayanaamsha_id=Ayanamsha.ASHVINI_STARTING_0)
    tithi_1_jds = span_finder.get_spans_in_period(jd_start=prev_jd, jd_end=jd, target_anga_id=1)
    is_prev_month_adhika = str(prev_jd_month.index).endswith(".5")
    if is_prev_month_adhika:
      lunar_month = prev_jd_month + max(0, len(tithi_1_jds) - 0.5)
    else:
      lunar_month = prev_jd_month + len(tithi_1_jds)
    return lunar_month


  @classmethod
  def _get_previous_post_dark_10_tropical_solar_month_span(cls, jd):
    solstice_tropical_month_span = zodiac.get_previous_solstice_month_span(jd=jd)
    prev_solstice_tropical_month_span = zodiac.get_previous_solstice_month_span(jd=solstice_tropical_month_span.jd_start - 1)
    if cls._is_tithi_post_dark10(jd=solstice_tropical_month_span.jd_start):
      if cls._is_tithi_post_dark10(jd=prev_solstice_tropical_month_span.jd_start):
        return cls._get_previous_post_dark_10_tropical_solar_month_span(jd=prev_solstice_tropical_month_span.jd_start + 15)
      else:
        return solstice_tropical_month_span
    else:
      return cls._get_previous_post_dark_10_tropical_solar_month_span(jd=prev_solstice_tropical_month_span.jd_start + 15)

    

  def _get_month(self, jd):
    """ Assigns Lunar months to days in the period
        
    :return: 
    """
    next_tithi_30_span = AngaSpanFinder.get_cached(anga_type=AngaType.TITHI, ayanaamsha_id=Ayanamsha.ASHVINI_STARTING_0).get_spans_in_period(jd_start=jd, jd_end=jd + 35, target_anga_id=30)[0]


    tropical_solar_month_span = self._get_previous_post_dark_10_tropical_solar_month_span(jd = next_tithi_30_span.jd_end)
    if tropical_solar_month_span.jd_start >= jd:
      return tropical_solar_month_span.anga + 0.5
    else:
      return self._month_from_previous_jd_month_provisional(jd=jd, prev_jd=tropical_solar_month_span.jd_start, prev_jd_month=tropical_solar_month_span.anga + 0.5)

  def _get_day(self, daily_panchaanga, previous_day_panchaanga=None):
    anga_finder = zodiac.AngaSpanFinder.get_cached(ayanaamsha_id=Ayanamsha.ASHVINI_STARTING_0, anga_type=zodiac.AngaType.TITHI)
    noon_tithi = daily_panchaanga.sunrise_day_angas.tithi_at_noon.index
    jd_noon = daily_panchaanga.get_jd_noon()
    if noon_tithi == 1:
      jd_prev_day_noon = daily_panchaanga.get_jd_prev_day_noon()
      tithi_span = anga_finder.find(jd1=jd_prev_day_noon, jd2=jd_noon, target_anga_id=1)
      if tithi_span is not None and (tithi_span.jd_start is None or tithi_span.jd_start > jd_prev_day_noon):
        return 1
      else:
        return 2
    elif noon_tithi < 29:
      if previous_day_panchaanga is not None:
        return previous_day_panchaanga.lunar_date.index + 1
      return noon_tithi
    elif noon_tithi >= 29:
      jd_next_day_noon = daily_panchaanga.get_jd_next_day_noon()
      tithi_span = anga_finder.find(jd1=(daily_panchaanga.jd_sunrise + daily_panchaanga.jd_sunset)/2, jd2=jd_next_day_noon, target_anga_id=1)
      if tithi_span is None:
        # Potentially duplicate day 29 (eg. if short tithi 29 touches both today and tomorrow noon).
        return 29
      else:
        # Potentially skip day 29  
        # (eg. if short tithi 30 is between today and tomorrow noon, but doesn't touch either).
        return 30

  def set_date(self, daily_panchaanga, previous_day_panchaanga=None):
    day = self._get_day(daily_panchaanga=daily_panchaanga, previous_day_panchaanga=previous_day_panchaanga)
    if day == 1:
      # It's possible that a short prathamA lies between two noons.  
      # In such a case, sending a tithi-30 time would yield the wrong month.
      # Hence the below.
      month = self._get_month(jd=daily_panchaanga.get_jd_noon() + 2)
    else:
      if previous_day_panchaanga is not None:
        month = previous_day_panchaanga.lunar_date.month
      else: 
        month = self._get_month(jd=daily_panchaanga.get_jd_noon())
    lunar_date = Tithi(month=month, index=day)
    daily_panchaanga.lunar_date = lunar_date


## TODO : Fix https://github.com/jyotisham/jyotisha/issues/142 by adding a more convulted variant of SolsticePostDark10AdhikaAssigner



# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
