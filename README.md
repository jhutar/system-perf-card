Assess generic performance of a system
======================================

This project tries to address these use-cases:

1. Measure HW and OS performance of a host and create **one number** to express it. Allow to drill down to details.
2. We want to assess raw HW or OS performance of multiple hosts, so we can **compare** them to allow us to relate the difference to different performance of our workload on them.
3. We want to know how host performance changes **over time** as OS updates or HW changes are being applied.

And main goal here is to make the process as simple as possible: run and evaluate the test and do not modify the tested host in any way.

To be able to achieve this, we need bunch of benchmarks to measure different performance aspects of a host.
Then we can make the result relative to some baseline and compare these relative numbers across hosts.
With a lot of help I have defined few benchmarks (see `measure.yaml`).
There are few benchmarks to measure memory performance, some to measure CPU (I assume some measure memory as well) and few to measure disk.

We can have lots of complains about the selection.
Some that come to my mind in no particular order:

* Benchmarks running for 1 minute only? Come on!
* Metrics in stress-ng are not meant to be used for benchmarking/measurements!
* This is only testing root disk performance!
* Who picked these params here? They are completely wrong!
* ...please share yours

Although I agree with the complaints above, I still think this set of benchmarks is some start.
Let's just assume, for now, these make sense.

For every benchmark, I also define a reg-exp on how to get a single numerical result from the output.
It uses modified `quay.io/pbench/pbench-agent-all-centos-8` container from <https://distributed-system-analysis.github.io/pbench/> project to run the test and store monitoring data.

See `webapp/` directory for a simple application that can be used to store results, visualize them and get final performance index number.


Running
-------

Prepare `inventory.ini` file with hosts to measure:

    [systems]
    192.168.1.2 ansible_user=cloud-user ansible_become=yes ansible_become_method=sudo ansible_become_user=root

And then run the playbook:

    ansible-galaxy collection install -r requirements.yaml
    ansible-playbook -i inventory.ini measure.yaml
