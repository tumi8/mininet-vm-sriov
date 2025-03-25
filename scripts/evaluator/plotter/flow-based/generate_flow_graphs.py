"""
Generates all flow-based plots as needed
"""
import csv
import logging
import colorsys
import math
import os
import sys
import re
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

import matplotlib.pyplot as plt
import pandas as pd
import postools as pos  # pylint: disable=import-error
import pylatex as pl
import numpy as np

experiment = sys.argv[1]
flows = int(pos.get("HVNet", _global=False, loop=False, delimiter=" ", remote=False)["flownumber"][int(experiment)])
repeat = int(pos.get("ATSBPR", _global=False, loop=False, delimiter=" ", remote=False)["REPEAT"])
processingdelay = pos.get("processingDelay", _global=False, loop=False, delimiter=" ", remote=False).split(";")
NC_DIR = "../nc/"
RESULTS_DIR = "results/"
FIGURES_DIR = "figures/"

templateFolder = Path('./template')
env = Environment(loader=FileSystemLoader(templateFolder))

"""
Generate a new list of colors
"""


def _get_colors(num_colors):
    colors = []
    for index in np.arange(0., 360., 360. / num_colors):
        hue = index / 360.
        lightness = (50 + np.random.rand() * 10) / 100.
        saturation = (90 + np.random.rand() * 10) / 100.
        colors.append(colorsys.hls_to_rgb(hue, lightness, saturation))
    return colors


#  Functions from https://gitlab.lrz.de/I8-testbeds/plot_scripts/-/blob/master/plot_latency.py by Dominik Scholz


def to_microsecond(data_local, keys=True, values=False):
    """
    to microseconds rounding from nanoseconds
    :param data_local: The data to round
    :param keys: To round keys
    :param values: To round values
    :return: The new data list
    """
    if keys and values:
        return {k / 1000: v / 1000 for k, v in data_local.items()}
    if keys:
        return {k / 1000: v for k, v in data_local.items()}
    if values:
        return {k: v / 1000 for k, v in data_local.items()}
    return None


def to_ms_bins(data_para, round_ms_digits=3):
    """
    To milliseconds instead of nanoseconds in bins
    :param data_para: The data to be put in bins
    :param round_ms_digits: The digits to round
    :return: the rounded dictionary
    """
    binned = {}
    for key, value in data_para.items():
        rounded = round(key, round_ms_digits)
        if rounded not in binned:
            binned[rounded] = value
        else:
            binned[rounded] += value
    return binned


def normalize(data_par):
    """
    Normalizing the submitted data
    :param data_par: The data to normalize
    :return: The percentiles as list
    """
    total = sum(data_par.values())        
    return {k: (v / total) for k, v in data_par.items()}


def accumulate(data_par):
    """
    Accumulate the vars as needed for CDF and HDR plots
    :param data_par: The data to accumulate
    :return: The accumulated data as list
    """
    curr = 0

    def acc(val):  # just for the list comprehension
        nonlocal curr
        curr += val
        return curr

    return {k: acc(v) for k, v in sorted(data_par.items())}


def to_hdr(data_par):
    """
    The function os dividing the data as needed for the HDR diagramm
    :param data_par:
    :return:
    """
    # treat negative (>1.0) and exact 1.0 values and very high values for v
    max_accuracy = 1000000000
    return {k: 1 / (1 - v) for k, v in data_par.items() if
            not (1 - v) == 0.0 and not 1 / (1 - v) < 0 and not 1 / (1 - v) > max_accuracy}


def get_sorted_values(x_items, y_items, sort_by='xs'):
    """
    Sort the values either xs or ys
    :param x_items: The x axis items
    :param y_items: The y axis items
    :param sort_by: which axis to sort by
    :return:
    """
    # necessary for python <3.6
    if sort_by == 'xs':
        sort_by = 0
    else:
        sort_by = 1
    tup = zip(x_items, y_items)
    tup = sorted(tup, key=lambda x: x[sort_by])
    x_items = [x for x, _ in tup]
    y_items = [y for _, y in tup]
    return x_items, y_items


def plot_hdr(data_par, name=''):
    """
    Plotting a high-definition range diagram
    :param data_par: The data used
    :param name: The name of the resulting file
    """
    _, axis = plt.subplots(figsize=(9, 6))
    max_value = 0
    min_value = 10000000000
    for exp, data_loc in sorted(data_par.items()):
        hdr = data_loc
        x_items = list(hdr.values())
        y_items = list(hdr.keys())
        if not y_items:
            continue
        x_items, y_items = get_sorted_values(x_items, y_items)
        max_value = max(max_value, max(y_items))
        min_value = min(min_value, min(y_items))
        axis.plot(x_items, y_items, label=exp)  

    # automatically determine min/max based on min/max values log10
    if max_value > 0:
        log_max = pow(10, math.ceil(math.log10(max_value)))
        log_min = pow(10, math.floor(math.log10(min_value)))
    else:
        log_max = 100
        log_min = 1

    plt.ylim(bottom=log_min)
    plt.ylim(top=log_max)

    axis.grid()
    axis.set(xlabel='Percentile [\%] (log)',  # pylint: disable=anomalous-backslash-in-string
             ylabel='Latency [$\mu$s] (log)')  # pylint: disable=anomalous-backslash-in-string
    axis.set_xscale('log')
    axis.set_yscale('log')
    ticks = [1, 2, 10, 100, 1000, 10000, 100000, 1000000]
    labels = ["0", "50", "90", "99", "99.9", "99.99", "99.999", "99.9999"]
    plt.xticks(ticks, labels)
    axis.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.xlim(left=1)

    plt.savefig(f"{FIGURES_DIR}hdr-repeat{name}.pdf")
    plt.clf()


def plot_cdf(data_par, name=''):
    """
    Is plotting a CDF based on the data
    :param data_par: The data to plot
    :param name: The name of the plot
    :return:
    """
    _, axis = plt.subplots(figsize=(9, 6))

    for exp, data_local in sorted(data_par.items()):
        cdf = data_local
        x_data = list(cdf.keys())
        y_data = [100 * val for val in cdf.values()]
        x_data, y_data = get_sorted_values(x_data, y_data)
        axis.plot(x_data, y_data, label=exp)

    plt.ylim(bottom=0)
    plt.ylim(top=100)

    axis.grid()
    axis.set(ylabel='CDF [\%]',  # pylint: disable=anomalous-backslash-in-string
             xlabel='Latency [$\mu$s]')  # pylint: disable=anomalous-backslash-in-string
    axis.legend(loc='upper left', bbox_to_anchor=(1, 1))

    plt.xlim(left=0)

    plt.savefig(f"{FIGURES_DIR}cdf-repeat{name}.pdf")
    plt.show()


def plot_hist(df_latency_small, df_nc_local, flow, repeat_var, delay):
    """
    Is plotting an histogram
    :param df_latency_small: The small latencies datagram
    :param df_nc_local: The network coding datagram
    :param flow: The flows number
    :param repeat_var: The number of repeats
    :param delay: The current delay
    :return:
    """
    df_hist = df_latency_small[i - 1]
    if not df_hist.empty:
        df_hist = df_hist.loc[df_hist["dstport"] == f"\\10{z:02d}"]
        quants = [[df_hist["latency"].quantile(0.05), 0.6, 0.16],
                  [df_hist["latency"].quantile(0.25), 0.8, 0.26],
                  [df_hist["latency"].quantile(0.5), 1, 0.36],
                  [df_hist["latency"].quantile(0.75), 0.8, 0.46],
                  [df_hist["latency"].quantile(0.95), 0.6, 0.56],
                  [df_hist["latency"].quantile(0.99), 0.6, 0.65],
                  [df_hist["latency"].quantile(0.999), 0.6, 0.70],
                  [df_hist["latency"].quantile(0.9999), 0.6, 0.75]]
        y_iter, _, _ = plt.hist(df_hist["latency"], label="Flow " + str(flow), bins=1000)
        for k in quants:
            plt.vlines(k[0], ymin=0, ymax=k[1] * y_iter.max(), alpha=k[1], linestyle=":", color="red")

        if isinstance(df_nc_local, pd.DataFrame):
            # NC
            nc_var = df_nc_local[df_nc_local["flow_id"] == flow]
            nc_lines = [[nc_var["tfa_delay"], 1, 1, "green", "tfa-delay"], [nc_var["sfa_delay"],
                                                                            1, 1, "orange", "sfa-delay"],
                        [nc_var["pmooa_delay"], 1, 1, "purple", "pmooa-delay"],
                        [nc_var["tma_delay"], 1, 1, "yellow", "tma-delay"]]
            if not math.isnan(nc_var["ulp_delay"].iloc[0]):
                nc_lines.append([nc_var["ulp_delay"], 1, 1, "black", "ulp-delay"])
            # NC
            for k in nc_lines:
                plt.vlines(k[0].iloc[0], ymin=0, ymax=y_iter.max(), label=k[4], linestyle="--", color=k[3])

        plt.legend()
        plt.grid()
        plt.xlabel("ns")
        plt.yscale("log")
        plt.xscale("log")
        plt.ylabel("Samples")
        plt.savefig(f"{FIGURES_DIR}histlatency-repeat{repeat_var}-flow{flow}-processing{delay}.pdf")
        plt.clf()


# End functions from plot_scripts for pos


plt.rcParams["text.usetex"] = True
plt.rcParams["font.family"] = "serif"
plt.rcParams[
    'text.latex.preamble'] = r'\usepackage{lmodern}\usepackage{oldgerm}\usepackage[T1]{fontenc}\usepackage{upgreek}'

# Get the list of files to process
df_latency = []
for i in range(0, int(repeat)):
    # Move to panda
    tempPanda = pd.read_csv(RESULTS_DIR + f"latencies-pre-repeat{i}.pcap.zst.latency-flows.csv",
                            usecols=["latency", "dstport"])
    df_latency.append(tempPanda)

# Print Average and worst case per flow
df_latency_average = []
df_latency_worst = []
df_latency_csv = []
X_ITER = 0
for i in df_latency:
    if not i.empty:
        tempListPanda = i.groupby("dstport")
        tempPanda = tempListPanda.mean()
        tempPanda['repeat'] = X_ITER
        df_latency_average.append(tempPanda)
        tempPanda = tempListPanda.max()
        tempPanda['repeat'] = X_ITER
        df_latency_worst.append(tempPanda)
        tempPanda = i.groupby(["dstport", "latency"]).size()
        df_latency_csv.append(tempPanda)
    else:
        df_latency_csv.append(pd.DataFrame(columns=['repeat', 'dstport', 'latency']))
        df_latency_average.append(pd.DataFrame(columns=['repeat', 'dstport', 'latency']))
        df_latency_worst.append(pd.DataFrame(columns=['repeat', 'dstport', 'latency']))
    X_ITER = X_ITER + 1

# Export data and save them
doc = pl.Document(documentclass='standalone')
doc.packages.append(pl.Package('booktabs'))
doc.append(pl.NoEscape(pd.concat(df_latency_worst).to_latex(escape=True)))
doc.generate_pdf(FIGURES_DIR + 'latencyWorstCase.pdf', clean_tex=False)
doc = pl.Document(documentclass='standalone')
doc.packages.append(pl.Package('booktabs'))
doc.append(pl.NoEscape(pd.concat(df_latency_average).to_latex(escape=True)))
doc.generate_pdf(FIGURES_DIR + 'latencyAverageCase.pdf', clean_tex=False)

for w in processingdelay:
    DF_NC = False
    if os.path.isfile(NC_DIR + "nc-" + str(w) + ".csv"):
        DF_NC = pd.read_csv(NC_DIR + "nc-" + str(w) + ".csv")
        for i in ["tfa_delay", "sfa_delay", "pmooa_delay", "tma_delay", "ulp_delay"]:
            DF_NC[i] = 1000000000 * DF_NC[i]  # s to ns
        DF_NC["flow_id"] = DF_NC["flow_id"].str[1:].astype(int) + 1

    for i in range(0, int(repeat)):
        for z in range(1, int(flows) + 1):
            plot_hist(df_latency, DF_NC, z, i, w)

for i in range(0, int(repeat)):
    for z in range(1, int(flows) + 1):
        data = {}
        df = df_latency_csv[i]
        if not df.empty:
            df = df.loc[df.index.isin([f"\\10{z:02d}"], level="dstport")]
            df = df.reset_index(level="dstport", drop=True)
            df.to_csv(FIGURES_DIR + 'histlatency-repeat' + str(i) + '-flow' + str(z) + '.csv')
            ms_data = to_microsecond(df)
            hist_data = to_ms_bins(ms_data, round_ms_digits=3)
            normalized_data = normalize(hist_data)
            accumulated_data = accumulate(normalized_data)
            hdr_data = to_hdr(accumulated_data)
            data[f"{z:02d}"] = hdr_data
            plot_hdr(data,
                     str(i) + "flow-" + str(z))  # Plot hdr for each flow individuall, otherwise too much in one figure
            data = {f"{z:02d}": accumulated_data}
            plot_cdf(data, str(i) + "flow-" + str(z))

# Get the list of files to process
for i in range(0, int(repeat)):
    # Move to panda
    df_latency = pd.read_csv(f"{RESULTS_DIR}latencies-pre-repeat{i}.pcap.zst.latency-flows.csv",
                             usecols=["latency", "dstport", "postts"])
    for z in range(1, int(flows) + 1):
        if not df_latency.empty:
            df_jitter = df_latency.loc[df_latency["dstport"] == f"\\10{z:02d}"]
            df_sorted = df_jitter.sort_values(by='postts', ascending=True).reset_index(drop=True)
            jitter_values = df_sorted["latency"].diff().abs()
            jitter_values_hist = jitter_values.value_counts().sort_index()
            jitter_values_hist.to_csv(FIGURES_DIR + 'jitter-repeat' + str(i) + '-flow' + str(z) + '.csv')

# Adapted from Gallenmüller et al. https://gitlab.lrz.de/nokia-university-donation/measurement-script/
# -/tree/suricata/ for processing IRQFiles including all templates:


templates = {}


def check_template_folder():
    """
    Controls the corresponding template folder used throughout the plotting
    :return:
    """
    logging.debug('checking template folder')
    for templ in templateFolder.glob('*.tex'):
        templates[templ.stem] = env.get_template(templ.name)


check_template_folder()


def filter_cpu_num(list_cpu):
    """
    Method to filter CPU numbers
    :param list_cpu: The list of CPUs to be considered
    :return: A sorted list of CPU numbers
    """
    cpu = set()
    for haeufle in list_cpu:
        list_of_cpu = haeufle.split('_')
        core = list_of_cpu[len(list_of_cpu) - 1]
        if re.match(r'CPU\d+', core):
            cpu.add(core)
    return sorted(list(cpu))


def dissect_irq_file(svfile, run):
    """
    Divide the IRQ file to be able for the plotting
    :param svfile: The corresponding file
    :param run: The current information from the RUN
    :return: The dictionary for plotting
    """
    with open(str(svfile), newline='', encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        header = list(next(reader, None))
        if not header:
            return None
        cpu_list = filter_cpu_num(header)
        timestamp_index = header.index('timestamp_us')
        dic = {}
        for cnum in cpu_list:
            dic[cnum] = []
            for index in header:
                if index == 'timestamp_us' or cnum not in index:
                    continue
                dic[cnum].append(templates['rateplot'].render(content=str(svfile), run=run,
                                                              x=str(timestamp_index), xdivisor=str(1000000),
                                                              y=str(header.index(index)), ydivisor=str(1), loop=run,
                                                              legendentry=index.replace('_' + cnum, '').replace('_'
                                                                                                                '',
                                                                                                                '\\_')))
        return dic


def create_irq_plot():
    """
    Function to create Interrupt plots based on the recording
    :return:
    """
    irqs = sorted(list(Path("figures/").glob('*.irq.csv')))
    if len(irqs) == 0:
        logging.warning("no irq csv files found, skipping packetrate plot creation")
        return
    for irq in irqs:
        run = re.findall(r'run\S+', irq.stem)[0].replace('run', '').replace('.irq.csv', '')
        cscheme = templates['color-scheme-nofill'].render()
        dic = dissect_irq_file(irq, run)
        for cpu in dic:
            xlbl = "Measurement time [\\si{\\second}]"
            ylbl = "IRQ [relative]"
            axis = templates['rateaxis'].render(xlabel=xlbl, ylabel=ylbl, plots=dic[cpu])
            docu = templates['standalone'].render(content=axis, colorscheme=cscheme)
            with open(Path("figures/") / ('irq-' + cpu.replace('CPU', 'cpu') + '-run' + run + '.tex'), 'w',
                      encoding="utf-8") as stream:
                stream.write(docu)


create_irq_plot()
