Assess generic performance of a system
======================================

Notes about pbench
------------------

    $ mkdir /var/tmp/fiotest
    $ mkdir /tmp/fiotest
    $ sudo podman run -it --privileged -v /var/tmp/fiotest:/fiotest_disk:Z -v /tmp/fiotest:/fiotest_memory:Z quay.io/pbench/pbench-agent-all-centos-8
    # pbench-register-tool-set heavy
    # pbench-fio --config=read-test --ioengine=libaio --iodepth=1 --test-types=read --direct=1 --file-size=512M --numjobs=2 --targets=/fiotest_disk/fio
    # pbench-fio --config=read-test --ioengine=libaio --iodepth=1 --test-types=read --direct=1 --file-size=512M --numjobs=2 --targets=/fiotest_memory/fio

Prerequisities
--------------

    ansible-galaxy collection install -r requirements.yaml
