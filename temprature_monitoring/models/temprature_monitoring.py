from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta
import math
import re
import matplotlib.pyplot as plt
import io
import base64
import matplotlib.ticker as ticker
import numpy as np
import math
from scipy.interpolate import CubicSpline , interp1d , Akima1DInterpolator
from scipy.optimize import minimize_scalar
from io import BytesIO
from scipy.interpolate import make_interp_spline
from odoo.exceptions import UserError
import openpyxl

class TemperatureMonitoring(models.Model):
    _name = 'temperature.monitoring.react'
    _inherit = "lerm.eln" 

    _rec_name = "name"

    name = fields.Char("Name",default="Temperature Monitoring")
    columns_data = fields.Json(string="Columns", default=list)
    rows_data = fields.Json(string="Rows", default=list)
    graph1 = fields.Binary()
    graph2 = fields.Binary()




