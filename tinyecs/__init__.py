from uuid import uuid4

eidx = {}
cidx = {}
fidx = {}


def create_entity(tag=None, **kwargs):
    global eidx, cidx

    eid = tag if tag else str(uuid4())
    eidx[eid] = {}

    # Add optionally passed components
    for cid, comp in kwargs.items():
        add_component(eid, cid, comp)

    return eid


def remove_entity(eid):
    # Ignore unknown eids, since we're removing anyways
    try:
        cids = eidx[eid].keys()
    except KeyError:
        return

    for cid in cids:
        del cidx[cid][eid]

    del eidx[eid]


def add_component(eid, cid, comp):
    global eidx, cidx

    if eid not in eidx:
        raise KeyError(f'{eid} not registered')

    if cid not in cidx:
        cidx[cid] = {}

    cidx[cid][eid] = comp
    eidx[eid][cid] = comp


def remove_component(eid, cid):
    global eidx, cidx

    # Ignore unknown cids or eids since we're removing anyways
    # Also, no need to try each on their own
    try:
        del cidx[cid][eid]
        del eidx[eid][cid]
    except KeyError:
        pass


def add_system(fkt, *comps):
    fidx[fkt] = comps


def remove_system(fkt):
    # Ignore unregistered systems, since we're removing anyways
    try:
        del fidx[fkt]
    except KeyError:
        pass


def eids_by_cids(*cids):
    eid_sets = [set(cidx[cid].keys()) for cid in cids]

    return list(set.intersection(*eid_sets))


def cids_of_eid(eid):
    return list(eidx[eid].keys())


def comps_of_eid(eid, *cids):
    if not cids:
        return eidx[eid].values()

    return [eidx[eid][cid] for cid in cids]


def run_system(dt, fkt, *cids):
    eids = eids_by_cids(*cids)

    return {eid: fkt(dt, eid, *comps_of_eid(eid, *cids))
            for eid in eids}


def run_all_systems(dt):
    return {fkt: run_system(dt, fkt, *comps)
            for fkt, comps in fidx.items()}
