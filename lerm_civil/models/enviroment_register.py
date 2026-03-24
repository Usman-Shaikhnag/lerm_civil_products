from odoo import models , fields,api


class EnviromentRegister(models.Model):
    _name = 'enviroment.register'    
    atmospheric_pressure = fields.Float("Atmospheric Pressure")
    temp_dry_bulb = fields.Float("Temprature (Dry Bulb)")
    temp_wet_bulb = fields.Float("Temprature (Wet Bulb)")
    relative_hum = fields.Float("Relative Humidity")
    date_time = fields.Datetime("Date and Time")



    
