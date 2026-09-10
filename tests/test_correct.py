from krishiayan.services.correct import correct_optical, moisture_correction_gain


def test_wet_soil_boosts_optical():
    dry = moisture_correction_gain(10)
    wet = moisture_correction_gain(35)
    assert wet > dry
    assert wet > 10  # 35% moisture is a large correction — this is the IP


def test_corrected_not_collapsed():
    raw = 0.20
    uncorrected_wet = raw  # hardware collapse already in raw
    corrected = correct_optical(raw, 35, "black_cotton")
    assert corrected is not None
    assert corrected > uncorrected_wet * 5
