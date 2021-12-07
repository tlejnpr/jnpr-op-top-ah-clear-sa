"""
Copyright 2021 Juniper Networks, Inc. All rights reserved.
"""

"""
jnpr-op-top-ah-clear-sa.py

One-shot script to process flow session table and check on preconfigured
thresholds, act on presumable dead protocol ah sessions when thresholds
are exceeded.

This version takes care of heaps of "protocol ah" sessions, and tries
to get rid of presumably dead or unwanted sessions by both clearing
associated ike sa and all ipsec sa (by index).

Configured correctly™, it can be scheduled to run once an hour as event
script (via set event-options...). It can be used manually anytime as op
script.

This script is written in Python 3 language dialect.
"""

from jnpr.junos import Device
from collections import defaultdict
from time import sleep
from jcs import syslog
from os import getpid
import logging, sys

# minimum_total_sessions_open (integer)
#
# how many sessions of protocol ah to find at minimum
# in session table recommended: 10000 sessions listed
# overall
#
minimum_total_sessions_open = 10000

# minimum_peer_sessions_open (integer)
#
# how many sessions to find at minimum for any given peer
# recommended: 1000 sessions listed for peer
#
minimum_peer_sessions_open = 1000

# top_x_talkers (integer)
#
# how many peer IP addresses to reset, if there are many;
# determined by number of reported sessions for that peer
# recommended: top 3 of them
#
top_x_talkers = 3

# dry_run (boolean)
#
# just show commands in dry run, or execute them actually
# suggested: True, dry run
#
dry_run = True

# debug_level ( 0 | 1 | 2 )
#
# print state on stderr
#   0: no output (performance measurement only)
#   1: informational (normal)
#   2: verbose
#   3: debug (lots of stuff)
#
debug_level = 2


def to_syslog(message):
    syslog("external.info", "top-esp-clear-sa[{}]: "
           .format(getpid()), message)

def bounce_top_talkers(dev):
    """
    Do what I mean
    """

    # logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    if debug_level == 0:
        logger.addHandler(logging.NullHandler())
    else:
        logger.addHandler(logging.StreamHandler())
        if debug_level == 1:
            logger.setLevel(logging.INFO)
        elif debug_level == 2:
            logger.setLevel(logging.DEBUG)
        else: #if debug_level > 1
            logger.setLevel(5)

    logger.info("Looking for {}+ ah sessions and {}+ peer sessions, top {} "
                "are {}, logging level {}".format(minimum_total_sessions_open,
                minimum_peer_sessions_open, top_x_talkers,
                "shown (DRY RUN)" if dry_run else "cleared", debug_level))

    to_syslog("starting flow session table scan.")

    logger.debug("Start collecting flow sessions (this may take a minute)...")

    srcip = defaultdict(int)
    salist = defaultdict(list)
    satemp = defaultdict(dict)

    """
    Phase 1: collect flow session statistics and select top talkers
    """

    # cli("show security flow session protocol ah", format="xml", warning=True)
    flowsessions = dev.rpc.get_flow_session_information(protocol="ah",
        dev_timeout=360)

    logger.debug("Finished collecting flow sessions.")

    total_sessions = int(flowsessions.findtext("displayed-session-count").strip("\n"))
    logger.debug("Number of sessions in flow table: {}".format(total_sessions))
    if total_sessions < minimum_total_sessions_open:
        logger.info("Found {} sessions in flow table total, preset minimum is {}, nothing to do."
              .format(total_sessions, minimum_total_sessions_open))
        return False

    for e in flowsessions.findall("flow-session/flow-information/source-address"):
        ip = e.text.strip("\n")
        #logger.log(5, "Source address: " + ip)
        srcip[ip]+=1

    peers_suspicious = {k: v for k, v in srcip.items() if v >= minimum_peer_sessions_open}
    talkers_sorted = {k: v for k, v in sorted(peers_suspicious.items(), reverse=True, key=lambda item: item[1])}
    top_peers = list(talkers_sorted.keys())[:top_x_talkers]

    logger.log(1, "All sus peers:" + str(peers_suspicious))
    logger.log(5, "All talkers:" + str(talkers_sorted))
    logger.debug("Top talkers: " + str(top_peers))

    logger.info(("Found {} unique peers, with {} peers having {} or more sessions open. " \
           "Top {} peers are:").format(len(srcip), len(talkers_sorted),
           minimum_peer_sessions_open, top_x_talkers))
    for peer in top_peers:
        logger.info("  {} ({} sessions)".format(peer, talkers_sorted[peer]))

    """
    Phase 2: collect ipsec security-assosiactions table select indices interested in
    """

    # cli("show security ipsec security-associations", format="xml", warning=True)
    ipsecsas = dev.rpc.get_security_associations_information()
    for e in ipsecsas.findall("ipsec-security-associations-block/ipsec-security-associations"):
        ip = e.findtext("sa-remote-gateway").strip("\n")
        index = e.findtext("sa-tunnel-index").strip("\n")
        #logger.log(5, "Found ip={} index={} in {}".format(ip, index, str(e)))
        satemp[ip][index] = 0

    logger.log(1, "All SA indices:" + str(satemp))

    for peer in top_peers:
        salist[peer] = satemp[peer].keys()
    del satemp

    logger.log(5, "All needed SA indices:" + str(salist))
    for peer in top_peers:
        logger.info("Indexes for IP {}: {}".format(peer, " ".join(salist[peer])))

    """
    Phase 3: show clear ike/ipsec statements for on-device execution
    """

    to_syslog("{} {} peers to clear - {}".format(
              ("dry_run: found" if dry_run else "selected"),
              len(top_peers), " ".join(top_peers)))

    if dry_run:
        logger.info("Dry run, not executing any operational commands.")
    else:
        logger.info("Clearing ike sa and ipsec sa indices for top {} talking peers...".format(len(top_peers)))
    logger.debug("Statements {}:".format("sent" if not dry_run else "to be executed (dry run)"))
    for peer in top_peers:
        cmd = "clear security ike security-associations {}".format(peer)
        logger.debug("  " + cmd)
        if not dry_run and not dev.rpc.clear_ike_security_association({"peer-address": peer}):
            logger.error("RPC call for '" + cmd + "' failed, continuing anyway")
        sleep(0.5)
        for index in salist[peer]:
            cmd = "clear security ipsec security-associations index {}".format(index)
            logger.debug("  " + cmd)
            if not dry_run and not dev.rpc.clear_ipsec_security_association({"index": index}):
                logger.error("RPC call for '" + cmd + "' failed, continuing anyway")

    to_syslog("all done, exiting.")
    logger.info("All done.")
    return True

if __name__ == "__main__":
    with Device() as dev:
        bounce_top_talkers(dev)
