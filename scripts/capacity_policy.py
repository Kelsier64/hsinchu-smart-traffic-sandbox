"""Single-route scenario filter. Hypothetical inputs, NOT traffic equilibrium."""
from math import isfinite, floor


def number(value, name, minimum=0, maximum=None):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not isfinite(value):
        raise ValueError(name + ' must be finite numeric')
    if value < minimum or (maximum is not None and value > maximum):
        raise ValueError(name + ' out of range')
    return value


def screen_route(segments, demand, adoption, interval, unit='vehicles/interval', load_limit=.85,
                 route_verified=False):
    """Expected added flow = recommended vehicles * adoption, every directed edge once.

    Whole-vehicle cap rounded down. Shared-edge slack MUST be updated before
    allocating other routes. Unknown data or connectivity => insufficient_data.
    """
    demand = number(demand, 'demand')
    adoption = number(adoption, 'adoption', maximum=1)
    load_limit = number(load_limit, 'load_limit', minimum=.000001, maximum=1)
    if demand % 1 or not isinstance(interval, str) or not interval:
        raise ValueError('integer demand and explicit interval required')
    if unit != 'vehicles/interval' or not isinstance(segments, list) or not segments:
        raise ValueError('vehicle/interval units and nonempty route required')
    if not route_verified:
        return {'status': 'insufficient_data', 'reason': 'direction/connectivity/turns unverified'}
    ids = [s.get('id') for s in segments]
    if any(not isinstance(i, str) or not i for i in ids) or len(set(ids)) != len(ids):
        raise ValueError('unique directed segment IDs required')
    slacks = []
    for s in segments:
        if s.get('allowed') is False:
            return {'status': 'excluded', 'reason': 'prohibited segment: ' + s['id']}
        if s.get('allowed') is not True or s.get('available') is not True or s.get('trusted') is not True:
            return {'status': 'insufficient_data', 'reason': 'restriction/availability/quality unknown'}
        if s.get('interval') != interval or s.get('unit') != unit:
            return {'status': 'insufficient_data', 'reason': 'interval or unit mismatch'}
        if s.get('capacity') is None or s.get('background') is None:
            return {'status': 'insufficient_data', 'reason': 'unknown capacity or background'}
        cap = number(s['capacity'], 'capacity', minimum=.000001)
        bg = number(s['background'], 'background')
        slacks.append(load_limit * cap - bg)
    if min(slacks) < 0:
        return {'status': 'excluded', 'reason': 'background already above limit'}
    requested_added = demand * adoption
    recommended = int(demand) if adoption == 0 else min(int(demand), floor(min(slacks) / adoption))
    added = recommended * adoption
    return {'status': 'eligible' if recommended == demand else 'limited',
            'recommended_vehicles': recommended, 'expected_added_vehicles': added,
            'requested_added_vehicles': requested_added, 'adoption': adoption,
            'load_limit': load_limit, 'interval': interval,
            'loads_after': {s['id']: (s['background'] + added) / s['capacity'] for s in segments},
            'evidence': 'hypothetical scenario; no measured benefit or equilibrium claim'}
