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
@click.option('--congestion_control', '-c', required=True, help='congestion control algorithm',
              type=click.Choice(CONGESTION_CONTROLS_ALGORITHMS), multiple=True)
def run(congestion_control):
    results = dict()
    for cc in congestion_control:
        results[cc] = list()
        for error_rate in [5, 10, 15, 20, 25, 50]:
            error_rate_percent = error_rate / 100.0
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
                continue
                # print("starting: {0}".format(args))
                # subprocess.check_call(args, shell=True, cwd=ROOT_DIR)
                # shutil.copytree(results_folder_full, results_folder_local)
            else:
                print("skipping: {0}".format(args))

            with open(os.path.join(results_folder_local, "throughput", "client.log")) as server_log_file:
                server_log = [l.strip() for l in server_log_file.readlines() if l.strip()]

            b_total, t = 0, 0
            for line in server_log:
                t, b = line.split(" ")
                b_total += float(b) * 8
            results[cc].append([error_rate, b_total / (float(t) * 1024 ** 3)])

        x, y = [], []
        for (error_rate, throughput) in results[cc]:
            x.append(error_rate)
            y.append(throughput)

        plt.clf()
        plt.plot(x, y)
        plt.xlabel('error_rate')
        plt.ylabel('throughput percentage')
        plt.savefig('./graphs/{0}_result.png'.format(cc))


if __name__ == "__main__":
    run()
