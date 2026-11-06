# ----------------------------
#       PART 1: Prepare the sample and define the observable
# ----------------------------
# Momentum is in GeV/c. Each particle contributes one entry.

# %%
# cell 1: Create a four-event RDF for the example.
# input: Synthetic momenta.
# output: frame with a vector of momenta per event.
import ROOT

ROOT.gInterpreter.Declare('#include "ROOT/RVec.hxx"')
frame = ROOT.RDataFrame(4).Define('p', 'ROOT::RVecD{0.1 * (rdfentry_ + 1), 0.3}')

# %%
# cell 2: Square each particle's momentum inside RDF.
# input: frame.p in GeV/c.
# output: frame.p2 in (GeV/c)^2.
frame = frame.Define('p2', 'p * p')

# ----------------------------
#       PART 2: Check and display the momentum histogram
# ----------------------------
# Show the histogram inline.

# %%
# cell 3: Fill and check the particle histogram.
# input: frame.p2.
# output: spectrum and its entry count.
from datafactory.hist import HistStaff

model    = ('h_p2', '', 20, 0., 0.2)  # (GeV/c)^2
spectrum = HistStaff(name='p2', histogram=frame.Histo1D(model, 'p2'))
assert spectrum.histogram.GetEntries() == 8

# %%
# cell 4: Display the completed momentum histogram.
# input: spectrum.
# output: Momentum-squared distribution.
import matplotlib.pyplot as plt

_, counts, _, edges = spectrum.get_numpy()
fig, ax             = plt.subplots()
ax.stairs(counts, edges)
ax.set(xlabel=r'$p^2\;[(\mathrm{GeV}/c)^2]$', ylabel='Particles / bin')
plt.show()
