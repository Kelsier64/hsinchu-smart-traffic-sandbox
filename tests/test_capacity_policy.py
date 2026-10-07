import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from capacity_policy import screen_route


class CapacityTests(unittest.TestCase):
    def call(self, demand=100, adoption=.5, **changes):
        s = dict(id='A>B', capacity=200, background=120, allowed=True, available=True,
                 trusted=True, interval='08:00/08:15', unit='vehicles/interval')
        s.update(changes)
        return screen_route([s], demand, adoption, '08:00/08:15', route_verified=True)

    def test_zero_demand(self):
        self.assertEqual(self.call(0)['expected_added_vehicles'], 0)

    def test_zero_adoption(self):
        self.assertEqual(self.call(adoption=0)['expected_added_vehicles'], 0)

    def test_full_adoption_capped(self):
        r = self.call(adoption=1)
        self.assertEqual(r['recommended_vehicles'], 50)
        self.assertEqual(r['status'], 'limited')
        self.assertLessEqual(r['loads_after']['A>B'], .85)

    def test_insufficient_capacity(self):
        self.assertEqual(self.call(background=180)['status'], 'excluded')

    def test_unknown(self):
        for kw in [dict(capacity=None), dict(background=None), dict(trusted=False),
                   dict(available=False), dict(allowed=None), dict(interval='09:00/09:15'), dict(unit='vehicles/hour')]:
            self.assertEqual(self.call(**kw)['status'], 'insufficient_data')

    def test_illegal(self):
        for kw in [dict(demand=-1), dict(demand=1.5), dict(adoption=1.1), dict(adoption=float('nan')),
                   dict(capacity=0), dict(capacity=float('inf')), dict(background=-1), dict(demand=True)]:
            with self.assertRaises(ValueError):
                self.call(**kw)

    def test_prohibited(self):
        self.assertEqual(self.call(allowed=False)['status'], 'excluded')

    def test_unverified_route(self):
        self.assertEqual(screen_route([{}], 0, 0, '08:00/08:15')['status'], 'insufficient_data')

    def test_bottleneck_and_rounding(self):
        base = dict(allowed=True, available=True, trusted=True, interval='x', unit='vehicles/interval', capacity=100)
        r = screen_route([dict(base, id='a', background=10), dict(base, id='b', background=84)],
                         100, .3, 'x', route_verified=True)
        self.assertEqual(r['recommended_vehicles'], 3)
        self.assertLessEqual(r['loads_after']['b'], .85)


if __name__ == '__main__':
    unittest.main()
