"""Top level Sleep class."""
import numpy as np
import sip

from PyQt4 import QtGui
import sys
import os
from warnings import warn

import vispy.app as visapp
import vispy.scene.cameras as viscam

from .interface import uiInit, uiElements
from .visuals import visuals
from .tools import Tools
from ..utils import (FixedCam, load_sleepdataset, load_hypno, color2vb,
                     ShortcutPopup, check_downsampling)

sip.setdestroyonexit(False)


class Sleep(uiInit, visuals, uiElements, Tools):
    """Visualize and edit sleep data.

    Use this module to :
        - Load .eeg (Brainvision and ELAN), .edf or directly raw data.
        - Visualize data channels, spectrogram and hypnogram
        - Edit hypnogram from the interface
        - Perform a spindle / REM / Peak detection
        - Further signal processing tools (de-mean, de-trend and filtering)
    Sleep has been developped in collaboration with Raphael Vallat.

    Kargs:
        file: string, optional, (def: None)
            Path to the data file (.eeg, .trc or .edf).

        hypno_file: string, optional, (def: None)
            Path to the hypnogram file (.hyp, .txt or .csv)

        data: np.ndarray, optional, (def: None)
            Array of data of shape (n_channels, n_pts)

        channels: list, optional, (def: None)
            List of channel names. The length of this list must be n_channels.

        sf: float, optional, (def: None)
            The sampling frequency of raw data.

        hypno: np.ndarray, optional, (def: None)
            Hypnogram data. Should be a raw vector of shape (n_pts,)

        downsample: float, optional, (def: 100.)
            The downsampling frequency for the data and hypnogram raw data.

        axis: bool, optional, (def: Fals)
            Specify if each axis have to contains its own axis. Be carefull
            with this option, the rendering can be much slower.

        line: string, optional, (def: 'gl')
            Specify the line rendering. Use 'gl' for the default line (fast) or
            'agg' for smooth lines. This option might not works on some
            plateforms.
    """

    def __init__(self, file=None, hypno_file=None, data=None, channels=None,
                 sf=None, hypno=None, downsample=100., axis=False, line='gl'):
        """Init."""
        # ====================== APP CREATION ======================
        # Create the app and initialize all graphical elements :
        self._app = QtGui.QApplication(sys.argv)
        uiInit.__init__(self)

        # Shortcuts popup window :
        self._shpopup = ShortcutPopup()

        # Set default GUI state :
        self.setDefaultState()

        # ====================== LOAD FILE ======================
        # Load file and convert if needed :
        if not all([k is not None for k in [data, channels, sf]]):
            # --------------- Qt Dialog ---------------
            if (file is None) or not isinstance(file, str):
                # Dialog window for the main dataset :
                file = QtGui.QFileDialog.getOpenFileName(
                    self, "Open dataset", "", "BrainVision /Elan (*.eeg);;"
                    "Edf (*.edf);;Micromed (*.trc)")
                file = str(file)  # py2
                # Get the user path :
                upath = os.path.split(file)[0]
                # Dialog window for hypnogram :
                hypno_file = QtGui.QFileDialog.getOpenFileName(
                    self, "Open hypnogram", upath, "Elan (*.hyp);;"
                    "Text file (*.txt);;""CSV file (*.csv);;All files "
                    "(*.*)")
                hypno_file = str(hypno_file)  # py2

            # Load dataset :
            sf, downsample, data, channels, N, start_time = load_sleepdataset(
                file, downsample)
            npts = data.shape[1]
            # Build the time vector :
            time = np.arange(N) / sf
            self._N = N
            self._sfori = sf
            self._toffset = start_time.hour * 3600 + \
                start_time.minute * 60 + start_time.second

            # Load hypnogram :
            if hypno_file:
                # Load the hypnogram :
                hypno = load_hypno(hypno_file, npts)

            # Change the sampling frequency if down-sample :
            if downsample is not None:
                time = time[::int(np.round(sf/downsample))]
                sf = downsample
                downsample = None

        # Data and sf are givin as an input :
        elif (data is not None) and (sf is not None):
            # Check down-sampling :
            downsample = check_downsampling(sf, downsample)
            self._N = data.shape[1]
            self._sfori = sf
            self._toffset = 0
            time = np.arange(self._N) / sf

        # ====================== VARIABLES ======================
        # Check all data :
        self._file = file
        self._sf, self._data, self._hypno, self._time = self._check_data(
            sf, data, channels, hypno, downsample, time)
        self._channels = [k.strip().replace(' ', '').split('.')[
            0] for k in channels]
        self._ax = axis
        # ---------- Default line width ----------
        self._linemeth = line
        self._lw = 1.
        self._lwhyp = 2.5
        self._defwin = 30.
        self._defstd = 5.
        # ---------- Default colors ----------
        self._chancolor = '#292824'
        # self._hypcolor = '#292824'
        # Hypnogram color :
        self._hypcolor = {-1: '#8bbf56', 0: '#56bf8b', 1: '#aabcce',
                          2: '#405c79', 3: '#0b1c2c', 4: '#bf5656'}
        self._indicol = '#e74c3c'
        # Default spectrogram colormap :
        self._defcmap = 'viridis'
        # Spindles / REM / Peaks colors :
        self._defspin = color2vb('#d73737')
        self._defsw = color2vb('#56bf8b')
        self._defkc = color2vb('#b45a3c')
        self._defrem = color2vb('#6684e1')
        self._defmt = color2vb('#FE8625')
        self._defpeaks = '#b854d4'
        # ---------- Symbol ----------
        self._spinsym = 'x'
        self._swsym = 'o'
        self._kcsym = 'diamond'
        self._remsym = 'triangle_down'
        self._mtsym = 'star'
        self._peaksym = 'disc'
        # Get some data info (min / max / std / mean)
        self._get_dataInfo()

        # ====================== USER & GUI INTERACTION  ======================
        # User <-> GUI :
        uiElements.__init__(self)

        # ====================== CAMERAS ======================
        self._camCreation()

        # ====================== OBJECTS CREATION ======================
        visuals.__init__(self)

        # ====================== TOOLS ======================
        Tools.__init__(self)

        # ====================== FUNCTIONS ON LOAD ======================
        self._fcnsOnCreation()

        # ====================== MACHINE LEARNING ======================
        from ..utils.sleep.mlsleep import ml_BuildTrainingSets
        ml_BuildTrainingSets(self._data, self._sf, self._hypno, self._channels)

    def __len__(self):
        """Return the number of channels."""
        return len(self._channels)

    def __getitem__(self, key):
        """Return corresponding data info."""
        return self._datainfo[key]

    ###########################################################################
    # CHECKING
    ###########################################################################
    def _check_data(self, sf, data, channels, hypno=None, downsample=None,
                    time=None):
        """Check data, hypnogram, channels and sample frequency after loading.

        Args:
            sf: float
                The sampling frequency.

            data: np.ndarray
                The data to use. Must be a (n_channels, n_pts) array.

            channel: list
                List of string where each element refer to a channel names.
                The length of this list must be n_channels.

        Kargs:
            hypno: np.ndarray, optional, (def: None)
                A row vector of shape (npts,) containing hypnogram values.
                If the hypnogram is None, this functions returns a row vector
                fill with zeros.

            time: np.ndarray, optional, (def: None)
                The time vector to use. If the time vector is None, it will be
                inferred from data length (be carefull to time consistency).

        Returns:
            sf: float
                The sampling frequency

            data: np.ndarray
                The float 32 data with a shape of (n_channels, n_pts).

            hypno: np.ndarray
                The float 32 hypnogram with a shape of (npts,).

            time: np.ndarray
                The time vector with a shape of (npts,).
        """
        # ========================== CHECKING ==========================
        nchan = len(channels)
        # Check sampling frequency :
        if not isinstance(sf, (int, float)):
            raise ValueError("The sampling frequency must be a float number "
                             "(e.g. 1024., 512., etc)")
        sf = float(sf)
        # Check data shape and format to float32 :
        # data = np.atleast_2d(data)
        if data.ndim is not 2:
            raise ValueError("The data must be a 2D array")
        if data.shape[0] is not nchan:
            warn("Organize data array as (n_channels, n_time_points) is more "
                 "memory efficient")
            data = data.T
        # Get data length :
        npts = data.shape[1]
        # Channels checking :
        if nchan not in data.shape:
            raise ValueError("Incorrect data shape. The number of channels "
                             "("+str(nchan)+') can not be found.')
        # Check hypnogram and format to float32 :
        if hypno is None:
            hypno = np.zeros((npts,), dtype=np.float32)
        else:
            n = len(hypno)
            # Check hypno values :
            if (hypno.min() < -1.) or (hypno.max() > 4) or (n != npts):
                warn("\nHypnogram values must be comprised between -1 and 4 "
                     "(see Iber et al. 2007). Use:\n-1 -> Art (optional)\n 0 "
                     "-> Wake\n 1 -> N1\n 2 -> N2\n 3 -> N4\n 4 -> REM\nEmpty "
                     "hypnogram will be used instead")
                hypno = np.zeros((npts,), dtype=np.float32)
        # Define time vector if needed :
        if time is None:
            time = np.arange(npts, dtype=np.float32) / sf

        # ========================== DOWN-SAMPLING ==========================
        if isinstance(downsample, (int, float)):
            # Find frequency ratio :
            fratio = int(round(sf / downsample))
            # Select time, data and hypno points :
            data = data[:, ::fratio]
            time = time[::fratio]
            hypno = hypno[::fratio]
            # Replace sampling frequency :
            sf = float(downsample)

        # ========================== CONVERSION ==========================
        # Convert data and hypno to be contiguous and float 32 (for vispy):
        if not data.flags['C_CONTIGUOUS']:
            data = np.ascontiguousarray(data, dtype=np.float32)
        if data.dtype != np.float32:
            data = data.astype(np.float32, copy=False)
        if not hypno.flags['C_CONTIGUOUS']:
            hypno = np.ascontiguousarray(hypno, dtype=np.float32)
        if hypno.dtype != np.float32:
            hypno = hypno.astype(np.float32, copy=False)

        return sf, data, hypno, time

    ###########################################################################
    # SUB-FONCTIONS
    ###########################################################################
    def _get_dataInfo(self):
        """Get some info about data (min, max, std, mean, dist)."""
        self._datainfo = {'min': self._data.min(1), 'max': self._data.max(1),
                          'std': self._data.std(1), 'mean': self._data.mean(1),
                          'dist': self._data.max(1) - self._data.min(1)}

    def setDefaultState(self):
        """Set the default window state."""
        # ================= TAB =================
        self.QuickSettings.setCurrentIndex(0)
        self.toolBox.setCurrentIndex(1)
        self.toolBox_2.setCurrentIndex(0)
        self._DetectionTab.setCurrentIndex(0)

        # ================= ICON =================
        pathfile = sys.modules[__name__].__file__.split('sleep.py')[0]
        app_icon = QtGui.QIcon()
        app_icon.addFile(os.path.join(pathfile, 'ico/sleep.svg'))
        self.setWindowIcon(app_icon)

    def _camCreation(self):
        """Create a set of cameras."""
        # ------------------- Channels -------------------
        self._chanCam = []
        for k in range(len(self)):
            self._chanCam.append(FixedCam())  # viscam.PanZoomCamera()
        # ------------------- Spectrogram -------------------
        self._speccam = FixedCam()  # viscam.PanZoomCamera()
        self._specCanvas.set_camera(self._speccam)
        # ------------------- Hypnogram -------------------
        self._hypcam = FixedCam()  # viscam.PanZoomCamera()
        self._hypCanvas.set_camera(self._hypcam)
        # ------------------- Topoplot -------------------
        self._topocam = viscam.PanZoomCamera()
        self._topoCanvas.set_camera(self._topocam)
        # ------------------- Time axis -------------------
        self._timecam = FixedCam()
        self._TimeAxis.set_camera(self._timecam)

        # Keep all cams :
        self._allCams = (self._chanCam, self._speccam, self._hypcam,
                         self._topocam, self._timecam)

    def _fcnsOnCreation(self):
        """Functions that need to be applied on creation."""
        self._fcn_sliderMove()
        self._chanChecks[0].setChecked(True)
        self._hypLabel.setVisible(self._PanHypViz.isChecked())
        self._fcn_chanViz()
        self._fcn_chanSymAmp()
        self._fcn_infoUpdate()
        self._fcn_Hypno2Score()
        # Set objects visible :
        self._SpecW.setVisible(True)
        self._HypW.setVisible(True)
        self._TimeAxisW.setVisible(True)

    def show(self):
        """Display the graphical user interface."""
        # This function has to be placed here (and not in the user.py script)
        self.showMaximized()
        visapp.run()
