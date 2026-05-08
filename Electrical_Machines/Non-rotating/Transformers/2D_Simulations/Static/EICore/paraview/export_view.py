# state file generated using paraview version 6.0.1
import paraview
paraview.compatibility.major = 6
paraview.compatibility.minor = 0

#### import the simple module from the paraview
from paraview.simple import *
#### disable automatic camera reset on 'Show'
paraview.simple._DisableFirstRenderCameraReset()

# ----------------------------------------------------------------
# setup views used in the visualization
# ----------------------------------------------------------------

# get the material library
materialLibrary1 = GetMaterialLibrary()

# Create a new 'Render View'
renderView1 = CreateView('RenderView')
renderView1.Set(
    ViewSize=[1452, 808],
    InteractionMode='2D',
    CameraPosition=[0.0, 0.0, 0.4875773033970238],
    CameraFocalDisk=1.0,
    CameraParallelScale=0.07774345826641657,
    OSPRayMaterialLibrary=materialLibrary1,
)

SetActiveView(None)

# ----------------------------------------------------------------
# setup view layouts
# ----------------------------------------------------------------

# create new layout object 'Layout #1'
layout1 = CreateLayout(name='Layout #1')
layout1.AssignView(0, renderView1)
layout1.SetSize(1452, 808)

# ----------------------------------------------------------------
# restore active view
SetActiveView(renderView1)
# ----------------------------------------------------------------

# ----------------------------------------------------------------
# setup the data processing pipelines
# ----------------------------------------------------------------

# create a new 'PVD Reader'
resultspvd = PVDReader(registrationName='results.pvd', FileName='/home/thales/Documentos/git/Elmer-Examples/Electrical_Machines/Static/Transformers/2D_Simulations/EICore/sim/result/paraview/results.pvd')
resultspvd.Set(
    CellArrays=['magnetic flux density e', 'magnetic field strength e', 'current density e'],
    PointArrays=['potential', 'magnetic flux density', 'magnetic field strength', 'current density'],
)

# create a new 'Extract Block'
coilB = ExtractBlock(registrationName='Coil B', Input=resultspvd)
coilB.Set(
    Assembly='Hierarchy',
    Selectors=['/Root/Block4', '/Root/Block5'],
)

# create a new 'Extract Block'
coilA = ExtractBlock(registrationName='Coil A', Input=resultspvd)
coilA.Set(
    Assembly='Hierarchy',
    Selectors=['/Root/Block2', '/Root/Block3'],
)

# create a new 'Extract Block'
ao = ExtractBlock(registrationName='Aço', Input=resultspvd)
ao.Set(
    Assembly='Hierarchy',
    Selectors=['/Root/Block1'],
)

# create a new 'Contour'
contour1 = Contour(registrationName='Contour1', Input=ao)
contour1.Set(
    ContourBy=['POINTS', 'potential'],
    Isosurfaces=[-0.049812152706779994, -0.0387428149485991, -0.02767347719041821, -0.01660413943223732, -0.005534801674056428, 0.005534536084124464, 0.016603873842305356, 0.027673211600486247, 0.03874254935866714, 0.04981188711684803],
)

# create a new 'Cell Data to Point Data'
fluxDensity = CellDatatoPointData(registrationName='Flux Density', Input=ao)

# ----------------------------------------------------------------
# setup the visualization in view 'renderView1'
# ----------------------------------------------------------------

# show data from fluxDensity
fluxDensityDisplay = Show(fluxDensity, renderView1, 'UnstructuredGridRepresentation')

# get color transfer function/color map for 'magneticfluxdensitye'
magneticfluxdensityeLUT = GetColorTransferFunction('magneticfluxdensitye')
magneticfluxdensityeLUT.Set(
    RGBPoints=GenerateRGBPoints(
        range_min=0.0,
        range_max=1.6,
    ),
    ScalarRangeInitialized=1.0,
)

# trace defaults for the display properties.
fluxDensityDisplay.Set(
    Representation='Surface',
    ColorArrayName=['POINTS', 'magnetic flux density e'],
    LookupTable=magneticfluxdensityeLUT,
    Assembly='Hierarchy',
)

# init the 'Piecewise Function' selected for 'ScaleTransferFunction'
fluxDensityDisplay.ScaleTransferFunction.Points = [0.0, 0.0, 0.5, 0.0, 1.1757813367477812e-38, 1.0, 0.5, 0.0]

# init the 'Piecewise Function' selected for 'OpacityTransferFunction'
fluxDensityDisplay.OpacityTransferFunction.Points = [0.0, 0.0, 0.5, 0.0, 1.1757813367477812e-38, 1.0, 0.5, 0.0]

# show data from contour1
contour1Display = Show(contour1, renderView1, 'GeometryRepresentation')

# trace defaults for the display properties.
contour1Display.Set(
    Representation='Surface',
    ColorArrayName=['POINTS', ''],
    Opacity=0.1,
    LineWidth=1.5,
    RenderLinesAsTubes=1,
    Assembly='Hierarchy',
)

# init the 'Piecewise Function' selected for 'ScaleTransferFunction'
contour1Display.ScaleTransferFunction.Points = [30783.00375898231, 0.0, 0.5, 0.0, 30787.00390625, 1.0, 0.5, 0.0]

# init the 'Piecewise Function' selected for 'OpacityTransferFunction'
contour1Display.OpacityTransferFunction.Points = [30783.00375898231, 0.0, 0.5, 0.0, 30787.00390625, 1.0, 0.5, 0.0]

# show data from coilA
coilADisplay = Show(coilA, renderView1, 'UnstructuredGridRepresentation')

# get color transfer function/color map for 'currentdensitye'
currentdensityeLUT = GetColorTransferFunction('currentdensitye')
currentdensityeLUT.Set(
    RGBPoints=GenerateRGBPoints(
        range_min=0.0,
        range_max=93901.7109375,
    ),
    ScalarRangeInitialized=1.0,
)

# trace defaults for the display properties.
coilADisplay.Set(
    Representation='Surface',
    ColorArrayName=['CELLS', 'current density e'],
    LookupTable=currentdensityeLUT,
    Assembly='Hierarchy',
)

# init the 'Piecewise Function' selected for 'ScaleTransferFunction'
coilADisplay.ScaleTransferFunction.Points = [0.0, 0.0, 0.5, 0.0, 1.1757813367477812e-38, 1.0, 0.5, 0.0]

# init the 'Piecewise Function' selected for 'OpacityTransferFunction'
coilADisplay.OpacityTransferFunction.Points = [0.0, 0.0, 0.5, 0.0, 1.1757813367477812e-38, 1.0, 0.5, 0.0]

# show data from coilB
coilBDisplay = Show(coilB, renderView1, 'UnstructuredGridRepresentation')

# trace defaults for the display properties.
coilBDisplay.Set(
    Representation='Surface',
    ColorArrayName=['CELLS', 'current density e'],
    LookupTable=currentdensityeLUT,
    Assembly='Hierarchy',
)

# init the 'Piecewise Function' selected for 'ScaleTransferFunction'
coilBDisplay.ScaleTransferFunction.Points = [0.0, 0.0, 0.5, 0.0, 1.1757813367477812e-38, 1.0, 0.5, 0.0]

# init the 'Piecewise Function' selected for 'OpacityTransferFunction'
coilBDisplay.OpacityTransferFunction.Points = [0.0, 0.0, 0.5, 0.0, 1.1757813367477812e-38, 1.0, 0.5, 0.0]

# setup the color legend parameters for each legend in this view

# get color legend/bar for magneticfluxdensityeLUT in view renderView1
magneticfluxdensityeLUTColorBar = GetScalarBar(magneticfluxdensityeLUT, renderView1)
magneticfluxdensityeLUTColorBar.Set(
    Title='magnetic flux density e',
    ComponentTitle='Magnitude',
    RangeLabelFormat='%.1f',
)

# set color bar visibility
magneticfluxdensityeLUTColorBar.Visibility = 1

# show color legend
fluxDensityDisplay.SetScalarBarVisibility(renderView1, True)

# ----------------------------------------------------------------
# setup color maps and opacity maps used in the visualization
# note: the Get..() functions create a new object, if needed
# ----------------------------------------------------------------

# get opacity transfer function/opacity map for 'currentdensitye'
currentdensityePWF = GetOpacityTransferFunction('currentdensitye')
currentdensityePWF.Set(
    Points=[0.0, 0.0, 0.5, 0.0, 93901.7109375, 1.0, 0.5, 0.0],
    ScalarRangeInitialized=1,
)

# get opacity transfer function/opacity map for 'magneticfluxdensitye'
magneticfluxdensityePWF = GetOpacityTransferFunction('magneticfluxdensitye')
magneticfluxdensityePWF.Set(
    Points=[0.0, 0.0, 0.5, 0.0, 1.6, 1.0, 0.5, 0.0],
    ScalarRangeInitialized=1,
)

# ----------------------------------------------------------------
# setup animation scene, tracks and keyframes
# note: the Get..() functions create a new object, if needed
# ----------------------------------------------------------------

# get time animation track
timeAnimationCue1 = GetTimeTrack()

# initialize the animation scene

# get the time-keeper
timeKeeper1 = GetTimeKeeper()

# initialize the timekeeper

# initialize the animation track

# get animation scene
animationScene1 = GetAnimationScene()

# initialize the animation scene
animationScene1.Set(
    ViewModules=renderView1,
    Cues=timeAnimationCue1,
    AnimationTime=1.0,
    StartTime=1.0,
    EndTime=2.0,
    PlayMode='Snap To TimeSteps',
)

# ----------------------------------------------------------------
# restore active source
SetActiveSource(coilA)
# ----------------------------------------------------------------


##--------------------------------------------
## You may need to add some code at the end of this python script depending on your usage, eg:
#
## Render all views to see them appears
# RenderAllViews()
#
## Interact with the view, usefull when running from pvpython
# Interact()
#
## Save a screenshot of the active view
# SaveScreenshot("path/to/screenshot.png")
#
## Save a screenshot of a layout (multiple splitted view)
# SaveScreenshot("path/to/screenshot.png", GetLayout())
#
## Save all "Extractors" from the pipeline browser
# SaveExtracts()
#
## Save a animation of the current active view
# SaveAnimation()
#
## Please refer to the documentation of paraview.simple
## https://www.paraview.org/paraview-docs/nightly/python/
##--------------------------------------------