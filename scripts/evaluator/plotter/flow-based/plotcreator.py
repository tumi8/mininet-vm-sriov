"""
Generates the plots as Tex file as needed for general plots
"""
from pathlib import Path
import re
import argparse
import csv
import logging
import os
from jinja2 import Environment, FileSystemLoader

# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("figures_folder", help="location of the figures folder")
parser.add_argument("measurement_folder", help="location of the folder containing the processed csv files")
parser.add_argument("result_folder", help="location of the original results (containing *.loop files)")
parser.add_argument("-v", "--verbose",  help="print debug output", action="store_true")
args = parser.parse_args()

# configure logging
if args.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.WARNING)

# read folder paths
figuresFolder = Path(args.figures_folder)
measurementFolder = Path(args.measurement_folder)
resultFolder = Path(args.result_folder)
templateFolder = Path('./template')

env = Environment(loader=FileSystemLoader(templateFolder))


def check_figures_folder():
    """
    Controls the figure folder and represents the loading of it
    :return:
    """
    logging.debug('checking figures folder')
    logging.debug(figuresFolder)


check_figures_folder()

templates = {}


def check_template_folder():
    """
    Controls the template folder and build a base of all templates for furth usage
    :return:
    """
    logging.debug('checking template folder')
    for templ in templateFolder.glob('*.tex'):
        templates[templ.stem] = env.get_template(templ.name)


check_template_folder()


def create_histograms():
    """
    Create default histograms for the presented data
    :return:
    """
    histo_files = sorted(list(measurementFolder.glob('*.hist.csv')))
    if len(histo_files) == 0:
        logging.warning("no histogram files found, skipping histogram creation")
        return
    for hist in histo_files:
        run = str(os.path.basename(hist))
        cscheme = templates['color-scheme-fill'].render()
        plot = templates['histogramplot'].render(content=str(hist), run=run, loop="Not known")
        axis = templates['histogramaxis'].render(content=plot)
        doc = templates['standalone'].render(content=axis, colorscheme=cscheme)
        logging.debug(figuresFolder)
        with open(figuresFolder / ('histogram-' + run + '.tex'), 'w', encoding="utf-8") as stream:
            logging.debug(figuresFolder / ('histogram-' + run + '.tex'))
            stream.write(doc)


create_histograms()


def create_jitter_histograms():
    """
    Create histograms from the data presenting the evaluated jitter
    :return:
    """
    histo_files = sorted(list(measurementFolder.glob('*.jitterpre.csv')))
    histo_files += sorted(list(measurementFolder.glob('*.jitterpost.csv')))
    if len(histo_files) == 0:
        logging.warning("no jitter files found, skipping jitter histogram creation")
        return
    for hist in histo_files:
        run = str(os.path.basename(hist))
        cscheme = templates['color-scheme-fill'].render()
        plot = templates['histogramplot'].render(content=str(hist), run=run, loop="Not Known")
        axis = templates['histogramaxis'].render(content=plot)
        doc = templates['standalone'].render(content=axis, colorscheme=cscheme)
        logging.debug(figuresFolder)
        with open(figuresFolder / ('histogram-' + run + '.tex'), 'w', encoding="utf-8") as stream:
            logging.debug(figuresFolder / ('histogram-' + run + '.tex'))
            stream.write(doc)


create_jitter_histograms()


def create_hdr_histograms():
    """
    create HDR histograms for all presented data
    :return:
    """
    histo_files = sorted(list(measurementFolder.glob('*.percentiles.csv')))
    if len(histo_files) == 0:
        logging.warning("no percentiles files found, skipping hdr-histogram creation")
        return
    for hist in histo_files:
        run = str(os.path.basename(hist))
        cscheme = templates['color-scheme-nofill'].render()
        plot = templates['hdr-histogramplot'].render(content=str(hist), run=run, loop="Not Known")
        axis = templates['hdr-histogramaxis'].render(content=plot)
        doc = templates['standalone'].render(content=axis, colorscheme=cscheme)
        with open(figuresFolder / ('hdr-histogram-' + run + '.tex'), 'w', encoding="utf-8") as stream:
            logging.debug(figuresFolder / ('hdr-histogram-' + run + '.tex'))
            stream.write(doc)


create_hdr_histograms()


def create_worst_of():
    """
    Creates the tex file to build worst case timeseries
    :return:
    """
    worst_of = sorted(list(measurementFolder.glob('*.worst.csv')))
    if len(worst_of) == 0:
        logging.warning("no worst files found, skipping worst-of-timeseries creation")
        return
    for worst in worst_of:
        run = str(os.path.basename(worst))
        cscheme = templates['color-scheme-mark'].render()
        plot = templates['scatterplot'].render(content=str(worst), run=run, loop="Not Known")
        axis = templates['scatteraxis'].render(content=plot)
        doc = templates['standalone'].render(content=axis, colorscheme=cscheme)
        with open(figuresFolder / ('worstof-timeseries-' + run + '.tex'), 'w', encoding="utf-8") as stream:
            logging.debug(figuresFolder / ('worstof-timeseries-' + run + '.tex'))
            stream.write(doc)


create_worst_of()


def create_packet_rate():
    """
    Create the packet rate tex file to build the figure
    :return:
    """
    packet_rates_pre = sorted(list(measurementFolder.glob('*.packetratepre.csv')))
    if len(packet_rates_pre) == 0:
        logging.warning("no packetrate files found, skipping packetrate plot creation")
        return
    for rate_pre in packet_rates_pre:
        run = str(os.path.basename(rate_pre))
        rate_post = str(rate_pre).replace('packetratepre', 'packetratepost')
        cscheme = templates['color-scheme-mark'].render()
        plot = [
            templates['rateplot'].render(content=str(rate_pre), run=run, x=str(0), xdivisor=str(1000000000), y=str(1),
                                         ydivisor=str(1000), loop="Not Known", legendentry='Pre'),
            templates['rateplot'].render(content=str(rate_post), run=run, x=str(0), xdivisor=str(1000000000), y=str(1),
                                         ydivisor=str(1000), loop="Not Known", legendentry='Post')]
        xlbl = "Measurement time [\\si{\\second}]"
        ylbl = "Packet rate [\\si{\\kilo pkt\\per\\second}]"
        axis = templates['rateaxis'].render(xlabel=xlbl, ylabel=ylbl, plots=plot)
        doc = templates['standalone'].render(content=axis, colorscheme=cscheme)
        with open(figuresFolder / ('packetrate-' + run + '.tex'), 'w', encoding="utf-8") as stream:
            logging.debug(figuresFolder / ('packetrate-' + run + '.tex'))
            stream.write(doc)


create_packet_rate()


def filter_cpunum(liste):
    """
    Filter the cpus based on the submitted list
    :param liste: The list of cpu ranges
    :return: A sorted list of CPUs
    """
    cpu = set()
    for haeufle in liste:
        core_list = haeufle.split('_')
        core = core_list[len(core_list) - 1]
        if re.match(r'CPU\d+', core):
            cpu.add(core)
    return sorted(list(cpu))


def dissect_irq_files(svfile, run):
    """
    Prepare the irq files for the plotting
    :param svfile: The file
    :param run: The run information from pos
    :return: The dictionary based on the results
    """
    with open(str(svfile), newline='', encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        header = list(next(reader, None))
        if not header:
            return None
        cpu_list = filter_cpunum(header)
        timestamp_index = header.index('timestamp_us')
        dic = {}
        for cnum in cpu_list:
            dic[cnum] = []
            for i in header:
                if i == 'timestamp_us' or not i.endswith(cnum):
                    continue

                dic[cnum].append(templates['rateplot'].render(content=str(svfile), run=run, x=str(timestamp_index),
                                                              xdivisor=str(1000000), y=str(header.index(i)),
                                                              ydivisor=str(1), loop=run,
                                                              legendentry=i.replace(''
                                                                                    '_' + cnum, '')\
                                                              .replace('_', '\\_')))
        return dic


def create_irq_plot():
    """
    Creates the interrupts plots based on the recording
    :return:
    """
    irqs = sorted(list(measurementFolder.glob('*.irq.csv')))
    if len(irqs) == 0:
        logging.warning("no irq csv files found, skipping packetrate plot creation")
        return
    for irq in irqs:
        run = str(irq)
        cscheme = templates['color-scheme-nofill'].render()
        dic = dissect_irq_files(irq, run)
        for cpu in dic:
            xlbl = "Measurement time [\\si{\\second}]"
            ylbl = "IRQ [relative]"
            axis = templates['rateaxis'].render(xlabel=xlbl, ylabel=ylbl, plots=dic[cpu])
            doc = templates['standalone'].render(content=axis, colorscheme=cscheme)
            with open(figuresFolder / ('irq-' + cpu.replace('CPU', 'cpu') + '-run' + run + '.tex'), 'w',
                      encoding="utf-8") as stream:
                stream.write(doc)


create_irq_plot()
