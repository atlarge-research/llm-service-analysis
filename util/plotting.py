import matplotlib.pyplot as plt

def set_two_column_figure_font(height_multiplier=1.0):
    set_default_figure_font()
    plt.rcParams['font.size'] = 30
    plt.rcParams['axes.labelsize'] = 30
    plt.rcParams['xtick.labelsize'] = 28
    plt.rcParams['ytick.labelsize'] = 28
    plt.rcParams['legend.fontsize'] = 28
    plt.rcParams['figure.figsize'] = (24, round(6 * height_multiplier))

def set_one_column_figure_font(height_multiplier=1.0):
    set_default_figure_font()
    plt.rcParams['font.size'] = 20
    plt.rcParams['axes.labelsize'] = 20
    plt.rcParams['xtick.labelsize'] = 18
    plt.rcParams['ytick.labelsize'] = 18
    plt.rcParams['legend.fontsize'] = 18
    plt.rcParams['figure.figsize'] = (9, round(6 * height_multiplier))

def set_half_column_figure_font(height_multiplier=1.0):
    set_default_figure_font()
    plt.rcParams['font.size'] = 26
    plt.rcParams['axes.labelsize'] = 26
    plt.rcParams['xtick.labelsize'] = 24
    plt.rcParams['ytick.labelsize'] = 24
    plt.rcParams['legend.fontsize'] = 24
    plt.rcParams['figure.figsize'] = (9, round(6 * height_multiplier))
    
def set_default_figure_font():
    plt.rcdefaults()
    plt.rcParams['font.weight'] = 'bold'
    plt.rcParams["axes.labelweight"] = "bold"
    plt.rcParams['text.usetex'] = True
    plt.rcParams['text.latex.preamble'] = r'\boldmath'
    plt.rcParams['font.family'] = 'libertine'
