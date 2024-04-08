#region imorts
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import PyQt5.QtWidgets as qtw

# importing from previous work on least squares fit
from LeastSquares2 import LeastSquaresFit_Class
#endregion

#region class definitions
class Pump_Model():
    """
    This is the pump model.  It just stores data.
    """
    def __init__(self): #pump class constructor
        #create some class variables for storing information
        self.PumpName = ""
        self.FlowUnits = ""
        self.HeadUnits = ""

        # place to store data from file
        self.FlowData = np.array([])
        self.HeadData = np.array([])
        self.EffData = np.array([])

        # place to store coefficients for cubic fits
        self.HeadCoefficients = np.array([])
        self.EfficiencyCoefficients = np.array([])

        # create two instances (objects) of least squares class
        self.LSFitHead=LeastSquaresFit_Class()
        self.LSFitEff=LeastSquaresFit_Class()


class Pump_Controller():
    def __init__(self):
        self.Model = Pump_Model()
        self.View = Pump_View()

    def ImportFromFile(self, data):
        """
        This processes the list of strings in data to build the pump model
        :param data:
        :return:
        """
        self.Model.PumpName = data[0]  # Assuming the first line is the pump name
        units = data[1].split()  # Assuming the second line contains units
        self.Model.FlowUnits = units[0]
        self.Model.HeadUnits = units[1]

        self.SetData(data[3:])  # Assuming the third line onwards contains the data
        self.updateView()

    def SetData(self, data):

        '''
        Expects three columns of data in an array of strings with space delimiter
        Parse line and build arrays.
        :param data:
        :return:
        '''

        for line in data:
            cells = line.split()  # Split each line into parts
            if len(cells) >= 3:  # Ensure there are at least three columns
                self.Model.FlowData = np.append(self.Model.FlowData, float(cells[0]))
                self.Model.HeadData = np.append(self.Model.HeadData, float(cells[1]))
                self.Model.EffData = np.append(self.Model.EffData, float(cells[2]))

        self.LSFit()

    def LSFit(self):
        self.Model.HeadCoefficients = np.polyfit(self.Model.FlowData, self.Model.HeadData, 3)
        self.Model.EfficiencyCoefficients = np.polyfit(self.Model.FlowData, self.Model.EffData, 3)

        self.Model.LSFitHead.SetCoefficients(self.Model.HeadCoefficients)
        self.Model.LSFitEff.SetCoefficients(self.Model.EfficiencyCoefficients)
        
    def LSFit(self):
        '''Fit cubic polynomial using Least Squares'''
        self.Model.LSFitHead.x=self.Model.FlowData
        self.Model.LSFitHead.y=self.Model.HeadData
        self.Model.LSFitHead.LeastSquares(3) #calls LeastSquares function of LSFitHead object

        self.Model.LSFitEff.x=self.Model.FlowData
        self.Model.LSFitEff.y=self.Model.EffData
        self.Model.LSFitEff.LeastSquares(3) #calls LeastSquares function of LSFitEff object
    #endregion

    #region functions interacting with view
    def setViewWidgets(self, w):
        self.View.setViewWidgets(w)

    def updateView(self):
        self.View.updateView(self.Model)
    #endregion
class Pump_View():
    def __init__(self):
        """
        In this constructor, I create some QWidgets as placeholders until they get defined later.
        """
        self.LE_PumpName=qtw.QLineEdit()
        self.LE_FlowUnits=qtw.QLineEdit()
        self.LE_HeadUnits=qtw.QLineEdit()
        self.LE_HeadCoefs=qtw.QLineEdit()
        self.LE_EffCoefs=qtw.QLineEdit()
        self.ax=None
        self.canvas=None

    def updateView(self, Model):
        """
        Put model parameters in the widgets.
        :param Model:
        :return:
        """
        self.LE_PumpName.setText(Model.PumpName)
        self.LE_FlowUnits.setText(Model.FlowUnits)
        self.LE_HeadUnits.setText(Model.HeadUnits)
        self.LE_HeadCoefs.setText(Model.LSFitHead.GetCoeffsString())
        self.LE_EffCoefs.setText(Model.LSFitEff.GetCoeffsString())
        self.DoPlot(Model)

    def DoPlot(self, Model):
        '''
        had chatgpt write us up the plot configuration to save time
        '''

        if not self.ax or not self.canvas:
            return  # Guard clause if plot components aren't set

        self.ax.clear()  # Clear existing plot

        # Create a secondary y-axis for efficiency
        ax2 = self.ax.twinx()

        # Plot Head Data with black dashed line and circles at each data point (outlined)
        headx, heady, headRSq = Model.LSFitHead.GetPlotInfo(3, npoints=500)
        line1, = self.ax.plot(headx, heady, 'k--',
                              label=f'Head Fit ($R^2={headRSq:.2f}$)')  # Black dashed line for head fit
        line2, = self.ax.plot(Model.FlowData, Model.HeadData, 'ko', fillstyle='none',
                              label='Head')  # Black circles as outlines

        # Plot Efficiency Data with black dotted line and triangles at each data point (outlined)
        effx, effy, effRSq = Model.LSFitEff.GetPlotInfo(3, npoints=500)
        line3, = ax2.plot(effx, effy, 'k:',
                          label=f'Efficiency Fit, $R^2={effRSq:.2f}$')  # Black dotted line for efficiency fit
        line4, = ax2.plot(Model.FlowData, Model.EffData, 'k^', fillstyle='none',
                          label='Efficiency')  # Black triangles as outlines

        # Set labels and title for primary y-axis (Head)
        self.ax.set_xlabel('Flow Rate (gpm)')
        self.ax.set_ylabel('Head (ft)')
        self.ax.tick_params(axis='y')

        # Set label for secondary y-axis (Efficiency)
        ax2.set_ylabel('Efficiency (%)')
        ax2.tick_params(axis='y')

        # Creating two separate legends
        # For the head data, move the legend to the middle left using axes coordinates
        self.ax.legend([line1, line2], [line1.get_label(), line2.get_label()], loc=(0, 0.5))
        ax2.legend([line3, line4], [line3.get_label(), line4.get_label()], loc='upper right')

        self.canvas.draw()
    def setViewWidgets(self, w):
        self.LE_PumpName, self.LE_FlowUnits, self.LE_HeadUnits, self.LE_HeadCoefs, self.LE_EffCoefs, self.ax, self.canvas = w
#endregion

