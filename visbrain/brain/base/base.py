"""This script initialize Brain objects and manage if they are empty.

The following elements are initialized :
    * Atlas : create the main standard MNI brain.
    * Sources : deep points inside / over the brain. They can materialized
    intracranial electrodes, MEG / EEG sensors...
    * Connectivity : straight lines which connect the deep sources.
    * Roi : deep structures can be added (like brodmann areas or gyrus...).
    This can be for processing (like projecting sources activity on it),
    educational or simply for visualiation purpose.
    * Colorbar : initialize the colorbar elements.
    * Projections : set of projections that can be applied on several
    Brain objects (like cortical_projection(), cortical_repartition(...))
    Those transformations are added here, at the top level, so that they
    can have access to the previously defined elements.
"""

from vispy import scene

from .AtlasBase import AtlasBase
from .SourcesBase import SourcesBase
from .ConnectBase import ConnectBase
from .RoiBase import RoiBase
from .projection import Projections


class base(Projections):
    """Initialize Brain objects.

    Initialize sources / connectivity / areas / colorbar / projections.
    Organize them at diffrent levels and make the link with the graphical
    user interface (if no object is detected, the corresponding panel in the
    GUI has to be deactivate).
    """

    def __init__(self, canvas, progressbar, **kwargs):
        """Init."""
        # ---------- Initialize base ----------
        # Get progress bar :
        self.progressbar = progressbar

        # Initialize brain, sources, connectivity and ROI objects :
        self.atlas = AtlasBase(**kwargs)
        self.sources = SourcesBase(**kwargs)
        self.connect = ConnectBase(_xyz=self.sources.xyz,
                                   c_xyz=self.sources.xyz, **kwargs)
        self.area = RoiBase(scale_factor=self.atlas._scaleMax,
                            name='NoneArea', select=None, color='#ab4642')

        # Add projections :
        Projections.__init__(self, **kwargs)
        self._tobj['brain'] = self.atlas

        # ---------- Panel management ----------
        # Some GUI panels are systematically deactivate if there's no
        # corresponding object.

        # Sources panel:
        if self.sources.name is 'NoneSources':
            # Disable menu :
            self.menuDispSources.setChecked(False)
            self.menuDispSources.setEnabled(False)
            self.menuTransform.setEnabled(False)
            # Disable source/connect/cbar tabs :
            self.QuickSettings.setTabEnabled(2, False)
            self.QuickSettings.setTabEnabled(3, False)
            self.QuickSettings.setTabEnabled(5, False)
            # Disable transparency on sources :
            self.o_Sources.setEnabled(False)
            self.o_Sources.setChecked(False)

        # Text panel:
        if self.sources.stextmesh.name == 'NoneText':
            self.o_Text.setEnabled(False)
            self.o_Text.setChecked(False)
            self.grpText.setEnabled(False)

        # Connectivity panel:
        if self.connect.name == 'NoneConnect':
            # Disable menu :
            self.menuDispConnect.setEnabled(False)
            self.menuDispConnect.setChecked(False)
            # Disable Connect tab :
            self.QuickSettings.setTabEnabled(3, False)
            self.o_Connect.setEnabled(False)
            self.o_Connect.setChecked(False)
        elif self.connect.colval is not None:
            self.cmapConnect.setEnabled(False)
            self.o_Connect.setEnabled(False)
        self._lw = kwargs.get('c_linewidth', 4.)

        # ---------- Put everything in a root node ----------
        # Here, each object is put in a root node so that each transformation
        # can be applied to all elements.

        # Create a root node :
        self._vbNode = scene.Node(name='visbrain')

        # Make this root node the parent of others Brain objects :
        self.atlas.mesh.parent = self._vbNode
        self.sources.mesh.parent = self._vbNode
        self.connect.mesh.parent = self._vbNode
        self.sources.stextmesh.parent = self._vbNode

        # Add XYZ axis (debugging : x=red, y=green, z=blue)
        # scene.visuals.XYZAxis(parent=self._vbNode)

        # Add a rescale / translate transformation to the Node :
        self._vbNode.transform = self.atlas.transform
