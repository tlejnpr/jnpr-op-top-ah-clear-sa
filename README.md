# On-box clear top AH sessions

Copyright 2021 Juniper Networks, Inc. All rights reserved.

## jnpr-op-top-ah-clear-sa.py

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

### Installation Instructions

1.  configure op script to personal needs (using a text editor)

2.  copy op script "jnpr-op-top-ah-clear-sa.py" onto target device, target directory is fixed

    ~~~
    to here: /var/db/scripts/op/jnpr-op-top-ah-clear-sa.py
    ~~~

3.  show sha256 checksum of op script

    ~~~
    % sha256 /var/db/scripts/op/jnpr-op-top-ah-clear-sa.py
    <af2f84e0c8..., copy checksum output to clipboard>
    ~~~

4.  configuration commands

    ~~~
    set system scripts language python3
    set system scripts op max-datasize 200000000
    set system scripts op file jnpr-op-top-ah-clear-sa.py command top-ah-clear-sa description "Process flow session table and act on presumable dead sessions"
    set system scripts op file jnpr-op-top-ah-clear-sa.py checksum sha-256 <af2f84e0c8...> <-- checksum
    commit
    ~~~

5.  test script from cli or shell

    ~~~
    user@srx1500> op top-ah-clear-sa
    ...
    ~~~

    ~~~
    user@srx1500> start shell
    % cli -c "op top-ah-clear-sa"
    ...
    %
    ~~~

5.  optional: configure hourly execution in config

    copy op script onto target device, into event directory:

    ~~~
    to here: /var/db/scripts/event/jnpr-op-top-ah-clear-sa.py
    ~~~

    ~~~
    set event-options generate-event hourlyEvent time-interval 3600
    set event-options generate-event hourlyEvent start-time "2021-11-25.23:25:00 +0000"
    set event-options policy evAhSessions events hourlyEvent
    set event-options policy evAhSessions then event-script jnpr-op-top-ah-clear-sa.py destination local-directory
    set event-options event-script max-datasize <200000000> <-- 196 MB max data size for python script execution
    set event-options event-script file jnpr-op-top-ah-clear-sa.py python-script-user <fwlocaluser>   <-- some script execution user
    set event-options event-script file jnpr-op-top-ah-clear-sa.py checksum sha-256 <af2f84e0c8...>   <-- sha-256 checksum
    set event-options destinations local-directory archive-sites /var/tmp/
    ~~~

### Configurable Parameters

These parameters can be adjusted either in the script itself, given as arguments to the op script invocation, or by setting them in event script invocation configuration (set event-options policy evAhSessions then event-script jnpr-op-top-ah-clear-sa.py arguments ...).

- "min-total-sessions" (integer)

    how many sessions to find at minimum in session table
    recommended: 10000 sessions listed overall

    > minimum_total_sessions_open = 10000

    must be greater than 5000 if used as command line argument

- "min-peer-sessions" (integer)

    how many sessions to find at minimum for any given peer
    recommended: 1000 sessions listed for peer

    > minimum_peer_sessions_open = 1000

    must be greater than 50 if used as command line argument

- "number-of-peers-to-clear" (integer)

    how many peer IP addresses to reset, if there are many;
    determined by number of reported sessions for that peer
    recommended: top 3 of them

    > top_x_talkers = 3

- "dry-run" (boolean) (on command line: 0 | 1)

    just show commands in dry run, or execute them actually
    suggested: True, dry run

    > dry_run = True

    to actually execute commands, "dry-run 0" must be provided

- "debug_level" ( 0 | 1 | 2 | 3)

    print state on stderr
        0: no output (production trust mode)
        1: informational (production with readable output)
        2: verbose
        3: debug (tons of output)

    > debug_level = 2

    default level of output is verbose (2)

### Sample output

- Dry run with Info logging level (2)

    ~~~
    lab@srx1500-r2603> op top-ah-clear-sa
    Looking for 10000+ ah sessions and 50+ peer sessions, top 3 are shown, logging level 2
    Start collecting flow sessions (this may take a minute)...
    Finished collecting flow sessions.
    Number of sessions in flow table: 21167
    Top talkers: ['4.0.0.2']
    Found 750 unique peers, with 1 peers having 50 or more sessions open. Top 3 peers are:
      4.0.0.2 (54 sessions)
    Indexes for IP 4.0.0.2: 67111733 67111734 67111735 67111736 67111737 67111738 67111739 67111740 67111741 67111742 67111724 67111743 67111725 67111726 67111730 67111731 67111732
    Dry run, not executing any operational commands.
    Statements to be executed (dry run):
      clear security ike security-associations 4.0.0.2
      clear security ipsec security-associations index 67111733
      clear security ipsec security-associations index 67111734
      clear security ipsec security-associations index 67111735
      clear security ipsec security-associations index 67111736
      clear security ipsec security-associations index 67111737
      clear security ipsec security-associations index 67111738
      clear security ipsec security-associations index 67111739
      clear security ipsec security-associations index 67111740
      clear security ipsec security-associations index 67111741
      clear security ipsec security-associations index 67111742
      clear security ipsec security-associations index 67111724
      clear security ipsec security-associations index 67111743
      clear security ipsec security-associations index 67111725
      clear security ipsec security-associations index 67111726
      clear security ipsec security-associations index 67111730
      clear security ipsec security-associations index 67111731
      clear security ipsec security-associations index 67111732
    All done.
    ~~~

- Executed on device with one matching peer IP, clearing that peer

    ~~~
    lab@srx1500-r2603> op top-ah-clear-sa
    Looking for 10000+ ah sessions and 50+ peer sessions, top 3 are cleared, logging level 2
    Start collecting flow sessions (this may take a minute)...
    Finished collecting flow sessions.
    Number of sessions in flow table: 21118
    Top talkers: ['4.0.0.2']
    Found 750 unique peers, with 1 peers having 50 or more sessions open. Top 3 peers are:
      4.0.0.2 (54 sessions)
    Indexes for IP 4.0.0.2: 67111733 67111734 67111735 67111736 67111737 67111738 67111739 67111740 67111741 67111742 67111724 67111743 67111725 67111726 67111730 67111731 67111732
    Clearing ike sa and ipsec sa indices for top 1 talking peers...
    Statements sent:
      clear security ike security-associations 4.0.0.2
      clear security ipsec security-associations index 67111733
      clear security ipsec security-associations index 67111734
      clear security ipsec security-associations index 67111735
      clear security ipsec security-associations index 67111736
      clear security ipsec security-associations index 67111737
      clear security ipsec security-associations index 67111738
      clear security ipsec security-associations index 67111739
      clear security ipsec security-associations index 67111740
      clear security ipsec security-associations index 67111741
      clear security ipsec security-associations index 67111742
      clear security ipsec security-associations index 67111724
      clear security ipsec security-associations index 67111743
      clear security ipsec security-associations index 67111725
      clear security ipsec security-associations index 67111726
      clear security ipsec security-associations index 67111730
      clear security ipsec security-associations index 67111731
      clear security ipsec security-associations index 67111732
    All done.
    ~~~

- Executed on a device with no matching peer IPs (not enough individual session), so no op statements generated

    ~~~
    lab@srx1500-r2603> op top-ah-clear-sa
    Looking for 10000+ ah sessions and 50+ peer sessions, top 3 are cleared, logging level 2
    Start collecting flow sessions (this may take a minute)...
    Finished collecting flow sessions.
    Number of sessions in flow table: 21043
    Top talkers: []
    Found 750 unique peers, with 0 peers having 50 or more sessions open. Top 3 peers are:
    Clearing ike sa and ipsec sa indices for top 0 talking peers...
    Statements sent:
    All done.
    ~~~

- Executed on device with one matching peer IP, clearing that peer

    ~~~
    lab@srx1500-r2603> op top-ah-clear-sa
    Looking for 10000+ ah sessions and 50+ peer sessions, top 3 are cleared, logging level 2
    Start collecting flow sessions (this may take a minute)...
    Finished collecting flow sessions.
    Number of sessions in flow table: 25950
    Top talkers: ['2.0.0.146', '2.0.0.150', '1.0.0.42']
    Found 750 unique peers, with 385 peers having 40 or more sessions open. Top 3 peers are:
      2.0.0.146 (62 sessions)
      2.0.0.150 (62 sessions)
      1.0.0.42 (58 sessions)
    Indexes for IP 2.0.0.146: 67109704 67109705 67109706 67109707 67109708
    Indexes for IP 2.0.0.150: 67109724 67109725 67109726 67109727 67109728
    Indexes for IP 1.0.0.42: 67109684 67109685 67109686 67109687
    Clearing ike sa and ipsec sa indices for top 3 talking peers...
    Statements sent:
      clear security ike security-associations 2.0.0.146
      clear security ipsec security-associations index 67109704
      clear security ipsec security-associations index 67109705
      clear security ipsec security-associations index 67109706
      clear security ipsec security-associations index 67109707
      clear security ipsec security-associations index 67109708
      clear security ike security-associations 2.0.0.150
      clear security ipsec security-associations index 67109724
      clear security ipsec security-associations index 67109725
      clear security ipsec security-associations index 67109726
      clear security ipsec security-associations index 67109727
      clear security ipsec security-associations index 67109728
      clear security ike security-associations 1.0.0.42
      clear security ipsec security-associations index 67109684
      clear security ipsec security-associations index 67109685
      clear security ipsec security-associations index 67109686
      clear security ipsec security-associations index 67109687
    All done.
    ~~~

### Syslog output examples

- Syslog with flag dry_run set

    ~~~
    Nov 23 21:03:53  srx1500-r2603 cscript: top-ah-clear-sa[22240]: starting flow session table scan.
    Nov 23 21:04:58  srx1500-r2603 cscript: top-ah-clear-sa[22240]: dry_run: found 3 peers to clear - 3.0.0.158 2.0.0.146 2.0.0.150
    Nov 23 21:05:00  srx1500-r2603 cscript: top-ah-clear-sa[22240]: all done, exiting.
    ~~~
    ~~~
    Nov 23 21:14:02  srx1500-r2603 cscript: top-ah-clear-sa[22762]: starting flow session table scan.
    Nov 23 21:15:09  srx1500-r2603 cscript: top-ah-clear-sa[22762]: dry_run: found 0 peers to clear -
    ~~~

- Syslog with clearing sessions on device

    ~~~
    Nov 23 21:15:54  srx1500-r2603 cscript: top-ah-clear-sa[22850]: starting flow session table scan.
    Nov 23 21:17:02  srx1500-r2603 cscript: top-ah-clear-sa[22850]: selected 0 peers to clear -
    ~~~
    ~~~
    Nov 23 23:05:09  srx1500-r2603 cscript: top-ah-clear-sa[27240]: starting flow session table scan.
    Nov 23 23:06:14  srx1500-r2603 cscript: top-ah-clear-sa[27240]: selected 3 peers to clear - 2.0.0.146 2.0.0.150 1.0.0.42
    Nov 23 23:06:19  srx1500-r2603 cscript: top-ah-clear-sa[27240]: cleared ike sa and ipsec sa for peers: 2.0.0.146 2.0.0.150 1.0.0.42
    ~~~
