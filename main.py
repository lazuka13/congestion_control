#!/usr/bin/python

import os
import shutil
import subprocess
import textwrap

import click
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt

CONGESTION_CONTROLS_ALGORITHMS = "reno, bbr, bic, cubic, dctcp, westwood, highspeed, " \
                                 "hybla, htcp, vegas, veno, scalable, lp, yeah, Illinois".split(",")
CONGESTION_CONTROLS_ALGORITHMS = [cc.strip() for cc in CONGESTION_CONTROLS_ALGORITHMS]
ROOT_DIR = "/home/simuser/repos/dce-4.19.79/source/ns-3-dce/"


@click.command()
@click.option('--congestion_control', '-c', required=False, help='congestion control algorithm',
              type=click.Choice(CONGESTION_CONTROLS_ALGORITHMS), multiple=True)
def run(congestion_control):
    if not congestion_control:
        congestion_control = CONGESTION_CONTROLS_ALGORITHMS
    results = dict()
    for cc in congestion_control:
        results[cc] = list()
        for error_rate in [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50]:
            error_rate_percent = error_rate / 10000.0
            results_folder = "{0}_{1}".format(cc, error_rate)
            results_folder_full = os.path.join(ROOT_DIR, "results", results_folder)
            results_folder_local = os.path.join(".", "data", results_folder)
            args = textwrap.dedent("""
            ./waf --run "task --congControl={congestion_control} 
            --errorRate={error_rate_percent:.2} --folderName={results_folder}"
            """).replace("\n", "").format(
                congestion_control=cc,
                error_rate_percent=error_rate_percent,
                results_folder=results_folder)
            if not os.path.exists(results_folder_local):
                print("starting: {0}".format(args))
                subprocess.check_call(args, shell=True, cwd=ROOT_DIR)
                shutil.copytree(results_folder_full, results_folder_local)
            else:
                print("skipping: {0}".format(args))

            with open(os.path.join(results_folder_local, "throughput", "client.log")) as server_log_file:
                server_log = [l.strip() for l in server_log_file.readlines() if l.strip()]

            b_total, t_start, t_end = 0, None, 0
            for line in server_log:
                t, b = line.split(" ")
                if t_start is None:
                    t_start = float(t)
                t_end = float(t)
                b_total += float(b) * 8 * 10.0 / 1000  # convert to bytes and * 10 ms == sent in this 10 ms
            results[cc].append(b_total / (float(t_end - t_start) * 1024 ** 3))  # utilization

    error_rate_percents = [x / 10000.0 for x in [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50]]

    for cc in congestion_control:
        plt.plot(error_rate_percents, results[cc], label=cc)

    plt.xlabel('error_rate_percentage')
    plt.ylabel('throughput percentage')
    plt.margins(0.05)
    legend = plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1),
                        ncol=3, fancybox=True, shadow=True)
    plt.savefig('./result.png', bbox_extra_artists=(legend,), bbox_inches='tight')


if __name__ == "__main__":
    run()
