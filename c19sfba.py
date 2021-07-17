#!/usr/bin/env python
# coding: utf-8

# In[1]:


import requests
import os
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import matplotlib._color_data as mcd
import shutil


# In[2]:


# get population data
# this should rarely be updated, if ever
# https://www.ers.usda.gov/data-products/county-level-data-sets/download-data/
popxl = 'PopulationEstimates.xls'
popurl = 'https://www.ers.usda.gov/webdocs/DataFiles/48747/' + popxl
if not os.path.exists(popxl):
    req = requests.get(popurl)
    with open(popxl, 'wb') as f:
        f.write(req.content)

popdf = pd.read_excel(popxl, sheet_name='Population Estimates 2010-19', usecols=[0, 19, 2, 1], header=2)

# first line is the whole country, don't need it
popdf.drop([0], inplace=True)

# merge names into single columns, set FIPS as index
popdf.rename(columns={'FIPStxt': 'FIPS', 'POP_ESTIMATE_2019': 'pop'}, inplace=True)

popdf.set_index('FIPS', inplace=True)
popdf.index.name = None
#popdf['name'] = popdf['Area_Name'] + ', ' + popdf['State']
popdf['name'] = popdf['Area_Name']
popdf.drop(columns=['State', 'Area_Name'], inplace=True)


# In[3]:


# get COVID-19 data
# this should be updated daily
# https://github.com/CSSEGISandData/COVID-19
tsfile = 'time_series_covid19_confirmed_US.csv'
tsurl = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/' + tsfile
if not os.path.exists(tsfile):
    req = requests.get(tsurl)
    with open(tsfile, 'wb') as f:
        f.write(req.content)

t = pd.read_csv(tsfile)

# no FIPS, no play
t = t[t['FIPS'].notna()].copy(deep=True)


# In[4]:


# keep only FIPS and dates
ts = t[['FIPS'] + list(t.columns[11:])].copy(deep=True)
# FIPS is integer
ts['FIPS'] = ts['FIPS'].astype(int)


# In[5]:


# set FIPS as index
ts.set_index('FIPS', inplace=True)


# In[6]:


# transpose: dates are index, FIPS are columns
df = ts.transpose(copy=True)
# clean the dates header
df.columns.name = None

# In[7]:


def lfill_date(date_in):
  # from M/DD/YY to YYYY/MM/DD
  date_chunks = date_in.split('/')
  date_filled = '20' + date_chunks[2] + '/' + date_chunks[0].rjust(2, '0') + '/' + date_chunks[1].rjust(2, '0')
  return(date_filled)

# smooth the graph
df = df.rolling(21, min_periods=1, center=False, win_type='blackmanharris').mean().copy(deep=True)

# Original data has cumulative numbers - columns increment forever.
# Convert cumulative numbers into daily deltas.
df = df.diff(axis=0).copy(deep=True)
# fill back first row with 0, because diff nuked it into NaN
#df.loc['1/22/20'] = 0
# not much happened before November 2020
df = df.iloc[284:, :]

# there can be no negative deltas
df.clip(lower=0, inplace=True)

# what is the most recent day in the data?
last_day = lfill_date(df.index.tolist()[-1])


# In[8]:


# divide by population
# multiply by 100k
for c in df.columns:
    if c in popdf.index.tolist():
        df[c] = 100000 * df[c] / popdf.loc[c, 'pop']
    else:
        # could not find population for that FIPS, so set numbers to 0
        df[c] = 0


# In[9]:


# massive copy-paste job from another project
# so the code here is more complicated than it needs to be
def make_plots(df, plot_folder, area_unit, unit_colors, data_type, plot_scope, name_dict, do_all):
  max_value = df.values.max()
  N = 12
  last_file = None

  # replace area unit numeric codes with actual names
  # this is for USA counties only
  if isinstance(name_dict, pd.DataFrame):
    for c in df.columns:
      if c not in name_dict.index.tolist():
        # if FIPS codes are not in population data
        # we don't draw represent them on the map anyway
        # so let's delete them from the plots as well
        df.drop(columns=[c], inplace=True)
        continue
      name = name_dict.loc[c, 'name']
      if name.endswith(' County'):
        name = name[:-len(' County')]
      df.rename(columns={c: name}, inplace=True)
      unit_colors[name] = unit_colors.pop(c)

  if do_all:
    day_list = df.index.tolist()
  else:
    day_list = df.index.tolist()[-1:]
  for day in day_list:
    # make it look like YYYY/MM/DD
    daystring = lfill_date(day)
    plot_file = 'frame-' + daystring.replace('/', '') + '.png'
    plot_full_path = os.path.join(plot_folder, plot_file)
    # if the file exists, skip this frame
    if os.path.exists(plot_full_path):
      continue

    plt.rcParams["figure.dpi"] = 192
    fig = plt.figure(figsize=(10, 5.625))
    plt.title('SF Bay Area counties - COVID-19 daily cases up to ' + daystring + ' - per 100k people - smoothed')
    # x ticks get too crowded, limit their number
    plt.gca().xaxis.set_major_locator(plt.MaxNLocator(nbins=7))
    plt.gca().spines['right'].set_visible(False)
    plt.gca().spines['top'].set_visible(False)

    # extract one day from dataframe
    # put area units in one column
    # put values in the other column
    daydf = df.loc[day].to_frame()
    daydf.index.name = area_unit
    daydf.reset_index(inplace=True)
    topN = daydf.sort_values(by=[day], ascending=False).head(N)
    topNunits = topN[area_unit].tolist()
    all_champs = df.loc[:day, topNunits]
    #max_value = all_champs.values.max()
    plt.gca().set_ylim(bottom=0, top=max_value)

    # just extract the x coordinate to draw the bottom zones
    zonemark = df.loc[:day, topNunits[0]].to_frame()
    alldays = zonemark.index.tolist()
    # draw the color zones at the bottom
    bzone = [7 for j in alldays]
    p = plt.plot(zonemark.index.tolist(), bzone, color='lightcoral')
    bzone = [4 for j in alldays]
    p = plt.plot(zonemark.index.tolist(), bzone, color='bisque')
    bzone = [1 for j in alldays]
    p = plt.plot(zonemark.index.tolist(), bzone, color='lightyellow')

    for u in topNunits:
      champ = df.loc[:day, u].to_frame()
      p = plt.plot(champ.index.tolist(), champ[u].tolist(), color=unit_colors[u])
    leg = plt.legend(topNunits, loc='upper left', frameon=False)
    for line, text in zip(leg.get_lines(), leg.get_texts()):
      line.set_color(unit_colors[text.get_text()])

    fig.subplots_adjust(left = 0.07, right = 0.99, bottom = 0.065, top = 0.94)
    fig.savefig(plot_full_path)
    last_file = plot_full_path
    plt.close()

  curr_snap = plot_scope + '_' + data_type + '_top.png'
  curr_snap = curr_snap.replace(' ', '_')
  curr_snap = curr_snap.lower()
  if last_file != None:
    if os.path.exists(curr_snap):
      os.remove(curr_snap)
    shutil.copyfile(last_file, curr_snap)
    shutil.rmtree(plot_folder)


def assign_colors(df):
  colors = {}
  colorPalette = [
      'r',
      'chartreuse',
      'dodgerblue',
      'cyan',
      'magenta',
      'gold',
      'black',
      'silver',
      'firebrick'
  ]
  for unit in df.columns:
    colors[unit] = colorPalette[df.columns.tolist().index(unit) % len(colorPalette)]
  return(colors)


def make_folder_name(prefix, scope, data_type):
  fn = prefix + '_' + scope + '_' + data_type
  fn = fn.replace(' ', '_')
  fn = fn.lower()
  return fn


# In[10]:

bacs = [6041,
       6097,
       6055,
       6095,
       6013,
       6001,
       6085,
       6081,
       6075]

barel = df[bacs].copy(deep=True)

data_type = 'per capita'
plot_scope = 'bay area'
color_ba_rel = assign_colors(barel)
plot_folder = make_folder_name('plot', plot_scope, data_type)
if not os.path.exists(plot_folder):
    os.makedirs(plot_folder)
make_plots(barel, plot_folder, 'counties', color_ba_rel, data_type, plot_scope, popdf, False)


# In[ ]:




