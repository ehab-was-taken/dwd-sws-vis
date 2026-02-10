# %% [markdown]
# # DWD SWS Interactive Dashboard
# 
# This notebook launches the interactive dashboard for DWD Road Weather Stations.

# %%
import sys
import os
from IPython.display import display

# Add src to path if running from notebooks dir and not installed
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..', 'src')))

from dwd_sws import launch

# %% [markdown]
# ## Launch Dashboard
# 
# The following cell will:
# 1. Download/Load the station catalog (Excel).
# 2. Display the map.
# 3. Allow you to select a station, fetch data, and visualize it.

# %%
dashboard = launch()
display(dashboard)

# %%
