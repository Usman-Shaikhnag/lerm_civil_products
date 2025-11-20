from odoo import api, fields, models


class MechanicalBricks(models.Model):
    _name = "mechanical.bricks"
    # _description = "Mechanical Bricks"
    _inherit = "lerm.eln"
    _description = 'mechanical.bricks'
    _rec_name = "name"

    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
   
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")

    name = fields.Char(string="Name", default="Fly Ash Bricks")

    def prefill_data(self):
        # import wdb; wdb.set_trace()
        return {
            'name': 'Prefill Data',
            'type': 'ir.actions.act_window',
            'res_model': 'brick.prefill.data',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.eln_ref.sample_id.material_id.id,
                'exclude_sample_id': self.eln_ref.sample_id.id,
                },
        }
    


   # Compressive Strength
    compressive_strength_name = fields.Char("Name",default=" Compressive Strength")
    compressive_strength_visible = fields.Boolean("Compressive Strength",compute="_compute_visible")

    temp_compressive_strength = fields.Char("Temp °c")
    humidity_compressive_strength = fields.Char("Humidity %")

    compressive_strength_child_lines = fields.One2many('mechanical.bricks.compressive.line','parent_id',string="Compressive Strength Test" )

    
    avg_compressive_strength = fields.Float(string="Average Compressive Strength ",compute="_compute_avg_compressive_strength")

    @api.depends('compressive_strength_child_lines.compressive_strength')
    def _compute_avg_compressive_strength(self):
        for record in self:
            if record.compressive_strength_child_lines:
              record.avg_compressive_strength = sum(record.compressive_strength_child_lines.mapped('compressive_strength'))/ len(record.compressive_strength_child_lines)
            else:
                record.avg_compressive_strength = 0.0

    avg_compressive_strength_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_avg_compressive_strength_conformity", store=True)

    @api.depends('avg_compressive_strength','eln_ref','grade')
    def _compute_avg_compressive_strength_conformity(self):
        
        for record in self:
            record.avg_compressive_strength_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','31478fghht-9287-48c7-a607-bf1b64a8115d')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','31478fghht-9287-48c7-a607-bf1b64a8115d')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_compressive_strength - record.avg_compressive_strength*mu_value
                    upper = record.avg_compressive_strength + record.avg_compressive_strength*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_compressive_strength_conformity = 'pass'
                        break
                    else:
                        record.avg_compressive_strength_conformity = 'fail'

    avg_compressive_strength_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_compressive_strength_nabl", store=True)

    @api.depends('avg_compressive_strength','eln_ref','grade')
    def _compute_avg_compressive_strength_nabl(self):
        
        for record in self:
            record.avg_compressive_strength_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','31478fghht-9287-48c7-a607-bf1b64a8115d')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','31478fghht-9287-48c7-a607-bf1b64a8115d')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_compressive_strength - record.avg_compressive_strength*mu_value
                    upper = record.avg_compressive_strength + record.avg_compressive_strength*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_compressive_strength_nabl = 'pass'
                        break
                    else:
                        record.avg_compressive_strength_nabl = 'fail'




                        # Water Absorption

    water_absorption_name = fields.Char("Name",default=" Water Absorption")
    water_absorption_visible = fields.Boolean("Water Absorption",compute="_compute_visible")

    temp_water_absorption = fields.Char("Temp °c")
    humidity_water_absorption = fields.Char("Humidity %")

    water_absorption_child_lines = fields.One2many('mechanical.bricks.water.absorption.line','parent_id',string="Water Absorption Test")

    avg_water_absorption = fields.Float(string="Average Water Absorption ",compute="_compute_avg_water_absorption")


    @api.depends('water_absorption_child_lines.water_absorption')
    def _compute_avg_water_absorption(self):
        for record in self:
            if record.water_absorption_child_lines:
              record.avg_water_absorption = sum(record.water_absorption_child_lines.mapped('water_absorption'))/ len(record.water_absorption_child_lines)
            else:
                record.avg_water_absorption = 0.0

    avg_water_absorption_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_avg_water_absorption_conformity", store=True)

    @api.depends('avg_water_absorption','eln_ref','grade')
    def _compute_avg_water_absorption_conformity(self):
        
        for record in self:
            record.avg_water_absorption_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','321475gfet1-f3ab-4b19-af25-91a4671baf5f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','321475gfet1-f3ab-4b19-af25-91a4671baf5f')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_water_absorption - record.avg_water_absorption*mu_value
                    upper = record.avg_water_absorption + record.avg_water_absorption*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_water_absorption_conformity = 'pass'
                        break
                    else:
                        record.avg_water_absorption_conformity = 'fail'

    avg_water_absorption_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_water_absorption_nabl", store=True)

    @api.depends('avg_water_absorption','eln_ref','grade')
    def _compute_avg_water_absorption_nabl(self):
        
        for record in self:
            record.avg_water_absorption_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','321475gfet1-f3ab-4b19-af25-91a4671baf5f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','321475gfet1-f3ab-4b19-af25-91a4671baf5f')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_water_absorption - record.avg_water_absorption*mu_value
                    upper = record.avg_water_absorption + record.avg_water_absorption*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_water_absorption_nabl = 'pass'
                        break
                    else:
                        record.avg_water_absorption_nabl = 'fail'



 # Dimensions
    dimension_name = fields.Char("Name",default="Dimension Test")
    dimension_visible = fields.Boolean("Dimension Test",compute="_compute_visible")

    length_name = fields.Char("Name",default="Length")
    length_visible = fields.Boolean("Length",compute="_compute_visible")

    width_name = fields.Char("Name",default="Width")
    width_visible = fields.Boolean("Width",compute="_compute_visible")

    height_name = fields.Char("Name",default="height")
    height_visible = fields.Boolean("height",compute="_compute_visible")

    temp_dimension = fields.Char("Temp °c")
    humidity_dimension = fields.Char("Humidity %")

    
    length1 = fields.Float(string="Length  ")
    length2 = fields.Float(string="Length 2 ")
    length3 = fields.Float(string="Length 3 ")
    avg_length = fields.Float(string="Average Length ",compute="_compute_average")

    width1 = fields.Float(string="Width  ")
    width2 = fields.Float(string="Width 2 ")
    width3 = fields.Float(string="Width 3 ")
    avg_width = fields.Float(string="Average Width ",compute="_compute_average")

    height1 = fields.Float(string="height  ")
    height2 = fields.Float(string="height 2 ")
    height3 = fields.Float(string="height 3 ")
    avg_height = fields.Float(string="Average height ",compute="_compute_average")


    @api.depends('length1','length2','length3','width1','width2','width3','height1','height2','height3')
    def _compute_average(self):
        for record in self:
            length = (record.length1 + record.length2 + record.length3)
            width = (record.width1 + record.width2 + record.width3)
            height = (record.height1 + record.height2 + record.height3)

            len_entries = sum(1 for field in [
                record.length1,
                record.length2,
                record.length3
            ] if field)
            if len_entries > 0:
                record.avg_length = length / len_entries
            else:
                record.avg_length = 0.0


            width_entries = sum(1 for field in [
                record.width1,
                record.width2,
                record.length3
            ] if field)
            if width_entries > 0:
                record.avg_width = width / width_entries
            else:
                record.avg_width = 0.0


            height_entries = sum(1 for field in [
                record.height1,
                record.height2,
                record.height3
            ] if field)

            if height_entries > 0:
                record.avg_height = height / height_entries
            else:
                record.avg_height = 0.0


    avg_length_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_avg_length_conformity", store=True)

    @api.depends('avg_length','eln_ref','grade')
    def _compute_avg_length_conformity(self):
        
        for record in self:
            record.avg_length_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ea445305-117e-4e49-82b1-f876b0a34d26')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ea445305-117e-4e49-82b1-f876b0a34d26')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_length - record.avg_length*mu_value
                    upper = record.avg_length + record.avg_length*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_length_conformity = 'pass'
                        break
                    else:
                        record.avg_length_conformity = 'fail'

    avg_length_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_length_nabl", store=True)

    @api.depends('avg_length','eln_ref','grade')
    def _compute_avg_length_nabl(self):
        
        for record in self:
            record.avg_length_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ea445305-117e-4e49-82b1-f876b0a34d26')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ea445305-117e-4e49-82b1-f876b0a34d26')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_length - record.avg_length*mu_value
                    upper = record.avg_length + record.avg_length*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_length_nabl = 'pass'
                        break
                    else:
                        record.avg_length_nabl = 'fail'

    avg_width_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_avg_width_conformity", store=True)

    @api.depends('avg_width','eln_ref','grade')
    def _compute_avg_width_conformity(self):
        
        for record in self:
            record.avg_width_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d29d2505-a5ea-4c8f-a644-8df0a5377a27')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d29d2505-a5ea-4c8f-a644-8df0a5377a27')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_width - record.avg_width*mu_value
                    upper = record.avg_width + record.avg_width*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_width_conformity = 'pass'
                        break
                    else:
                        record.avg_width_conformity = 'fail'

    avg_width_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_width_nabl", store=True)




    @api.depends('avg_width','eln_ref','grade')
    def _compute_avg_width_nabl(self):
        
        for record in self:
            record.avg_width_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d29d2505-a5ea-4c8f-a644-8df0a5377a27')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d29d2505-a5ea-4c8f-a644-8df0a5377a27')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_width - record.avg_width*mu_value
                    upper = record.avg_width + record.avg_width*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_width_nabl = 'pass'
                        break
                    else:
                        record.avg_width_nabl = 'fail'  

    
    avg_height_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_avg_height_conformity", store=True)

    @api.depends('avg_height','eln_ref','grade')
    def _compute_avg_height_conformity(self):
        
        for record in self:
            record.avg_height_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ec5ffecb-2f38-4a7f-93e0-9626feb08139')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ec5ffecb-2f38-4a7f-93e0-9626feb08139')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_height - record.avg_height*mu_value
                    upper = record.avg_height + record.avg_height*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_height_conformity = 'pass'
                        break
                    else:
                        record.avg_height_conformity = 'fail'

    avg_height_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_height_nabl", store=True)

    @api.depends('avg_height','eln_ref','grade')
    def _compute_avg_height_nabl(self):
        
        for record in self:
            record.avg_height_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ec5ffecb-2f38-4a7f-93e0-9626feb08139')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ec5ffecb-2f38-4a7f-93e0-9626feb08139')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_height - record.avg_height*mu_value
                    upper = record.avg_height + record.avg_height*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_height_nabl = 'pass'
                        break
                    else:
                        record.avg_height_nabl = 'fail'  



   



   ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:
            record.compressive_strength_visible = False
            record.water_absorption_visible = False
            record.dimension_visible = False
            record.length_visible = False
            record.width_visible = False
            record.height_visible = False

           

            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)
                if sample.internal_id == "31478fghht-9287-48c7-a607-bf1b64a8115d":
                    record.compressive_strength_visible = True
                if sample.internal_id == "321475gfet1-f3ab-4b19-af25-91a4671baf5f":
                    record.water_absorption_visible = True



                if sample.internal_id == "b8d83f94-3e58-4760-acc9-512499f563dc":
                    record.dimension_visible = True
                    record.length_visible = True 
                    record.width_visible = True
                    record.height_visible = True  


                # if sample.internal_id == "3214598fgrt-d27d-4ef9-9b27-e8eb4e7ae6ac":
                #     record.efflorescence_visible = True
                # if sample.internal_id == "125478bvf3-8d5d-4f45-8afb-b911f9cafe41":
                #     record.dimension_visible = True 
     
    def open_eln_page(self):
        # import wdb; wdb.set_trace()
        for result in self.eln_ref.parameters_result:
            
            # crushing 
            if result.parameter.internal_id == '31478fghht-9287-48c7-a607-bf1b64a8115d':
                result.result_char = round(self.avg_compressive_strength,2)
                if self.avg_compressive_strength_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # water absorbtion
            if result.parameter.internal_id == '321475gfet1-f3ab-4b19-af25-91a4671baf5f':
                result.result_char = round(self.avg_water_absorption,2)
                if self.avg_water_absorption_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

        return {
                'view_mode': 'form',
                'res_model': "lerm.eln",
                'type': 'ir.actions.act_window',
                'target': 'current',
                'res_id': self.eln_ref.id,
                
            }

    @api.model
    def create(self, vals):
        # import wdb;wdb.set_trace()
        record = super(MechanicalBricks, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id
    

    @api.depends('eln_ref')
    def _compute_sample_parameters(self):
        # records = self.env['lerm.eln'].sudo().search([('id','=', record.eln_id.id)]).parameters_result
        # print("records",records)
        # self.sample_parameters = records
        for record in self:
            records = record.eln_ref.parameters_result.parameter.ids
            record.sample_parameters = records
            print("Records",records)

    def get_all_fields(self):
        record = self.env['mechanical.bricks'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values
    





class BrickCompressiveLine(models.Model):
    _name = "mechanical.bricks.compressive.line"
    parent_id = fields.Many2one('mechanical.bricks',string="Parent Id")

   

    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    sample1 = fields.Char(string="Sample Identification")
    length = fields.Float(string="Length")
    width = fields.Float(string="Width")
    thickness = fields.Float(string="Thickness")
    area = fields.Float(string="Area (mm2)",compute="_compute_area",store=True)
    load = fields.Float(string=" Load at Failure (kN)")
    compressive_strength = fields.Float(string="Compressive Strength  N/mm2",compute="_compute_compressive_strength",store=True)
    

    @api.depends('length','width')
    def _compute_area(self):
        for rec in self:
            rec.area = (rec.length * rec.width )

    @api.depends('load','area')
    def _compute_compressive_strength(self):
        for rec in self:
            if rec.area != 0:
                rec.compressive_strength = ((rec.load * 1000) / rec.area )
            else:
                rec.compressive_strength = 0.0




    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(BrickCompressiveLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1

class BrickWaterAbsorptionLine(models.Model):
    _name = "mechanical.bricks.water.absorption.line"
    parent_id = fields.Many2one('mechanical.bricks',string="Parent Id")

    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    sample = fields.Char(string="Sample Identification")
    dry_weight= fields.Float(string="Dry Weight")
    sat_weight= fields.Float(string="Saturated Weight")
    sat_dry_weight = fields.Float(string="Saturated Weight-Dry Weight ",compute="_compute_sat_dry_weight")
    
    water_absorption = fields.Float(string="Saturated Weight-Dry Weight/Dry Weight*100	",compute="_compute_water_absorption")
    
    @api.depends('sat_weight','dry_weight')
    def _compute_sat_dry_weight(self):
        for rec in self:
            rec.sat_dry_weight = (rec.sat_weight - rec.dry_weight )

    @api.depends('sat_dry_weight','dry_weight')
    def _compute_water_absorption(self):
        for rec in self:
            if rec.dry_weight != 0:
                rec.water_absorption = (rec.sat_dry_weight / rec.dry_weight ) *100 
            else:
                rec.water_absorption = 0.0
    



   
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(BrickWaterAbsorptionLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1