import unittest

from engine.report import unverified_numbers


def test_scientific_notation_dollar_amounts():
    metrics = {"holding_value": 2500}
    assert unverified_numbers("The holding is worth $2500.", metrics) == []
    assert unverified_numbers("The holding is worth $2.5e3.", metrics) == []
    assert unverified_numbers("The holding is worth $2.5E+3.", metrics) == []
    assert unverified_numbers("The holding is worth $2500e3.", metrics) == [2500000.0]


def test_negative_exponent_scientific_notation():
    metrics = {"weight": 0.05}
    assert unverified_numbers("The weight is 5e-2.", metrics) == []
    assert unverified_numbers("The weight is 5e2.", metrics) == [500.0]


class TestReportVerifier(unittest.TestCase):
    def test_scientific_notation(self):
        test_scientific_notation_dollar_amounts()
        test_negative_exponent_scientific_notation()


if __name__ == "__main__":
    unittest.main()
