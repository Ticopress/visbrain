"""GUI interactions with the contextual menu."""
import os
from PyQt5 import QtWidgets
import vispy.scene.cameras as viscam

from ....io import write_fig_canvas, dialogSave, write_fig_pyqt

__all__ = ['uiMenu']


class uiMenu(object):
    """Interactions with the menu."""

    def __init__(self):
        """Init."""
        # =============================================================
        # FILE
        # =============================================================
        # ----------- SAVE -----------
        # Screenshots :
        self.menuSaveScreenCan.triggered.connect(self._fcn_screenshotCan)
        self.menuSaveScreenWin.triggered.connect(self._fcn_screenshotWin)
        # Config :
        self.menuSaveGuiConfig.triggered.connect(self._fcn_saveConfig)
        # ----------- LOAD -----------
        # Config :
        self.menuLoadGuiConfig.triggered.connect(self._fcn_loadConfig)
        # Exit :
        self.actionExit.triggered.connect(QtWidgets.qApp.quit)

        # =============================================================
        # DISPLAY
        # =============================================================
        # Quick settings panel :
        self.menuDispQuickSettings.triggered.connect(self._fcn_menuDispSet)
        # Brain :
        self.menuDispBrain.triggered.connect(self._fcn_menuBrain)
        # Sources :
        self.menuDispSources.triggered.connect(self._fcn_menuSources)
        # Connectivity :
        self.menuDispConnect.triggered.connect(self._fcn_menuConnect)
        # ROI :
        self.menuDispROI.triggered.connect(self._fcn_menuROI)
        # Colorbar :
        self.menuDispCbar.triggered.connect(self._fcn_menuCbar)

        # =============================================================
        # ROTATION
        # =============================================================
        self.menuRotTop.triggered.connect(self._fcn_rotateTop)
        self.menuRotBottom.triggered.connect(self._fcn_rotateBottom)
        self.menuRotLeft.triggered.connect(self._fcn_rotateLeft)
        self.menuRotRight.triggered.connect(self._fcn_rotateRight)
        self.menuRotFront.triggered.connect(self._fcn_rotateFront)
        self.menuRotBack.triggered.connect(self._fcn_rotateBack)

        # =============================================================
        # CAMERA
        # =============================================================
        self.menuCamFly.triggered.connect(self._fcn_setCamFly)

        # =============================================================
        # PROJECTIONS
        # =============================================================
        self.menuCortProj.triggered.connect(self._fcn_menuProjection)
        self.menuCortRep.triggered.connect(self._fcn_menuRepartition)

    def _fcn_screenshotCan(self):
        """Screenshot using the GUI.

        This function need that a savename is already defined (otherwise, a
        window appeared so that the user specify the path/name).
        """
        # Manage filename :
        if isinstance(self._savename, str):
            cond = self._savename.split('.')[0] == ''
        if (self._savename is None) or cond:
            saveas = dialogSave(self, 'Export the figure', 'brain',
                                "PNG file (*.png);;JPG file(*.jpg);;TIFF file"
                                " (*.tiff);;All files (*.*)")
            self._autocrop = True
        else:
            saveas = self._savename

        # Get filename and extension :
        file, ext = os.path.splitext(saveas)
        if not ext:
            raise ValueError("No extension detected in "+saveas)

        # Export the main canvas :
        write_fig_canvas(saveas, self.view.canvas, resolution=self._uirez,
                         autocrop=self._autocrop, region=self._crop)

        # Export the colorbar :
        if self._cbarexport:
            # Display colorbar :
            self.cbpanelW.setVisible(True)

            # Colorbar file name : filename_colorbar.extension
            saveas = saveas.replace('.', '_colorbar.')

            # Export the colorbar canvas :
            write_fig_canvas(saveas, self.cbqt.cbviz._canvas,
                             region=None, autocrop=self._autocrop,
                             resolution=1000)

    def _fcn_screenshotWin(self):
        """Take a screenshot of the entire window."""
        # Get filename :
        filename = dialogSave(self, 'Screenshot', 'screenshot', "PNG (*.PNG);;"
                              "TIFF (*.tiff);;JPG (*.jpg);;""All files (*.*)")
        # Screnshot function :
        write_fig_pyqt(self, filename)

    ###########################################################################
    #                                DISPLAY
    ###########################################################################
    def _fcn_menuDispSet(self):
        """Toggle method for display / hide the settings panel."""
        viz = self.menuDispQuickSettings.isChecked()
        self.q_widget.setVisible(viz)

    def _fcn_menuBrain(self):
        """Display/hide the main Brain."""
        viz = self.menuDispBrain.isChecked()
        self.atlas.mesh.visible = viz
        self.QuickSettings.setTabEnabled(1, viz)
        self.o_Brain.setEnabled(viz)
        self.o_Brain.setChecked(viz)

    def _fcn_menuSources(self):
        """Display/hide sources."""
        inn = self.sources.mesh.name != 'NoneSources'
        viz = self.menuDispSources.isChecked() and inn
        self.sources.mesh.visible = viz
        self.sources.stextmesh.visible = viz
        self.q_stextshow.setChecked(viz)
        self.toolBox.setEnabled(viz)
        self.toolBox.setEnabled(viz)
        self.groupBox_6.setEnabled(viz)
        self.o_Sources.setEnabled(viz)
        self.o_Sources.setChecked(viz)
        self.o_Text.setEnabled(viz)
        self.o_Text.setChecked(viz)

    def _fcn_menuConnect(self):
        """Display/hide connectivity."""
        inn = self.connect.mesh.name != 'NoneConnect'
        viz = self.menuDispConnect.isChecked() and inn
        self.connect.mesh.visible = viz
        self.toolBox_5.setEnabled(viz)
        self.toolBox_6.setEnabled(viz)
        self.o_Connect.setEnabled(viz)
        self.o_Connect.setChecked(viz)

    def _fcn_menuROI(self):
        """Display/hide ROI."""
        self.area.mesh.visible = self.menuDispROI.isChecked()

    def _fcn_menuCbar(self):
        """Display/hide the colorbar."""
        viz = self.menuDispCbar.isChecked()
        self.QuickSettings.setTabEnabled(5, viz)
        self.cbpanelW.setVisible(viz)

    ###########################################################################
    #                                ROTATION
    ###########################################################################
    def _fcn_rotateTop(self):
        """Display top scene."""
        self._rotate('axial_0')

    def _fcn_rotateBottom(self):
        """Display bottom scene."""
        self._rotate('axial_1')

    def _fcn_rotateLeft(self):
        """Display left scene."""
        self._rotate('sagittal_0')

    def _fcn_rotateRight(self):
        """Display ritgh scene."""
        self._rotate('sagittal_1')

    def _fcn_rotateFront(self):
        """Display front scene."""
        self._rotate('coronal_0')

    def _fcn_rotateBack(self):
        """Display back scene."""
        self._rotate('coronal_1')

    ###########################################################################
    #                                CAMERA
    ###########################################################################
    def _fcn_setCamFly(self):
        """Switch between different types of cameras.

        The user can either use a Turntable or a Fly camera. The turntable
        camera is centered on the central object. Every rotation is arround
        this object. The fly camera can be used for go in every deep part of
        the brain (not easy to control).
        """
        # Get radio buttons values :
        if self.menuCamFly.isChecked():
            # camera = viscam.PanZoomCamera(aspect=1)
            camera = viscam.FlyCamera(name='fly')
        else:
            camera = viscam.TurntableCamera(azimuth=0, distance=1000,
                                            name='turntable')

        # Add camera to the mesh and to the canvas :
        self.view.wc.camera = camera
        self.atlas.mesh.set_camera(camera)
        if self.area.name == 'displayed':
            self.area.mesh.set_camera(camera)
        self.view.wc.update()
        if camera.name == 'turntable':
            self._rotate(fixed='axial_0')

    ###########################################################################
    #                           PROJECTIONS
    ###########################################################################
    def _fcn_menuProjection(self):
        """Run the cortical projection."""
        self._tprojectas = 'activity'
        self._sourcesProjection()

    def _fcn_menuRepartition(self):
        """Run the cortical projection."""
        self._tprojectas = 'repartition'
        self._sourcesProjection()