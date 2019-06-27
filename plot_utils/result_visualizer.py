"""
Script for restoring results array from .npz dump file generated by CNN training engine

Author: Julian Ding
"""

import os
import argparse
import numpy as np
import plot_utils.plot_utils as plu

CSV_NAME = "log_train.csv"
TASKS = [func for func in dir(plu) if func.startswith('plot')]

def parse_args():
    parser = argparse.ArgumentParser(
        description="Normalizes data from an input HDF5 file and outputs to HDF5 file.")
    parser.add_argument("--input_file", '-in', dest="input_file", type=str, nargs=1,
                        help="path to dataset to visualize", required=True)
    parser.add_argument('--output_path', '-out', dest="output_path", type=str, nargs=1,
                        help="desired output path", required=True)
    parser.add_argument('--tasks', '-do', dest="tasks", type=str, default=TASKS,
                        help="specify plots to dump (available: "+str(TASKS)+")", required=False)
    args = parser.parse_args()
    return args

# Returns a results dictionary
def open_result(path):
    assert os.path.isfile(path), "Provided file ("+path+") does not exist, aborting."
    return np.load(path)

# Dumps an instance of every training-based plot in plot_utils to save_path based on data in result
def dump_training_visuals(train_csv_path, val_csv_path, save_path=''):
    plotted = []
    if os.path.isfile(train_csv_path):
        plu.plot_training([train_csv_path], ['Resnet18'], {'Resnet18': ['red', 'blue']}, downsample_interval=128, legend_loc=(0.8, 0.3), save_path=save_path+"training_log.eps")
        plotted.append('plot_training')
        plu.plot_train_smoothed(train_csv_path, save_path=save_path+"train_log_smoothed.eps")
        plotted.append('plot_train_smoothed')
        if os.path.isfile(val_csv_path):
            plu.plot_learn_hist(train_csv_path, val_csv_path, save_path=save_path+"train_learn_hist.eps")
            plotted.append('plot_learn_hist')
        else:
            print("Could not locate validation log at", val_csv_path)
    else:
        print("Could not locate training log at", train_csv_path)
    
    print ("Dumped performance plots", plotted, "to", save_path)

# Dumps an instance of every validation-based plot in plot_utils to save_path based on data in result
def dump_validation_visuals(result, tasks=TASKS, save_path=''):
    save_path += '' if save_path.endswith('/') else '/'
    if not os.path.isdir(save_path):
        print("Making output directory as ", save_path)
        os.mkdir(save_path)
    
    prediction = result['prediction']
    softmax = result['softmax']
    loss = result['loss']
    accuracy = result['accuracy']
    labels = result['labels']
    energies = result['energies']

    vis_energies = plu.convert_to_visible_energy(energies, labels)
    
    class_names = ['gamma', 'e', 'mu']
    index_dict = {name:index for index, name in enumerate(class_names)}
    
    plotted = []
    # Plotting tasks below:
    if 'plot_event_energy_distribution' in tasks:
        plu.plot_event_energy_distribution(vis_energies, labels, index_dict, save_path=save_path+"energy_distribution.eps")
        plotted.append('plot_event_energy_distribution')
    if 'plot_confusion_matrix' in tasks:
        plu.plot_confusion_matrix(labels, prediction, vis_energies, class_names, 0, np.amax(vis_energies), save_path=save_path+"confusion_matrix.eps")
        plotted.append('plot_confusion_matrix')
    if 'plot_classifier_response' in tasks:
        for i, name in enumerate(class_names):
            plu.plot_classifier_response(softmax, labels, vis_energies, index_dict, {name:i}, save_path=save_path+"classifier_response_"+name+".eps")
        plotted.append('plot_classifier_response')
    if 'plot_ROC_curve_one_vs_one' in tasks:
        for i, name in enumerate(class_names):
            other = class_names[(i+1)%len(class_names)]
            plu.plot_ROC_curve_one_vs_one(softmax, labels, vis_energies, index_dict, name, other, save_path=save_path+name+"_vs_"+other+".eps")
            plu.plot_ROC_curve_one_vs_one(softmax, labels, vis_energies, index_dict, other, name, save_path=save_path+other+"_vs_"+name+".eps")
        plotted.append('plot_ROC_curve_one_vs_one')
    if 'plot_signal_efficiency' in tasks:
        for name, i in index_dict.items():
            other = class_names[(i+1)%len(class_names)]
            plu.plot_signal_efficiency(softmax, labels, vis_energies, index_dict, name, other, save_path=save_path+"signal_efficiency_"+name+".eps")
        plotted.append('plot_signal_efficiency')
    if 'plot_background_rejection' in tasks:
        for name, i in index_dict.items():
            other = class_names[(i+1)%len(class_names)]
            plu.plot_background_rejection(softmax, labels, vis_energies, index_dict, name, other, save_path=save_path+"background_rejection_"+name+".eps")
        plotted.append('plot_background_rejection')

    print ("Dumped performance plots", plotted, "to", save_path)
    
if __name__ == "__main__":
    config = parse_args()
    assert config.tasks in TASKS, "Invalid task(s) specified: "+str([t for t in config.tasks if t not in TASKS])+"\nValid tasks are: "+str(TASKS)
    result = open_result(config.input_file[0])
    dump_validation_visuals(result, tasks=config.tasks, save_path=config.output_path[0])