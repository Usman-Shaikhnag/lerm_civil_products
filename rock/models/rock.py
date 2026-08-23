from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math
from math import pi

import io
import base64
import matplotlib.pyplot as plt
import numpy as np

import base64
from io import BytesIO
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt



class MechanicalRock(models.Model):
    _name = "mechanical.rock"
    _inherit = "lerm.eln"
    _rec_name = "name_rock"

    name_rock = fields.Char("Name",default="ROCK")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=False)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    size_id = fields.Many2one('lerm.size.line',string="Size",compute="_compute_size_id",store=True)
    sample_id = fields.Many2one('lerm.srf.sample',string="Sample")
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)

    image = fields.Image(
        string="Image",
        max_width=1024,
        max_height=1024
    )


    notes_id = fields.One2many('rock.notes','parent_id',string="Notes")
    
    calc_mode = fields.Boolean(default=True)


    temp_rock = fields.Char(string="Temp.°C" )
    humidity_rock= fields.Char(string="Humidity %" )


    lab_id = fields.Char(
            string="Lab ID",
            compute="_compute_lab_id",
            store=True
        )
    

   

    @api.depends('eln_ref')
    def _compute_lab_id(self):
        for rec in self:
            if rec.eln_ref:
                rec.lab_id = rec.eln_ref.lab_id
            else:
                rec.lab_id = False

    @api.model
    def default_get(self, fields):
        res = super(MechanicalRock, self).default_get(fields)

        default_notes = [
            (0, 0, {
                'sr_no': 'a',
                'notes': 'The information marked with an #  received from customer',
            }),
            (0, 0, {
                'sr_no': 'b',
                'notes': 'The results listed refer only to tested parameters and sample as received from customer',
            }),
            (0, 0, {
                'sr_no': 'c',
                'notes': 'The balance samples if any will be discarded after 15 days from the date of issue of test certificate unless otherwise specified.',
            }),
            (0, 0, {
                'sr_no': 'd',
                'notes': 'This document shall not be reproduced in part or full without the approval of Genstru.',
            }),
              (0, 0, {
                'sr_no': 'e',
                'notes': '^ represents unsoaked test',
            }),
              (0, 0, {
                'sr_no': 'd',
                'notes': '$ represents crumbled in water',
            }),
        ]

        res['notes_id'] = default_notes
        return res

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id

    @api.depends('eln_ref')
    def _compute_size_id(self):
        if self.eln_ref:
            self.size_id = self.eln_ref.size_id.id

    def prefill_data(self):
        # import wdb; wdb.set_trace()
        return {
            'name': 'Prefill Data',
            'type': 'ir.actions.act_window',
            'res_model': 'rock.prefill.data',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.eln_ref.sample_id.material_id.id,
                'exclude_sample_id': self.eln_ref.sample_id.id,
                },
        }



    rock_child_lines = fields.One2many('mechanical.rock.line','parent_id',string="Parameter")
    
    point_load_constant = fields.Float(string="Point Load Constant Core")

    point_load_constant_2 = fields.Float(string="Point Load Constant Lump")

    compressive_strength_constant = fields.Float(string="Compressive Strength  Constant")
    compressive_strength_constant_hd = fields.Float(string="Compressive Strength HD  Constant",digits=(12,4))

    rock_lines_generated = fields.Boolean(string="Rock Lab Lines ",default=False)
    show_sieve = fields.Boolean(default=False)

    # def action_generate_rock_lines(self):
    #     for record in self:
    #         if record.lab_id and ' - ' in record.lab_id:
    #             start_str, end_str = record.lab_id.split(' - ')
    #             prefix = '-'.join(start_str.split('-')[:2])
    #             start = int(start_str.split('-')[2])
    #             end = int(end_str.split('-')[2])

    #             lines = []
    #             for i in range(start, end + 1):
    #                 lab_id = f"{prefix}-{str(i).zfill(3)}"
    #                 lines.append((0, 0, {'lab_id': lab_id}))

    #             record.rock_child_lines = lines
    #             record.rock_lines_generated = True

    #         # 🔹 Set flag to show sieve analysis
    #         if record.rock_child_lines:
    #             record.show_sieve = True

    #         # 🔹 Reload the current record in form view
    #         return {
    #             'type': 'ir.actions.act_window',
    #             'name': 'Rock Form',
    #             'res_model': 'mechanical.rock',
    #             'res_id': record.id,  # ✅ Use record.id instead of self.id
    #             'view_mode': 'form',
    #             'target': 'current',
    #         }

    def action_generate_rock_lines(self):
        for record in self:
            lines = []

            if record.lab_id:
                # 🔹 Range case (e.g. ABC-001 - ABC-005)
                if ' - ' in record.lab_id:
                    start_str, end_str = record.lab_id.split(' - ')
                    prefix = '-'.join(start_str.split('-')[:2])
                    start = int(start_str.split('-')[2])
                    end = int(end_str.split('-')[2])

                    for i in range(start, end + 1):
                        lab_id = f"{prefix}-{str(i).zfill(3)}"
                        lines.append((0, 0, {'lab_id': lab_id}))

                # 🔹 Single lab id case (e.g. ABC-001)
                else:
                    lines.append((0, 0, {'lab_id': record.lab_id}))

            # 🔹 Assign lines and flags
            if lines:
                record.rock_child_lines = lines
                record.rock_lines_generated = True
                record.show_sieve = True

    avg_dia_visible = fields.Boolean("Average Diameter / Distance between Platens (D )",compute="_compute_visible")
    avg_height_visible = fields.Boolean("Average Height (H) / Width (W)",compute="_compute_visible")
    hd_visible = fields.Boolean("H/D",compute="_compute_visible")
    bulk_density_visible = fields.Boolean("Bulk Density",compute="_compute_visible")
    sat_density_visible = fields.Boolean("Sat Density",compute="_compute_visible")
    dry_density_visible = fields.Boolean("Dry Density",compute="_compute_visible")
    water_absorption_visible = fields.Boolean("Water Absorption",compute="_compute_visible")
    porosity_visible = fields.Boolean("Porosity",compute="_compute_visible")
    moisture_content_visible = fields.Boolean("Moisture content",compute="_compute_visible")
    compressive_strength_visible = fields.Boolean("Compressive Strength ",compute="_compute_visible")
    compressive_strength_visible1 = fields.Boolean("Compressive Strength ",compute="_compute_visible")
    point_load_visible = fields.Boolean("Point load",compute="_compute_visible")
    point_load_visible1 = fields.Boolean("Point load",compute="_compute_visible")
    modulus_visible = fields.Boolean("Modulus of Elasticity Test*",compute="_compute_visible")
    stress_rate_visible = fields.Boolean("Stress rate",compute="_compute_visible")
    mode_of_failure_visible = fields.Boolean("Mode of failure / Orientation of sample",compute="_compute_visible")
    sp_gravity_visible = fields.Boolean("Sp. Gravity",compute="_compute_visible")
    duration_of_test_visible = fields.Boolean("Duration of test",compute="_compute_visible")

    
    cerchar_abrasivity_name = fields.Char("Name",default="Determination of CERCHAR Abrasivity Index of Rock")
    cerchar_abrasivity_visible = fields.Boolean("Determination of CERCHAR Abrasivity Index of Rock",compute="_compute_visible")

    show_sieve = fields.Boolean(default=False)

    cerchar_abrasivity_generated = fields.Boolean(string="GSA Lines Generated",default=False)
    cerchar_abrasivity_ids = fields.One2many('cerchar.abrasivity.line', 'parent_id',ondelete='cascade')

    # def action_generate_cerchar_abrasivity_lines(self):
    #     for record in self:
    #         if record.lab_id and ' - ' in record.lab_id:
    #             start_str, end_str = record.lab_id.split(' - ')
    #             prefix = '-'.join(start_str.split('-')[:2])
    #             start = int(start_str.split('-')[2])
    #             end = int(end_str.split('-')[2])

    #             lines = []
    #             for i in range(start, end + 1):
    #                 lab_id = f"{prefix}-{str(i).zfill(3)}"
    #                 lines.append((0, 0, {'lab_id': lab_id}))

    #             record.cerchar_abrasivity_ids = lines
    #             record.cerchar_abrasivity_generated = True

    #         # 🔹 Set flag to show sieve analysis
    #         if record.cerchar_abrasivity_ids:
    #             record.show_sieve = True

    def action_generate_cerchar_abrasivity_lines(self):
        for record in self:
            lines = []

            if record.lab_id:
                # 🔹 Range case (e.g. ABC-001 - ABC-005)
                if ' - ' in record.lab_id:
                    start_str, end_str = record.lab_id.split(' - ')
                    prefix = '-'.join(start_str.split('-')[:2])
                    start = int(start_str.split('-')[2])
                    end = int(end_str.split('-')[2])

                    for i in range(start, end + 1):
                        lab_id = f"{prefix}-{str(i).zfill(3)}"
                        lines.append((0, 0, {'lab_id': lab_id}))

                # 🔹 Single lab id case (e.g. ABC-001)
                else:
                    lines.append((0, 0, {'lab_id': record.lab_id}))

            # 🔹 Assign lines and flags
            if lines:
                record.cerchar_abrasivity_ids = lines
                record.cerchar_abrasivity_generated = True
                record.show_sieve = True



    slake_durability_child_lines = fields.One2many('mechanical.slake.line','parent_id',string="Parameter")
    slake_durability_visible = fields.Boolean("DETERMINATION OF SLAKE DURABILITY OF ROCK",compute="_compute_visible")

    slake_durability_name = fields.Char("Name",default="DETERMINATION OF SLAKE DURABILITY OF ROCK")


   
    slake_durability_generated = fields.Boolean(string="Rock Lab Lines ",default=False)
    show_sieve = fields.Boolean(default=False)

    # def action_generate_slake_durability(self):
    #     for record in self:
    #         if record.lab_id and ' - ' in record.lab_id:
    #             start_str, end_str = record.lab_id.split(' - ')
    #             prefix = '-'.join(start_str.split('-')[:2])
    #             start = int(start_str.split('-')[2])
    #             end = int(end_str.split('-')[2])

    #             lines = []
    #             for i in range(start, end + 1):
    #                 lab_id = f"{prefix}-{str(i).zfill(3)}"
    #                 lines.append((0, 0, {'lab_id': lab_id}))

    #             record.slake_durability_child_lines = lines
    #             record.slake_durability_generated = True

    #         # 🔹 Set flag to show sieve analysis
    #         if record.slake_durability_child_lines:
    #             record.show_sieve = True

    def action_generate_slake_durability(self):
        for record in self:
            lines = []

            if record.lab_id:
                # 🔹 Range case (e.g. ABC-001 - ABC-005)
                if ' - ' in record.lab_id:
                    start_str, end_str = record.lab_id.split(' - ')
                    prefix = '-'.join(start_str.split('-')[:2])
                    start = int(start_str.split('-')[2])
                    end = int(end_str.split('-')[2])

                    for i in range(start, end + 1):
                        lab_id = f"{prefix}-{str(i).zfill(3)}"
                        lines.append((0, 0, {'lab_id': lab_id}))

                # 🔹 Single lab id case (e.g. ABC-001)
                else:
                    lines.append((0, 0, {'lab_id': record.lab_id}))

            # 🔹 Assign lines and flags
            if lines:
                record.slake_durability_child_lines = lines
                record.slake_durability_generated = True
                record.show_sieve = True












    # MODULUS OF ELASTICITY AND POISSON'S RATIO OF ROCK  

 


# class StressStrainLine(models.Model):
#     _name = "stress.strain.line"
#     _description = "Stress Strain Line"

#     parent_id = fields.Many2one(
#         "stress.strain",
#         string="Parent",
#         ondelete="cascade",
#         required=True
#     )

#     stress = fields.Float(string="Stress (MPa)")
#     strain = fields.Float(string="Strain")
#     StressStrain_visible = fields.Boolean("Stress Range",compute="_compute_visible")









    # triaxial 

    triaxial_visible = fields.Boolean("Triaxial Shear Test (Rock)",compute="_compute_visible")
    triaxial_name = fields.Char("Name",default="Triaxial Shear Test (Rock)")
    show_sieve = fields.Boolean(default=False)
    triaxial_generated = fields.Boolean(string="GSA Lines Generated",default=False)
    triaxial_ids = fields.One2many('triaxial.line', 'parent_id',ondelete='cascade')

    doc_name1 = fields.Char("Doc Name",default="Triaxial Shear Test (Rock)")


    # def action_generate_triaxial_lines(self):
    #     for record in self:
    #         if record.lab_id and ' - ' in record.lab_id:
    #             start_str, end_str = record.lab_id.split(' - ')
    #             prefix = '-'.join(start_str.split('-')[:2])
    #             start = int(start_str.split('-')[2])
    #             end = int(end_str.split('-')[2])

    #             lines = []
    #             for i in range(start, end + 1):
    #                 lab_id = f"{prefix}-{str(i).zfill(3)}"
    #                 lines.append((0, 0, {'lab_id': lab_id}))

    #             record.triaxial_ids = lines
    #             record.triaxial_generated = True

    #         # 🔹 Set flag to show sieve analysis
    #         if record.triaxial_ids:
    #             record.show_sieve = True

    def action_generate_triaxial_lines(self):
        for record in self:
            lines = []

            if record.lab_id:
                # 🔹 Range case (e.g. ABC-001 - ABC-005)
                if ' - ' in record.lab_id:
                    start_str, end_str = record.lab_id.split(' - ')
                    prefix = '-'.join(start_str.split('-')[:2])
                    start = int(start_str.split('-')[2])
                    end = int(end_str.split('-')[2])

                    for i in range(start, end + 1):
                        lab_id = f"{prefix}-{str(i).zfill(3)}"
                        lines.append((0, 0, {'lab_id': lab_id}))

                # 🔹 Single lab id case (e.g. ABC-001)
                else:
                    lines.append((0, 0, {'lab_id': record.lab_id}))

            # 🔹 Assign lines and flags
            if lines:
                record.triaxial_ids = lines
                record.triaxial_generated = True
                record.show_sieve = True


    elasticity_visible = fields.Boolean("MODULUS OF ELASTICITY AND POISSON'S RATIO OF ROCK",compute="_compute_visible")
    elasticity_name = fields.Char("Name",default="MODULUS OF ELASTICITY AND POISSON'S RATIO OF ROCK")

    show_sieve = fields.Boolean(default=False)
    elasticity_generated = fields.Boolean(string="GSA Lines Generated",default=False)
    elasticity_ids = fields.One2many('elasticity.line', 'parent_id',ondelete='cascade')

    doc_name2 = fields.Char("Doc Name",default="MODULUS OF ELASTICITY AND POISSON'S RATIO OF ROCK")


    # def action_generate_elasticity_lines(self):
    #     for record in self:
    #         if record.lab_id and ' - ' in record.lab_id:
    #             start_str, end_str = record.lab_id.split(' - ')
    #             prefix = '-'.join(start_str.split('-')[:2])
    #             start = int(start_str.split('-')[2])
    #             end = int(end_str.split('-')[2])

    #             lines = []
    #             for i in range(start, end + 1):
    #                 lab_id = f"{prefix}-{str(i).zfill(3)}"
    #                 lines.append((0, 0, {'lab_id': lab_id}))

    #             record.elasticity_ids = lines
    #             record.elasticity_generated = True

    #         # 🔹 Set flag to show sieve analysis
    #         if record.elasticity_ids:
    #             record.show_sieve = True

    def action_generate_elasticity_lines(self):
        for record in self:
            lines = []

            if record.lab_id:
                # 🔹 Range case (e.g. ABC-001 - ABC-005)
                if ' - ' in record.lab_id:
                    start_str, end_str = record.lab_id.split(' - ')
                    prefix = '-'.join(start_str.split('-')[:2])
                    start = int(start_str.split('-')[2])
                    end = int(end_str.split('-')[2])

                    for i in range(start, end + 1):
                        lab_id = f"{prefix}-{str(i).zfill(3)}"
                        lines.append((0, 0, {'lab_id': lab_id}))

                # 🔹 Single lab id case (e.g. ABC-001)
                else:
                    lines.append((0, 0, {'lab_id': record.lab_id}))

            # 🔹 Assign lines and flags
            if lines:
                record.elasticity_ids = lines
                record.elasticity_generated = True
                record.show_sieve = True



    # Tensile Srength 

    tensile_strength_visible = fields.Boolean("Tensile Srength",compute="_compute_visible")
    tensile_strength_name = fields.Char("Name",default="Tensile Srength")
    show_sieve = fields.Boolean(default=False)
    tensile_strength_generated = fields.Boolean(string="GSA Lines Generated",default=False)
    tensile_strength_ids = fields.One2many('rock.tensile.strength.line', 'parent_id',ondelete='cascade')

    doc_name1 = fields.Char("Doc Name",default="Tensile Srength")



    def action_generate_tensile_strength_lines(self):
        for record in self:
            lines = []

            if record.lab_id:
                # 🔹 Range case (e.g. ABC-001 - ABC-005)
                if ' - ' in record.lab_id:
                    start_str, end_str = record.lab_id.split(' - ')
                    prefix = '-'.join(start_str.split('-')[:2])
                    start = int(start_str.split('-')[2])
                    end = int(end_str.split('-')[2])

                    for i in range(start, end + 1):
                        lab_id = f"{prefix}-{str(i).zfill(3)}"
                        lines.append((0, 0, {'lab_id': lab_id}))

                # 🔹 Single lab id case (e.g. ABC-001)
                else:
                    lines.append((0, 0, {'lab_id': record.lab_id}))

            # 🔹 Assign lines and flags
            if lines:
                record.tensile_strength_ids = lines
                record.tensile_strength_generated = True
                record.show_sieve = True



    




   
    ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:
            # record.usc_visible = False
            record.avg_dia_visible = False
            record.avg_height_visible = False
            record.hd_visible = False
            record.bulk_density_visible = False
            record.sat_density_visible = False
            record.dry_density_visible = False
            record.water_absorption_visible = False
            record.porosity_visible = False
            record.moisture_content_visible = False
            record.compressive_strength_visible = False
            record.compressive_strength_visible1 = False
            record.point_load_visible = False
            record.point_load_visible1 = False
            record.modulus_visible = False
            record.duration_of_test_visible = False
            record.stress_rate_visible = False
            record.mode_of_failure_visible = False
            record.sp_gravity_visible = False

            record.cerchar_abrasivity_visible = False

            record.slake_durability_visible = False
            record.triaxial_visible = False

            record.tensile_strength_visible = False



            record.elasticity_visible = False


          
            
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)

                # if sample.internal_id == "a1f9c5d0-0bc7-41a6-a2bb-0fe9d898008d":
                #     record.usc_visible = True
                if sample.internal_id == "a1f9c5d0-0bc7-41a6-a2bb-0fe9214587uytf":
                    record.avg_dia_visible = True
                if sample.internal_id == "a1f9c5d0-0bc7-41a6-a2bb-0fe921147852gh":
                    record.avg_height_visible = True
                if sample.internal_id == "201478ght-0bc7-41a6-a2bb-0fe9211478521gt":
                    record.hd_visible = True
                if sample.internal_id == "210478bbb-0bc7-41a6-a2bb-0fe9211478521r4":
                    record.bulk_density_visible = True
                if sample.internal_id == "20123rtyng-0bc7-41a6-a2bb-0fe921147814524":
                    record.sat_density_visible = True
                if sample.internal_id == "4578uuuytt-0bc7-41a6-a2bb-0fe9211478tyu556":
                    record.dry_density_visible = True
                if sample.internal_id == "2147852trr-0bc7-41a6-a2bb-0fe92114rterrgghy":
                    record.water_absorption_visible = True
                if sample.internal_id == "55544ttyyyr-0bc7-41a6-a2bb-0fe92114rterertty":
                    record.porosity_visible = True
                if sample.internal_id == "7778rrrtttgg-0bc7-41a6-a2bb-0fe92114rr445ttj":
                    record.moisture_content_visible = True
                if sample.internal_id == "88rrty222vv33-0bc7-41a6-a2bb-0fe92114rr445t":
                    record.compressive_strength_visible = True


                if sample.internal_id == "5578gghty214-0bc7-41a6-a2bb-0fe92114rr445t":
                    record.compressive_strength_visible1 = True

                if sample.internal_id == "785587rttgg11-0bc7-41a6-a2bb-0fe92114rr445t":
                    record.point_load_visible = True

                if sample.internal_id == "87522869rtyhn-0bc7-41a6-a2bb-0fe92114rr445t":
                    record.point_load_visible1 = True

                if sample.internal_id == "8855fgrtuumm-0bc7-41a6-a2bb-0fe92114rr445t":
                    record.modulus_visible = True
                if sample.internal_id == "9995522tyynn1-0bc7-41a6-a2bb-0fe92114rr4457":
                    record.duration_of_test_visible = True
                if sample.internal_id == "3332gghytt1144-0bc7-41a6-a2bb-0fe92114rr478t":
                    record.stress_rate_visible = True
                if sample.internal_id == "22277gght1100t-0bc7-41a6-a2bb-0fe92114rr478y":
                    record.mode_of_failure_visible = True
                if sample.internal_id == "8866ggtrhh2277j-0bc7-41a6-a2bb-0fe92114rr4yre":
                    record.sp_gravity_visible = True

                if sample.internal_id == "210324nrhh2277j-0bc7-41a6-a2bb-0fe92111234poy":
                    record.cerchar_abrasivity_visible = True

                if sample.internal_id == "3258tyumhh2277j-0bc7-41a6-a2bb-0fe92112457hyte":
                    record.slake_durability_visible = True

                if sample.internal_id == "214jht3mhh2277j-0bc7-41a6-a2bb-0fe9211321ytrbe":
                    record.triaxial_visible = True


                if sample.internal_id == "b448cca3-37d8-40d5-9599-87a2f0a8d267":
                    record.tensile_strength_visible = True





                if sample.internal_id == "22145-f6f5-4b5b-bfc2-34792cf1a235265555677":
                    record.elasticity_visible = True

              
               

                
    
   
            
           

    def open_eln_page(self):
        # import wdb; wdb.set_trace()
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        if current_user.has_group('lerm_civil.lerm_discipline_group'):
            technician_results = self.eln_ref.parameters_result
        else:
            technician_results = self.eln_ref.parameters_result.filtered(
                lambda r: r.technician == current_user
            )

        for result in technician_results:

            

            if result.parameter.internal_id == 'b448cca3-37d8-40d5-9599-87a2f0a8d267':
                result.calculated = True
                   
            if result.parameter.internal_id == 'a1f9c5d0-0bc7-41a6-a2bb-0fe9d898008d':
                result.calculated = True

            if result.parameter.internal_id == 'a1f9c5d0-0bc7-41a6-a2bb-0fe9214587uytf':
                result.calculated = True
            
            if result.parameter.internal_id == 'a1f9c5d0-0bc7-41a6-a2bb-0fe921147852gh':
                result.calculated = True
            if result.parameter.internal_id == '201478ght-0bc7-41a6-a2bb-0fe9211478521gt':
                result.calculated = True

            if result.parameter.internal_id == '210478bbb-0bc7-41a6-a2bb-0fe9211478521r4':
                result.calculated = True
            if result.parameter.internal_id == '20123rtyng-0bc7-41a6-a2bb-0fe921147814524':
                result.calculated = True
            if result.parameter.internal_id == '4578uuuytt-0bc7-41a6-a2bb-0fe9211478tyu556':
                result.calculated = True
            if result.parameter.internal_id == '2147852trr-0bc7-41a6-a2bb-0fe92114rterrgghy':
                result.calculated = True
            if result.parameter.internal_id == '55544ttyyyr-0bc7-41a6-a2bb-0fe92114rterertty':
                result.calculated = True
            if result.parameter.internal_id == '7778rrrtttgg-0bc7-41a6-a2bb-0fe92114rr445ttj':
                result.calculated = True
            if result.parameter.internal_id == '88rrty222vv33-0bc7-41a6-a2bb-0fe92114rr445t':
                result.calculated = True
            if result.parameter.internal_id == '785587rttgg11-0bc7-41a6-a2bb-0fe92114rr445t':
                result.calculated = True
            if result.parameter.internal_id == '8855fgrtuumm-0bc7-41a6-a2bb-0fe92114rr445t':
                result.calculated = True
            if result.parameter.internal_id == '9995522tyynn1-0bc7-41a6-a2bb-0fe92114rr4457':
                result.calculated = True
            if result.parameter.internal_id == '3332gghytt1144-0bc7-41a6-a2bb-0fe92114rr478t':
                result.calculated = True
            if result.parameter.internal_id == '22277gght1100t-0bc7-41a6-a2bb-0fe92114rr478y':
                result.calculated = True
            if result.parameter.internal_id == '8866ggtrhh2277j-0bc7-41a6-a2bb-0fe92114rr4yre':
                result.calculated = True
            if result.parameter.internal_id == '5578gghty214-0bc7-41a6-a2bb-0fe92114rr445t':
                result.calculated = True
            if result.parameter.internal_id == '87522869rtyhn-0bc7-41a6-a2bb-0fe92114rr445t':
                result.calculated = True
            if result.parameter.internal_id == '210324nrhh2277j-0bc7-41a6-a2bb-0fe92111234poy':
                result.calculated = True

            if result.parameter.internal_id == '3258tyumhh2277j-0bc7-41a6-a2bb-0fe92112457hyte':
                result.calculated = True

            if result.parameter.internal_id == '214jht3mhh2277j-0bc7-41a6-a2bb-0fe9211321ytrbe':
                result.calculated = True

            if result.parameter.internal_id == '6315f914-f6f5-4b5b-bfc2-34792cf1a237':
                result.calculated = True

            if result.parameter.internal_id == '6315f914-f6f5-4b5b-bfc2-34792cf1a237e':
                result.calculated = True

            if result.parameter.internal_id == '22145-f6f5-4b5b-bfc2-34792cf1a235265555677':
                result.calculated = True





           


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
        record = super(MechanicalRock, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record







    @api.depends('eln_ref', 'eln_ref.parameters_result.technician')
    @api.depends_context('uid')
    def _compute_sample_parameters(self):
        current_user = self.env.user

        for record in self:
            if not record.eln_ref:
                record.sample_parameters = [(6, 0, [])]
                continue

            # Check if user is in Lerm Admin group
            if (
                current_user.has_group('lerm_civil.kes_admin_access_group')
                or current_user.has_group('lerm_civil.lerm_sample_verification')
                or current_user.has_group('lerm_civil.lerm_sample_approval')
            ):
                # Admin sees all parameters
                parameter_ids = record.eln_ref.parameters_result.mapped('parameter').ids
            else:
                # Other users only see parameters assigned to them
                user_param_results = record.eln_ref.parameters_result.filtered(
                    lambda r: r.technician and r.technician.id == current_user.id
                )
                parameter_ids = user_param_results.mapped('parameter').ids

            record.sample_parameters = [(6, 0, parameter_ids)]



    def get_all_fields(self):
        record = self.env['mechanical.rock'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values




class MechanicalRockLine(models.Model):
    _name = "mechanical.rock.line"
    parent_id = fields.Many2one('mechanical.rock',string="Parent Id")

    bh_no = fields.Char(
        string="BH No./Location",
        compute="_compute_consolidation",
        store=True
    )

    depth = fields.Char(
        string="Depth (m)",
        compute="_compute_consolidation",
        store=True
    )

    
    @api.depends('lab_id')
    def _compute_consolidation(self):
        ReviewLine = self.env['sample.request.review.lines']

        for line in self:
            line.bh_no = False
            line.depth = False

            if not line.lab_id:
                continue

            review_line = ReviewLine.search(
                [('lab_id', '=', line.lab_id)],
                order='id desc',
                limit=1
            )

            if review_line:
                line.bh_no = review_line.source        # BH ID / Location
                line.depth = review_line.depth         # Depth (m)

    # blue_input = fields.Boolean(default=True,invisible=True)
   
    sr_no = fields.Integer(string="Specimen NO.", readonly=True, copy=False, default=1)
    date_received = fields.Date(string="Date of Test Started")
    date_testing = fields.Date(string="Date of Completion")
    lab_id = fields.Char(string="Lab ID") 
    # bh_no = fields.Char(string="BH No./Location",digits=(16, 3))
    # depth = fields.Char(string="Depth")
    piece_no = fields.Char(string="Piece No")
    lithological = fields.Char(string="Lithological Description of rock")
    room_temp = fields.Float(string="Room Temperature")
    relative_humidity = fields.Float(string="Relative humidity %",digits=(16, 2))
    water_temperature = fields.Float(string="Water temperature",digits=(16, 2))
    dia_rock1 = fields.Float(string="Diameter of Rock Sample 1",digits=(16, 2))
    dia_rock2 = fields.Float(string="Diameter of Rock Sample 2",digits=(16, 2))
    dia_rock3 = fields.Float(string="Diameter of Rock Sample 3",digits=(16, 2))
    avg_dia = fields.Float(string="Average Diameter (D)",digits=(16, 13),store=True,compute="_compute_avg_dia")
    height_rock1 = fields.Float(string="Height of Rock Sample 1",digits=(16, 2))
    height_rock2 = fields.Float(string="Height of Rock Sample 2",digits=(16, 2))
    height_rock3 = fields.Float(string="Height of Rock Sample 3",digits=(16, 2))
    avg_height = fields.Float(string="Average Height (H)",digits=(16, 10),store=True,compute="_compute_avg_height")
    hd = fields.Float(string="H/D",digits=(16, 10),store=True,compute="_compute_hd")
    volume_of_sample = fields.Float(string="Volume of Sample(Wsat-Wsub)",digits=(16, 2),store=True,compute="_compute_volume_of_sample")
    volume_of_sample1 = fields.Float(string="Volume of Sample",digits=(16, 2))
    initial_wt = fields.Float(string="Initial Wt of sample",digits=(16, 2))
    dry_wet = fields.Float(string="Dry Wt of sample",digits=(16, 2))
    saturated_wet = fields.Float(string="Saturated Wt of sample",digits=(16, 2))
    volume_of_void = fields.Float(string="Volume of Voids (cm³)",digits=(16, 2),store=True,compute="_compute_volume_of_void")
    wt_of_sample = fields.Float(string="Wt of sample in Water",digits=(16, 2))
    sp_gravity = fields.Float(string="Sp. Gravity",digits=(16, 2),store=True,compute="_compute_sp_gravity")
    bulk_density = fields.Float(string="Bulk Density",digits=(16, 2),store=True,compute="_compute_bulk_density")
    sat_density = fields.Float(string="Sat Density",digits=(16, 4),store=True,compute="_compute_sat_density")
    dry_density = fields.Float(string="Dry Density",digits=(16, 4),store=True,compute="_compute_dry_density")
    water_absorption = fields.Float(string="Water Absorption",digits=(16, 2),store=True,compute="_compute_water_absorption")
    porosity = fields.Float(string="Porosity",digits=(16, 2),store=True,compute="_compute_porosity")
    load_ucs = fields.Float(string="Load (UCS)",digits=(16, 2))
    load = fields.Float(string="Load",digits=(16, 10),store=True,compute="_compute_load")
    comp_strength1 = fields.Float(string="Compressive Strength qc ",digits=(16, 10),store=True,compute="_compute_comp_strength1")
    comp_strength2 = fields.Float(string="Compressive Strength  qc at H/D=2",digits=(16, 10),store=True,compute="_compute_comp_strength2")
    point_load = fields.Float(string="Point Load",digits=(16, 2))
    point_load_strength = fields.Float(string="Point load strength index-Core",digits=(16, 3),store=True,compute="_compute_point_load_strength")
    point_load_index = fields.Float(string="Point load strength index-Lump",digits=(16, 3),store=True,compute="_compute_point_load_index")
    comp_strength4 = fields.Float(string="Compressive strength , qc from pt load",digits=(16, 2),store=True,compute="_compute_comp_strength4")
    comp_strength5 = fields.Float(string="Compressive strength , qc (H/D >1)",digits=(16, 2),store=True,compute="_compute_comp_strength5")
    duration_of_test = fields.Float(string="Duration of the test (Sec)",digits=(16, 2))
    mode_of_failure = fields.Char(string="Mode of failure",digits=(16, 2))
    comp_rock = fields.Float(string="Compressive Strength  qc ",digits=(16, 2),store=True,compute="_compute_comp_rock")
    comp_rock1 = fields.Float(string="Compressive Strength  qc at H/D=2",digits=(16, 2),store=True,compute="_compute_comp_rock1")
    stress_rate = fields.Float(string="Stress Rate",digits=(16, 2),store=True,compute="_compute_stress_rate")
    moisture_content = fields.Float(string="Moisture Content %",digits=(16, 2),store=True,compute="_compute_moisture_content")

    point_load_type = fields.Selection(
    [
        ('core', 'Core'),
        ('lump', 'Lump'),
    ],
    string="Point Load Type",
    required=True)

    point_load_index1 = fields.Float(string="Point Load",digits=(16, 2),store=True,compute="_compute_point_load_index1")

   

    @api.depends('point_load', 'avg_dia', 'avg_height', 'point_load_type')
    def _compute_point_load_index1(self):
     for rec in self:
        P = rec.point_load or 0.0

        if rec.point_load_type == 'core' and rec.avg_dia:
            D = rec.avg_dia
            rec.point_load_index1 = (
                1000 * P
            ) / (math.sqrt(50) * (D ** 1.5))

        elif rec.point_load_type == 'lump' and rec.avg_dia and rec.avg_height:
            De = rec.avg_dia * rec.avg_height
            rec.point_load_index1 = (
                1000 * P
            ) / (math.sqrt(50) * (De ** 0.75))

        else:
            rec.point_load_index1 = 0.0


    @api.depends('dia_rock1', 'dia_rock2', 'dia_rock3')
    def _compute_avg_dia(self):
        for rec in self:
            values = [rec.dia_rock1, rec.dia_rock2, rec.dia_rock3]
            valid_values = [v for v in values if v]  
            rec.avg_dia = sum(valid_values) / len(valid_values) if valid_values else 0.0

    @api.depends('height_rock1', 'height_rock2', 'height_rock3')
    def _compute_avg_height(self):
        for rec in self:
            valuess = [rec.height_rock1, rec.height_rock2, rec.height_rock3]
            valid_valuess = [v for v in valuess if v]  
            rec.avg_height = sum(valid_valuess) / len(valid_valuess) if valid_valuess else 0.0

    @api.depends('avg_height', 'avg_dia')
    def _compute_hd(self):
        for rec in self:
            if rec.avg_dia:
                rec.hd = rec.avg_height / rec.avg_dia
            else:
                rec.hd = 0.0

 

    # ---- Compute method ----
    @api.depends('saturated_wet', 'wt_of_sample')
    def _compute_volume_of_sample(self):
        for rec in self:
            rec.volume_of_sample = rec.saturated_wet - rec.wt_of_sample if rec.saturated_wet and rec.wt_of_sample else 0.0


      # ---- Compute method ----
    @api.depends('saturated_wet', 'dry_wet')
    def _compute_volume_of_void(self):
        for rec in self:
            rec.volume_of_void = rec.saturated_wet - rec.dry_wet if rec.saturated_wet and rec.dry_wet else 0.0

    @api.depends('dry_wet', 'saturated_wet', 'wt_of_sample', 'volume_of_void')
    def _compute_sp_gravity(self):
        for rec in self:
            denominator = (rec.saturated_wet - rec.wt_of_sample) - rec.volume_of_void
            if denominator and denominator != 0:
                rec.sp_gravity = rec.dry_wet / denominator
            else:
                rec.sp_gravity = 0.0

    @api.depends('initial_wt', 'volume_of_sample1')
    def _compute_bulk_density(self):
        for rec in self:
            if rec.volume_of_sample1 and rec.volume_of_sample1 != 0:
                rec.bulk_density = rec.initial_wt / rec.volume_of_sample1
            else:
                rec.bulk_density = 0.0

    @api.depends('saturated_wet', 'volume_of_sample1')
    def _compute_sat_density(self):
        for rec in self:
            if rec.volume_of_sample1 and rec.volume_of_sample1 != 0:
                rec.sat_density = rec.saturated_wet / rec.volume_of_sample1
            else:
                rec.sat_density = 0.0

    @api.depends('dry_wet', 'volume_of_sample1')
    def _compute_dry_density(self):
        for rec in self:
            if rec.volume_of_sample1 and rec.volume_of_sample1 != 0:
                rec.dry_density = rec.dry_wet / rec.volume_of_sample1
            else:
                rec.dry_density = 0.0

    # @api.depends('sat_density', 'dry_density')
    # def _compute_water_absorption(self):
    #     for rec in self:
    #         if rec.dry_density and rec.dry_density != 0:
    #             rec.water_absorption = ((rec.sat_density - rec.dry_density) / rec.dry_density) * 100
    #         else:
    #             rec.water_absorption = 0.0

    @api.depends('sat_density', 'dry_density')
    def _compute_water_absorption(self):
        for rec in self:
            if rec.dry_density and rec.dry_density != 0:
                # चार दशांश पर्यंत calculation साठी precision control
                sat = float(f"{rec.sat_density:.4f}")
                dry = float(f"{rec.dry_density:.4f}")

                rec.water_absorption = ((sat - dry) / dry) * 100
            else:
                rec.water_absorption = 0.0

    @api.depends('sat_density', 'dry_density')
    def _compute_porosity(self):
        for rec in self:
                rec.porosity = (rec.sat_density - rec.dry_density) * 100

    @api.depends('load_ucs')
    def _compute_load(self):
        for rec in self:
            rec.load = rec.load_ucs / 10 if rec.load_ucs else 0.0

    @api.depends('load', 'avg_dia')
    def _compute_comp_strength1(self):
        for rec in self:
            if rec.load and rec.avg_dia:
                rec.comp_strength1 = (rec.load * 1000) / ((math.pi / 4) * (rec.avg_dia ** 2) / 100)
            else:
                rec.comp_strength1 = 0.0

    @api.depends('comp_strength1', 'hd')
    def _compute_comp_strength2(self):
        for rec in self:
            if rec.hd and rec.comp_strength1:
                rec.comp_strength2 = 0.889 * rec.comp_strength1 / (0.778 + (0.222 / rec.hd))
            else:
                rec.comp_strength2 = 0.0

    

    @api.depends('point_load', 'avg_dia')
    def _compute_point_load_strength(self):
     for rec in self:
        point_load = rec.point_load or 0
        avg_dia = rec.avg_dia or 0
        

        if point_load > 0 and avg_dia > 0 :
            rec.point_load_strength = (
                1000 * point_load
            ) / (
                math.sqrt(50) * (avg_dia ** 1.5)
            )
        else:
            rec.point_load_strength = 0.0



    # @api.depends('point_load', 'avg_dia', 'avg_height','parent_id.point_load_constant')
    # def _compute_point_load_index(self):
    #     for rec in self:
    #         if rec.point_load and rec.avg_dia and rec.avg_height and rec.avg_dia*rec.avg_height > 0:
    #             rec.point_load_index = (1000 * rec.point_load) / (math.sqrt(rec.parent_id.point_load_constant) * ((rec.avg_dia * rec.avg_height) ** 0.75))
    #         else:
    #             rec.point_load_index = 0.0

    @api.depends(
    'point_load',
    'avg_dia',
    'avg_height'
)
    def _compute_point_load_index(self):
     for rec in self:
        point_load = rec.point_load or 0
        avg_dia = rec.avg_dia or 0
        avg_height = rec.avg_height or 0
        

        if avg_dia > 0 and avg_height > 0 and  point_load > 0:
            area = avg_dia * avg_height

            rec.point_load_index = (
                1000 * point_load
            ) / (
                math.sqrt(50) * (area ** 0.75)
            )
        else:
            rec.point_load_index = 0.0 


    @api.depends('point_load_strength')
    def _compute_comp_strength4(self):
        for rec in self:
            rec.comp_strength4 = 20 * rec.point_load_strength if rec.point_load_strength else 0.0

    @api.depends('point_load_index')
    def _compute_comp_strength5(self):
        for rec in self:
            rec.comp_strength5 = 20 * rec.point_load_index if rec.point_load_index else 0.0


    @api.depends('comp_strength1')
    def _compute_comp_rock(self):
        for rec in self:
            rec.comp_rock = 0.098 * rec.comp_strength1 if rec.comp_strength1 else 0.0

    @api.depends('comp_strength2')
    def _compute_comp_rock1(self):
        for rec in self:
            rec.comp_rock1 = 0.098 * rec.comp_strength2 if rec.comp_strength2 else 0.0

    @api.depends('comp_rock1', 'duration_of_test')
    def _compute_stress_rate(self):
        for rec in self:
            if rec.duration_of_test:
                rec.stress_rate = rec.comp_rock1 / rec.duration_of_test
            else:
                rec.stress_rate = 0.0

    @api.depends('initial_wt', 'dry_wet')
    def _compute_moisture_content(self):
        for rec in self:
            if rec.dry_wet:
                rec.moisture_content = ((rec.initial_wt - rec.dry_wet) / rec.dry_wet) * 100
            else:
                rec.moisture_content = 0.0










    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(MechanicalRockLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class RockNotes(models.Model):
    _name = "rock.notes"

    parent_id = fields.Many2one('mechanical.rock',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")



class MechanicalCercharLine(models.Model):
    _name = "mechanical.cerchar.line"
    parent_id_cerchar = fields.Many2one('cerchar.abrasivity.line',string="Parent Id")

    
   
    sr_no = fields.Integer(string="Sr. No.", readonly=True, copy=False, default=1)
    d_mm = fields.Char(string="d (mm)")
    room_temp1 = fields.Float(string="Room Temperature (°C)")
   
    pin1_intial = fields.Float(string="Initial Reading(mm)")
    pon1_final = fields.Float(string="Final Reading(mm)")
    pin_result = fields.Float(string="",digits=(16, 2),compute="_compute_pin_result",store=True)

    

    pin2initial = fields.Float(string="Initial Reading(mm)",digits=(16, 2))
    pin2final = fields.Float(string="Final Reading(mm)",digits=(16, 2))
    pin2result = fields.Float(string="",digits=(16, 2),compute="_compute_pin2_result",store=True)

    pin3initial = fields.Float(string="Initial Reading(mm)",digits=(16, 2))
    pin3final = fields.Float(string="Final Reading(mm)",digits=(16, 2))
    pin3result = fields.Float(string="",digits=(16, 2),compute="_compute_pin3_result",store=True)

    pin4initial = fields.Float(string="Initial Reading(mm)",digits=(16, 2))
    pin4final = fields.Float(string="Final Reading(mm)",digits=(16, 2))
    pin4result = fields.Float(string="",digits=(16, 2),compute="_compute_pin4_result",store=True)

    pin5initial = fields.Float(string="Initial Reading(mm)",digits=(16, 2))
    pin5final = fields.Float(string="Final Reading(mm)",digits=(16, 2))
    pin5result = fields.Float(string="",digits=(16, 2),compute="_compute_pin5_result",store=True)

    @api.depends('pin1_intial', 'pon1_final')
    def _compute_pin_result(self):
        for rec in self:
            if rec.pin1_intial and rec.pon1_final:
                rec.pin_result = rec.pin1_intial - rec.pon1_final
            else:
                rec.pin_result = 0.0

    @api.depends('pin2initial', 'pin2final')
    def _compute_pin2_result(self):
        for rec in self:
            if rec.pin2initial and rec.pin2final:
                rec.pin2result = rec.pin2initial - rec.pin2final
            else:
                rec.pin2result = 0.0

    @api.depends('pin3initial', 'pin3final')
    def _compute_pin3_result(self):
        for rec in self:
            if rec.pin3initial and rec.pin3final:
                rec.pin3result = rec.pin3initial - rec.pin3final
            else:
                rec.pin3result = 0.0

    @api.depends('pin4initial', 'pin4final')
    def _compute_pin4_result(self):
        for rec in self:
            if rec.pin4initial and rec.pin4final:
                rec.pin4result = rec.pin4initial - rec.pin4final
            else:
                rec.pin4result = 0.0

    @api.depends('pin5initial', 'pin5final')
    def _compute_pin5_result(self):
        for rec in self:
            if rec.pin5initial and rec.pin5final:
                rec.pin5result = rec.pin5initial - rec.pin5final
            else:
                rec.pin5result = 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id_cerchar'):
            existing_records = self.search([('parent_id_cerchar', '=', vals['parent_id_cerchar'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(MechanicalCercharLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class AercharAbrasivityLine(models.Model):
    _name = "cerchar.abrasivity.line"
    parent_id = fields.Many2one('mechanical.rock',string="Parent Id",ondelete='cascade')

    serial_no = fields.Integer(string="SR NO",readonly=True, copy=False, default=1)
    is_checked = fields.Boolean(
        string="Calculated",
        default=False
    )
    start_date = fields.Date(string="Start Date")  # manually fill
    end_date = fields.Date(string="End Date")      # auto fill on submit

    

    def action_submit(self):
        self.ensure_one()
        
        # Boolean True save
        self.write({
            'is_checked': True,
            'end_date': fields.Date.context_today(self),  # current date auto fill
        })
        
        # Close inline editor → Save-like back
        return {'type': 'ir.actions.act_window_close'}

    lab_id=  fields.Char(string="Lab ID" )

    bh_id = fields.Char(
        string="BH ID",
        compute="_compute_triaxial",
        store=True
    )

    depth = fields.Char(
        string="Depth (m)",
        compute="_compute_triaxial",
        store=True
    )

    
    @api.depends('lab_id')
    def _compute_triaxial(self):
        ReviewLine = self.env['sample.request.review.lines']

        for line in self:
            line.bh_id = False
            line.depth = False

            if not line.lab_id:
                continue

            review_line = ReviewLine.search(
                [('lab_id', '=', line.lab_id)],
                order='id desc',
                limit=1
            )

            if review_line:
                line.bh_id = review_line.source       
                line.depth = review_line.depth        


    cerchar_abrasivity_lines = fields.One2many('mechanical.cerchar.line','parent_id_cerchar',string="Parameter",default=lambda self: self._default_cerchar_abrasivity_lines())

    @api.model
    def _default_cerchar_abrasivity_lines(self):
        default_lines = [
            (0, 0, {'d_mm': 'd1'}),
            (0, 0, {'d_mm': 'd2 '}),
            (0, 0, {'d_mm': 'd3'}),
            (0, 0, {'d_mm': 'd4'}),
        ]
        return default_lines

    classification = fields.Selection(
    [
        ('very_low', 'Very Low Abrasiveness'),
        ('low', 'Low Abrasiveness'),
        ('medium', 'Medium Abrasiveness'),
        ('high', 'High Abrasiveness'),
        ('extreme', 'Extreme Abrasiveness'),
        ('quartzite', 'Quartzite'),
    ],
    string="CAI Classification",
    compute="_compute_classification",
    store=True
)
    

    @api.depends('cai_prime')
    def _compute_classification(self):
     for rec in self:
        cai_prime = rec.cai_prime or 0.0

        if cai_prime >= 6.0:
            rec.classification = 'quartzite'
        elif cai_prime >= 4.0:
            rec.classification = 'extreme'
        elif cai_prime >= 2.0:
            rec.classification = 'high'
        elif cai_prime >= 1.0:
            rec.classification = 'medium'
        elif cai_prime >= 0.5:
            rec.classification = 'low'
        elif cai_prime >= 0.3:
            rec.classification = 'very_low'
        else:
            rec.classification = False


    # point_load = fields.Selection([
    # ('Core', 'Core'),
    # ('Lump', 'Lump'),], string="Point Load Core/Lump")

    avg_pin_result = fields.Float(
        string="Average Pin 1 Result",
        digits=(16, 4),
        compute="_compute_avg_pin_result",
        store=True
    )

    @api.depends('cerchar_abrasivity_lines.pin_result')
    def _compute_avg_pin_result(self):
        for rec in self:
            values = rec.cerchar_abrasivity_lines.mapped('pin_result')
            values = [v for v in values if v]  # remove 0 / False

            if values:
                rec.avg_pin_result = sum(values) / len(values)
            else:
                rec.avg_pin_result = 0.0

    avg_pin2_result = fields.Float(
        string="Average Pin 2 Result",
        digits=(16, 4),
        compute="_compute_avg_pin2_result",
        store=True
    )

    @api.depends('cerchar_abrasivity_lines.pin2result')
    def _compute_avg_pin2_result(self):
        for rec in self:
            values = rec.cerchar_abrasivity_lines.mapped('pin2result')
            values = [v for v in values if v]  # remove 0 / False

            if values:
                rec.avg_pin2_result = sum(values) / len(values)
            else:
                rec.avg_pin2_result = 0.0

    avg_pin3_result = fields.Float(
        string="Average Pin 3 Result",
        digits=(16, 4),
        compute="_compute_avg_pin3_result",
        store=True
    )

    @api.depends('cerchar_abrasivity_lines.pin3result')
    def _compute_avg_pin3_result(self):
        for rec in self:
            values = rec.cerchar_abrasivity_lines.mapped('pin3result')
            values = [v for v in values if v]  # remove 0 / False

            if values:
                rec.avg_pin3_result = sum(values) / len(values)
            else:
                rec.avg_pin3_result = 0.0

    avg_pin4_result = fields.Float(
        string="Average Pin 4 Result",
        digits=(16, 4),
        compute="_compute_avg_pin4_result",
        store=True
    )

    @api.depends('cerchar_abrasivity_lines.pin4result')
    def _compute_avg_pin4_result(self):
        for rec in self:
            values = rec.cerchar_abrasivity_lines.mapped('pin4result')
            values = [v for v in values if v]  # remove 0 / False

            if values:
                rec.avg_pin4_result = sum(values) / len(values)
            else:
                rec.avg_pin4_result = 0.0

    avg_pin5_result = fields.Float(
        string="Average Pin 5 Result",
        digits=(16, 4),
        compute="_compute_avg_pin5_result",
        store=True
    )

    @api.depends('cerchar_abrasivity_lines.pin5result')
    def _compute_avg_pin5_result(self):
        for rec in self:
            values = rec.cerchar_abrasivity_lines.mapped('pin5result')
            values = [v for v in values if v]  # remove 0 / False

            if values:
                rec.avg_pin5_result = sum(values) / len(values)
            else:
                rec.avg_pin5_result = 0.0

    overall_avg_pin_result = fields.Float(
    string="Mean Pin wear (mm)",
    digits=(16, 10),
    compute="_compute_overall_avg_pin_result",
    store=True
   )




    @api.depends(
    'avg_pin_result',
    'avg_pin2_result',
    'avg_pin3_result',
    'avg_pin4_result',
    'avg_pin5_result'
    )
    def _compute_overall_avg_pin_result(self):
        for rec in self:
            values = [
                rec.avg_pin_result,
                rec.avg_pin2_result,
                rec.avg_pin3_result,
                rec.avg_pin4_result,
                rec.avg_pin5_result,
            ]

            # remove 0 / False / None (Excel AVERAGE sarkha)
            values = [v for v in values if v]

            if values:
                rec.overall_avg_pin_result = sum(values) / len(values)
            else:
                rec.overall_avg_pin_result = 0.0


    cai = fields.Float(
    string="CERCHAR Abrasivity Index (CAI) (a x 10)",
    digits=(16, 2),
    compute="_compute_cai",
    store=True
)
    
    @api.depends('overall_avg_pin_result')
    def _compute_cai(self):
     for rec in self:
        rec.cai = (rec.overall_avg_pin_result or 0.0) * 10

    hrc_1 = fields.Float(string="HRC 1", digits=(16, 2) ,default=(55.3))
    hrc_2 = fields.Float(string="HRC 2", digits=(16, 2) ,default=(55.7))
    hrc_3 = fields.Float(string="HRC 3", digits=(16, 2) ,default=(55.5))
    hrc_4 = fields.Float(string="HRC 4", digits=(16, 2) ,default=(55.9))
    hrc_5 = fields.Float(string="HRC 5", digits=(16, 2) ,default=(55.3)) 

    avg_hrc = fields.Float(
    string="Average HRC",
    digits=(16, 2),
    compute="_compute_avg_hrc",
    store=True
)

    @api.depends('hrc_1', 'hrc_2', 'hrc_3', 'hrc_4', 'hrc_5')
    def _compute_avg_hrc(self):
     for rec in self:
        values = [
            rec.hrc_1 or 0.0,
            rec.hrc_2 or 0.0,
            rec.hrc_3 or 0.0,
            rec.hrc_4 or 0.0,
            rec.hrc_5 or 0.0,
        ]

        # Count only filled values
        filled_values = [v for v in values if v > 0]

        if filled_values:
            rec.avg_hrc = round(sum(filled_values) / len(filled_values), 2)
        else:
            rec.avg_hrc = 0.0

    

    cai_prime = fields.Float(
    string="CAI'",
    digits=(16, 2),
    compute="_compute_cai_prime",
    
)
    
    @api.depends('cai', 'avg_hrc')
    def _compute_cai_prime(self):
     for rec in self:
        if rec.avg_hrc:
            rec.cai_prime = (0.415 * rec.cai) / (1 - (0.0107 * rec.avg_hrc))
        else:
            rec.cai_prime = 0.0

        
    

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(AercharAbrasivityLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1





# MODULUS OF ELASTICITY AND POISSON'S RATIO OF ROCK  


# class StressStrain(models.Model):
#     _name = "stress.strain"
#     _description = "Stress Strain"

#     line_ids = fields.One2many(
#         "stress.strain.line",
#         "parent_id",
#         string="Stress Strain Data"
#     )

#     stress_range = fields.Float(
#         string="Stress Range (MPa)",
#         compute="_compute_values",
#         store=True
#     )

#     modulus_e = fields.Float(
#         string="Modulus, E (GPa)",
#         compute="_compute_values",
#         store=True
#     )

#     poisson_ratio = fields.Float(string="Poisson Ratio")
#     graph_image = fields.Binary(string="Graph")

   
#     @api.depends("line_ids.stress", "line_ids.strain")
#     def _compute_values(self):
#         for rec in self:

#             valid_lines = rec.line_ids.filtered(
#                 lambda l: l.stress and l.strain
#             )

#             if len(valid_lines) < 2:
#                 rec.stress_range = 0
#                 rec.modulus_e = 0
#                 continue

#             strain = np.array([l.strain for l in valid_lines])
#             stress = np.array([l.stress for l in valid_lines])

#             rec.stress_range = float(max(stress) - min(stress))

#             slope, intercept = np.polyfit(strain, stress, 1)
#             rec.modulus_e = float(slope / 1000)

    
#     def action_generate_graph(self):
#         for rec in self:

#             valid_lines = rec.line_ids.filtered(
#                 lambda l: l.stress and l.strain
#             )

#             if len(valid_lines) < 2:
#                 rec.graph_image = False
#                 continue

#             strain = np.array([l.strain for l in valid_lines])
#             stress = np.array([l.stress for l in valid_lines])

#             slope, intercept = np.polyfit(strain, stress, 1)
#             x_line = np.linspace(min(strain), max(strain), 100)
#             y_line = slope * x_line + intercept

#             plt.figure(figsize=(6, 4))
#             plt.plot(strain, stress, marker="o")
#             plt.plot(x_line, y_line, linestyle="--")
#             plt.xlabel("Strain")
#             plt.ylabel("Stress (MPa)")
#             plt.grid(True)

#             buffer = io.BytesIO()
#             plt.tight_layout()
#             plt.savefig(buffer, format="png", dpi=150)
#             plt.close()

#             rec.graph_image = base64.b64encode(buffer.getvalue())

















    


class MechanicalSlakeLine(models.Model):
    _name = "mechanical.slake.line"
    parent_id = fields.Many2one('mechanical.rock',string="Parent Id")

    # blue_input = fields.Boolean(default=True,invisible=True)
   
    sr_no = fields.Integer(string="Sr NO.", readonly=True, copy=False, default=1)
    
    lab_id = fields.Char(string="Lab ID") 
    date = fields.Date(string="Date")

    bh_no = fields.Char(string="BH No./Location",digits=(16, 3))
    
    room_temp = fields.Float(string="Room Temperature")
    relative_humidity = fields.Float(string="Relative humidity",digits=(16, 2))
    water_temperature = fields.Float(string="Water temperature",digits=(16, 2))

    wt_drum_a = fields.Float(string="Weight of drum plus sample after drying before initiation of test, (gm), A",digits=(16, 2))
    wt_drum_b = fields.Float(string="Weight of drum plus retained portion of the sample (first cycle), (gm), B",digits=(16, 2))
    wt_drum_c = fields.Float(string=" Weight of drum plus retained portion of the sample (second cycle), (gm), C",digits=(16, 2))
    wt_drum_d = fields.Float(string="Weight of drum after cleaning, (gm), D",digits=(16, 2),)
    slake_second = fields.Float(string=" Slake durability Index percent (second cycle) = (C-D)/(A-D)*100",digits=(16, 2),compute="_compute_slake_index",store=True)
    slake_first = fields.Float(string=" Slake durability Index percent (First cycle) = (B-D)/(A-D)*100",digits=(16, 2),compute="_compute_slake_index",store=True
    )

    classification1 = fields.Selection(
    [
        ('very_low', 'VERY LOW'),
        ('low', 'LOW'),
        ('medium', 'MEDIUM'),
        ('high', 'HIGH'),
        ('very_high', 'VERY HIGH'),
        ('extremely_high', 'EXTREMELY HIGH'),
    ],
    string="Classification",
    compute="_compute_classification1",
    store=True
)
    

    @api.depends('slake_second')
    def _compute_classification1(self):
     for rec in self:
        val = rec.slake_second or 0.0

        if val <= 25:
            rec.classification1 = 'very_low'
        elif val <= 50:
            rec.classification1 = 'low'
        elif val <= 75:
            rec.classification1 = 'medium'
        elif val <= 90:
            rec.classification1 = 'high'
        elif val <= 95:
            rec.classification1 = 'very_high'
        else:
            rec.classification1 = 'extremely_high'

   
    @api.depends(
    'wt_drum_a',
    'wt_drum_b',
    'wt_drum_c',
    'wt_drum_d'
    )
    def _compute_slake_index(self):
        for rec in self:
            rec.slake_second = 0.0
            rec.slake_first = 0.0

            if rec.wt_drum_a is None or rec.wt_drum_d is None:
                continue

            denominator = rec.wt_drum_a - rec.wt_drum_d

            if denominator == 0:
                continue

            # Second cycle
            if rec.wt_drum_c is not None:
                rec.slake_second = round(
                    ((rec.wt_drum_c - rec.wt_drum_d) / denominator) * 100,
                    1
                )

            # First cycle condition
            if rec.slake_second < 10 and rec.wt_drum_b is not None:
                rec.slake_first = round(
                    ((rec.wt_drum_b - rec.wt_drum_d) / denominator) * 100,
                    1
                )



 

          





    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(MechanicalSlakeLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1



class MechanicalTriaxialLine(models.Model):
    _name = "mechanical.triaxial.line"
    parent_id_triaxial = fields.Many2one('triaxial.line',string="Parent Id")

    # blue_input = fields.Boolean(default=True,invisible=True)
   
    sr_no = fields.Integer(string="Number of Specimen Tested.", readonly=True, copy=False, default=1)
    
   

  
    
    

    con_pressure = fields.Float(string="Confining Pressure S3 # MPa",digits=(16, 2))
    failure_load = fields.Float(string="Failure Load kN",digits=(16, 2))
    duration_test = fields.Float(string=" Duration of test  sec",digits=(16, 2))
    height = fields.Float(string="Height of Sample mm",digits=(16, 2),)
    area = fields.Float(string=" Area mm2",digits=(16, 1),compute="_compute_area",store=True)
    axial = fields.Float(string=" Axial Strength MPa",digits=(16, 2), compute="_compute_axial_strength",store=True)
    stress = fields.Float(string=" Stress rate MPa/sec",digits=(16, 1),compute="_compute_stress_rate",store=True )

    # 🔹 Compute Area = π/4 × d²
    # @api.depends('parent_id_triaxial.dia_spe')
    # def _compute_area(self):
    #     for rec in self:
    #         dia = rec.parent_id_triaxial.dia_spe
    #         if dia and dia > 0:
    #             rec.area = (math.pi / 4.0) * (dia ** 2)
    #         else:
    #             rec.area = 0.0

    @api.depends('parent_id_triaxial.dia_spe')
    def _compute_area(self):
 
     for rec in self:

        rec.area = 0.0

        dia = rec.parent_id_triaxial.dia_spe or 0.0

        if dia > 0:

            PI = 3.14

            rec.area = (
                PI
                * 0.25
                * (dia ** 2)
            )

    @api.depends('failure_load', 'area')
    def _compute_axial_strength(self):
        for rec in self:
            rec.axial = 0.0

            if rec.failure_load is None or rec.area in (None, 0):
                continue

            # failure_load in kN → convert to N (*1000)
            rec.axial = (rec.failure_load * 1000) / rec.area

    @api.depends('axial', 'duration_test')
    def _compute_stress_rate(self):
        for rec in self:
            rec.stress = 0.0

            # safety checks
            if rec.axial is None or rec.duration_test in (None, 0):
                continue

            rec.stress = rec.axial / rec.duration_test

    



   

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id_triaxial'):
            existing_records = self.search([('parent_id_triaxial', '=', vals['parent_id_triaxial'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(MechanicalTriaxialLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1

class TriaxialLine(models.Model):
    _name = "triaxial.line"
    parent_id = fields.Many2one('mechanical.rock',string="Parent Id",ondelete='cascade')

    serial_no = fields.Integer(string="SR NO",readonly=True, copy=False, default=1)
    is_checked = fields.Boolean(
        string="Calculated",
        default=False
    )
    start_date = fields.Date(string="Start Date")  # manually fill
    end_date = fields.Date(string="End Date")      # auto fill on submit

    

    def action_submit(self):
        self.ensure_one()
        
        # Boolean True save
        self.write({
            'is_checked': True,
            'end_date': fields.Date.context_today(self),  # current date auto fill
        })
        
        # Close inline editor → Save-like back
        return {'type': 'ir.actions.act_window_close'}

    lab_id=  fields.Char(string="Lab ID" )

    bh_id = fields.Char(
        string="BH ID",
        compute="_compute_triaxial",
        store=True
    )

    depth = fields.Char(
        string="Depth (m)",
        compute="_compute_triaxial",
        store=True
    )

    
    @api.depends('lab_id')
    def _compute_triaxial(self):
        ReviewLine = self.env['sample.request.review.lines']

        for line in self:
            line.bh_id = False
            line.depth = False

            if not line.lab_id:
                continue

            review_line = ReviewLine.search(
                [('lab_id', '=', line.lab_id)],
                order='id desc',
                limit=1
            )

            if review_line:
                line.bh_id = review_line.source        # BH ID / Location
                line.depth = review_line.depth         # Depth (m)

    triaxial_child_lines = fields.One2many('mechanical.triaxial.line','parent_id_triaxial',string="Parameter")

    room_temp_triaxial = fields.Float(string="Room Temperature")
    relative_humidity_triaxial = fields.Float(string="Relative humidity",digits=(16, 2))
    lithologic_dic = fields.Char(string="Lithologic description of rock")
    machine_used = fields.Char(string="Type of machine used")

    dia_spe = fields.Float(string="Diameter of Specimen, mm ")
    initial_wt = fields.Float(string="Initial Weight of Sample (gm)   ")
    area_spe = fields.Float(string="Area of Specimen, cm2 ",compute="_compute_area_spe",store=True,digits=(16, 2))

    @api.depends('dia_spe')
    def _compute_area_spe(self):
        for rec in self:
            if rec.dia_spe and rec.dia_spe > 0:
                rec.area_spe = (math.pi / 4.0) * (rec.dia_spe ** 2) / 100.0
            else:
                rec.area_spe = 0.0

    dry_et = fields.Float(string="Dry Weight of Sample (gm) ")
    moisture_content = fields.Float(string="Moisture content (%)",compute="_compute_moisture_content", store=True,digits=(16, 2))

    tangent_staright = fields.Float(string="Tangent of straight line (m) :",compute="_compute_triaxial_line_constants",store=True)
    intercept_staright = fields.Float(string="Intercept of straight line (b) :",compute="_compute_triaxial_line_constants",store=True)

    phi = fields.Float(string="Angle of internal friction, f",compute="_compute_phi_cohesion",store=True,digits=(12,1))
    cohesion = fields.Float(string="Apparent Cohesion, c",compute="_compute_phi_cohesion",store=True,digits=(12,1))

    @api.depends('tangent_staright', 'intercept_staright')
    def _compute_phi_cohesion(self):
        for rec in self:
            rec.phi = 0.0
            rec.cohesion = 0.0

            m = rec.tangent_staright
            b = rec.intercept_staright

            # safety checks
            if m is None or b is None:
                continue
            if (m + 1) == 0:
                continue

            # ---- φ calculation ----
            value = (m - 1) / (m + 1)

            # ASIN domain must be [-1, 1]
            if value < -1 or value > 1:
                continue

            phi_rad = math.asin(value)          # radians
            phi_deg = math.degrees(phi_rad)     # convert to degrees

            rec.phi = phi_deg

            # ---- cohesion calculation ----
            sin_phi = math.sin(phi_rad)
            cos_phi = math.cos(phi_rad)

            if cos_phi == 0:
                continue

            rec.cohesion = b * ((1 - sin_phi) / (2 * cos_phi))


    @api.depends(
    'triaxial_child_lines.con_pressure',
    'triaxial_child_lines.axial'
    )
    def _compute_triaxial_line_constants(self):
        for rec in self:
            rec.tangent_staright = 0.0
            rec.intercept_staright = 0.0

            lines = rec.triaxial_child_lines.filtered(
                lambda l: l.con_pressure is not None and l.axial is not None
            )

            # Excel SLOPE needs minimum 2 points
            if len(lines) < 2:
                continue

            x = np.array([l.con_pressure for l in lines])
            y = np.array([l.axial for l in lines])

            # y = mx + b
            m, b = np.polyfit(x, y, 1)

            rec.tangent_staright = m
            rec.intercept_staright = b

        

    @api.depends('initial_wt', 'dry_et')
    def _compute_moisture_content(self):
        for rec in self:
            rec.moisture_content = 0.0

            # safety checks
            if rec.initial_wt is None or rec.dry_et in (None, 0):
                continue

            rec.moisture_content = (
                (rec.initial_wt - rec.dry_et) / rec.dry_et
            ) * 100


   
    triaxial_graph = fields.Binary(string="Triaxial Graph")



#     def action_generate_triaxial_graph(self):
#      import numpy as np
#      import matplotlib
#      matplotlib.use('Agg')
#      import matplotlib.pyplot as plt
#      import base64
#      import io

#      for rec in self:
#         lines = rec.triaxial_child_lines.filtered(
#             lambda l: l.con_pressure and l.axial
#         )

#         if not lines:
#             rec.triaxial_graph = False
#             continue

#         # -----------------------------
#         # Data
#         # -----------------------------
#         x = np.array([l.con_pressure for l in lines], float)
#         y = np.array([l.axial for l in lines], float)

#         # -----------------------------
#         # Linear regression
#         # -----------------------------
#         m, c = np.polyfit(x, y, 1)

#         # Use real X values so line passes through points
#         # Line THROUGH actual points
#         order = np.argsort(x)
#         x_line = x[order]
#         y_line = y[order]

#         # -----------------------------
#         # Figure
#         # -----------------------------
#         fig, ax = plt.subplots(figsize=(10, 5), dpi=100)

#         excel_blue = '#4472C4'

#         # Scatter points
#         ax.scatter(x, y, color=excel_blue, s=60, zorder=3)

#         # Dotted regression line (Excel style)
#         ax.plot(
#             x_line,
#             y_line,
#             linestyle=(0, (1, 2)),
#             linewidth=3.5,
#             color=excel_blue,
#             solid_capstyle='round'
#         )

#         # Labels
#         ax.set_xlabel("Confining Pressure (MPa)")
#         ax.set_ylabel("Axial Strength (MPa)")

#         # -----------------------------
#         # Auto Y scaling (tight)
#         # -----------------------------
#         y_pad = (max(y) - min(y)) * 0.15 if max(y) != min(y) else 1
#         ax.set_ylim(min(y) - y_pad, max(y) + y_pad)

#         # -----------------------------
#         # Grid
#         # -----------------------------
#         ax.grid(True, linewidth=0.8, alpha=0.7)

#         # Dark borders
#         for spine in ax.spines.values():
#             spine.set_linewidth(1.2)

#         # -----------------------------
#         # Equation ON the line
#         # -----------------------------
#         x_eq = np.mean(x)
#         y_eq = m * x_eq + c

#         eq = f"y = {m:.3f}x + {c:.3f}"

#         ax.text(
#     x_eq,
#     y_eq + y_pad * 0.9,   # small vertical lift
#     eq,
#     fontsize=10,
#     ha='center',
#     va='bottom'
# )

#         # -----------------------------
#         # Export
#         # -----------------------------
#         buf = io.BytesIO()
#         fig.tight_layout()
#         fig.savefig(buf, format='png')
#         plt.close(fig)

#         rec.triaxial_graph = base64.b64encode(buf.getvalue())


    def action_generate_triaxial_graph(self):

     import numpy as np
     import matplotlib
     matplotlib.use('Agg')

     import matplotlib.pyplot as plt
     import base64
     import io

     for rec in self:

        lines = rec.triaxial_child_lines.filtered(
            lambda l: l.con_pressure and l.axial
        )

        if not lines:
            rec.triaxial_graph = False
            continue

        # --------------------------------
        # DATA
        # --------------------------------
        x = np.array(
            [float(l.con_pressure) for l in lines],
            dtype=float
        )

        y = np.array(
            [float(l.axial) for l in lines],
            dtype=float
        )

        # --------------------------------
        # SORT
        # --------------------------------
        order = np.argsort(x)

        x = x[order]
        y = y[order]

        # --------------------------------
        # REGRESSION USING 10 DECIMALS
        # --------------------------------
        x_reg = np.array(
            [round(v, 10) for v in x],
            dtype=float
        )

        y_reg = np.array(
            [round(v, 10) for v in y],
            dtype=float
        )

        m, c = np.polyfit(
            x_reg,
            y_reg,
            1
        )

        # --------------------------------
        # CONNECT ONLY FIRST & LAST POINT
        # --------------------------------
        x_line = np.array([
            x[0],
            x[-1]
        ])

        y_line = np.array([
            y[0],
            y[-1]
        ])

        # --------------------------------
        # FIGURE
        # --------------------------------
        fig, ax = plt.subplots(
            figsize=(10, 5),
            dpi=100
        )

        excel_blue = '#4472C4'

        # --------------------------------
        # LINE
        # --------------------------------
        ax.plot(
            x_line,
            y_line,
            linestyle=':',
            linewidth=3,
            color=excel_blue
        )

        # --------------------------------
        # POINTS
        # --------------------------------
        ax.scatter(
            x,
            y,
            color=excel_blue,
            s=70,
            zorder=3
        )

        # --------------------------------
        # LABELS
        # --------------------------------
        ax.set_xlabel(
            "Confining Pressure (MPa)",
            fontsize=12
        )

        ax.set_ylabel(
            "Axial Strength (MPa)",
            fontsize=12
        )

        # --------------------------------
        # AXIS LIMITS
        # --------------------------------
        ax.set_xlim(0, 4.5)
        ax.set_ylim(0, 100)

        # --------------------------------
        # GRID
        # --------------------------------
        ax.grid(
            True,
            linewidth=0.8,
            alpha=0.7
        )

        # --------------------------------
        # BORDERS
        # --------------------------------
        for spine in ax.spines.values():

            spine.set_linewidth(1.2)

        # --------------------------------
        # EQUATION
        # --------------------------------
        eq = (
            f"y = {m:.4f}x + {c:.3f}"
        )

        ax.text(
            2.8,
            48,
            eq,
            fontsize=10,
            fontweight='bold',
            bbox=dict(
                facecolor='white',
                edgecolor='none',
                alpha=0.8
            )
        )

        # --------------------------------
        # EXPORT
        # --------------------------------
        buf = io.BytesIO()

        fig.tight_layout()

        fig.savefig(
            buf,
            format='png',
            bbox_inches='tight',
            facecolor='white'
        )

        plt.close(fig)

        rec.triaxial_graph = base64.b64encode(
            buf.getvalue()
        )


           


    

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(TriaxialLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1

class MechanicalElasticityLine(models.Model):
    _name = "mechanical.elasticity.line"
    parent_id_elasticity = fields.Many2one('elasticity.line',string="Parent Id")

    # blue_input = fields.Boolean(default=True,invisible=True)
   
    sr_no = fields.Integer(string="Sr No.", readonly=True, copy=False, default=1)
    
   

    stress = fields.Float(string="Stress (MPa)",digits=(16, 2))
    strain = fields.Float(string="Strain",digits=(16, 6))

    
    


   

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id_elasticity'):
            existing_records = self.search([('parent_id_elasticity', '=', vals['parent_id_elasticity'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(MechanicalElasticityLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1

class ElasticityLine(models.Model):
    _name = "elasticity.line"
    parent_id = fields.Many2one('mechanical.rock',string="Parent Id",ondelete='cascade')

    serial_no = fields.Integer(string="SR NO",readonly=True, copy=False, default=1)
    is_checked = fields.Boolean(
        string="Calculated",
        default=False
    )
    start_date = fields.Date(string="Start Date")  # manually fill
    end_date = fields.Date(string="End Date")      # auto fill on submit

    

    def action_submit(self):
        self.ensure_one()
        
        # Boolean True save
        self.write({
            'is_checked': True,
            'end_date': fields.Date.context_today(self),  # current date auto fill
        })
        
        # Close inline editor → Save-like back
        return {'type': 'ir.actions.act_window_close'}

    lab_id=  fields.Char(string="Lab ID" )

    bh_id = fields.Char(
        string="BH ID",
        compute="_compute_triaxial",
        store=True
    )

    depth = fields.Char(
        string="Depth (m)",
        compute="_compute_triaxial",
        store=True
    )

    
    @api.depends('lab_id')
    def _compute_triaxial(self):
        ReviewLine = self.env['sample.request.review.lines']

        for line in self:
            line.bh_id = False
            line.depth = False

            if not line.lab_id:
                continue

            review_line = ReviewLine.search(
                [('lab_id', '=', line.lab_id)],
                order='id desc',
                limit=1
            )

            if review_line:
                line.bh_id = review_line.source        # BH ID / Location
                line.depth = review_line.depth         # Depth (m)

    rock_line_id = fields.Many2one(
    'mechanical.rock.line',
    compute="_compute_rock_line",
    store=True
)

    @api.depends('lab_id')
    def _compute_rock_line(self):

     for rec in self:

        rec.rock_line_id = False

        if rec.lab_id:

            rock_line = self.env[
                'mechanical.rock.line'
            ].search([
                ('lab_id', '=', rec.lab_id)
            ], limit=1)

            rec.rock_line_id = rock_line.id 
    
    elasticity_child_lines = fields.One2many('mechanical.elasticity.line','parent_id_elasticity',string="Parameter")

    elasticity_graph = fields.Binary("Stress-Strain Graph")

    # def action_generate_graph(self):
    #     for record in self:

    #         x_vals = []
    #         y_vals = []

    #         for line in record.elasticity_child_lines:
    #             if line.strain and line.stress:
    #                 x_vals.append(line.strain)
    #                 y_vals.append(line.stress)

    #         if not x_vals:
    #             return

    #         plt.figure()
    #         plt.plot(x_vals, y_vals, marker='o')
    #         plt.xlabel("Strain")
    #         plt.ylabel("Stress (mPa)")
    #         plt.title("Stress vs Strain")
    #         plt.grid(True)

    #         buffer = BytesIO()
    #         plt.savefig(buffer, format='png')
    #         plt.close()

    #         record.elasticity_graph = base64.b64encode(buffer.getvalue())

    def action_generate_graph(self):
        for record in self:

            x_vals = []
            y_vals = []

            # 👉 Collect Data
            for line in record.elasticity_child_lines:
                if line.strain is not None and line.stress is not None:
                    x_vals.append(line.strain)
                    y_vals.append(line.stress)

            # 👉 If no data, skip
            if not x_vals or not y_vals:
                record.elasticity_graph = False
                continue

            # 👉 Create Plot
            plt.figure()

            plt.plot(x_vals, y_vals, marker='o', linestyle='-')

            plt.xlabel("Strain")
            plt.ylabel("Stress (mPa)")
            plt.title("Stress vs Strain")

            # 👉 FORCE START FROM ZERO
            plt.xlim(0, max(x_vals) * 1.1)
            plt.ylim(0, max(y_vals) * 1.1)

            plt.grid(True)

            # 👉 Save Image
            buffer = BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight')
            plt.close()

            # 👉 Store in Binary Field
            record.elasticity_graph = base64.b64encode(buffer.getvalue())

    room_temp_elasticity = fields.Float(
        related="rock_line_id.room_temp",
        string="Room Temperature",
        store=True
    )

    relative_humidity_elasticity = fields.Float(
        related="rock_line_id.relative_humidity",
        string="Relative humidity",
        store=True
    )

    lithological = fields.Char(
        related="rock_line_id.lithological",
        string="Lithologic description of rock",
        store=True
    )

    avg_dia = fields.Float(
        related="rock_line_id.avg_dia",
        string="Average Diameter (D)",
        store=True
    )

    avg_height = fields.Float(
        related="rock_line_id.avg_height",
        string="Average Height (H)",
        store=True
    )

    hd = fields.Float(
        related="rock_line_id.hd",
        string="H/D",
        store=True
    )

    bulk_density = fields.Float(
        related="rock_line_id.bulk_density",
        string="Bulk Density",
        store=True
    )

    sat_density = fields.Float(
        related="rock_line_id.sat_density",
        string="Sat Density",
        store=True
    )

    dry_density = fields.Float(
        related="rock_line_id.dry_density",
        string="Dry Density",
        store=True
    )

    water_absorption = fields.Float(
        related="rock_line_id.water_absorption",
        string="Water Absorption",
        store=True
    )

    sp_gravity = fields.Float(
        related="rock_line_id.sp_gravity",
        string="Sp. Gravity",
        store=True
    )

    porosity = fields.Float(
        related="rock_line_id.porosity",
        string="Porosity",
        store=True
    )

    moisture_content = fields.Float(
        related="rock_line_id.moisture_content",
        string="Water Content",
        store=True
    )

    duration_of_test = fields.Float(
        related="rock_line_id.duration_of_test",
        string="Duration of test",
        store=True
    )

    stress_rate = fields.Float(
        related="rock_line_id.stress_rate",
        string="Stress Rate",
        store=True
    )

    comp_strength1 = fields.Float(
        related="rock_line_id.comp_strength1",
        string="Compressive Strength qc",
        store=True
    )

    comp_strength2 = fields.Float(
        related="rock_line_id.comp_strength2",
        string="Compressive Strength qc at H/D=2",
        store=True
    )

    mode_of_failure = fields.Char(
        related="rock_line_id.mode_of_failure",
        string="Mode of failure",
        store=True
    )

    stress_range = fields.Float(
    string="Stress Range (MPa)",
    digits=(16, 2)
)

    modulus_e = fields.Float(
    string="Modulus, E (GPa)",
    digits=(16, 2)
)

    poissons_ratio = fields.Float(
    string="Poissons Ratio, μ",
    digits=(16, 2)
)

    machine_used = fields.Char(string="Type of Sample & Condition")

    lithologic_dic = fields.Char(string="Lithologic description of rock")

    avg_dia = fields.Float(string="Average Diameter (D) mm",)
    avg_height = fields.Float(string="Average Height (H) mm",)
    hd = fields.Float(string="H/D",digits=(16, 2),store=True)

    bulk_density = fields.Float(string="Bulk Density g/cc",digits=(16, 2),store=True)
    sat_density = fields.Float(string="Sat Density g/cc",digits=(16, 2),store=True)
    dry_density = fields.Float(string="Dry Density g/cc",digits=(16, 2),store=True,)
    water_absorption = fields.Float(string="Water Absorption %",digits=(16, 2))

    room_temp_elasticity = fields.Float(string="Room Temperature")
    relative_humidity_elasticity = fields.Float(string="Relative humidity",digits=(16, 2))
    
    machine_used = fields.Char(string="Type of Sample & Condition")


    sp_gravity = fields.Float(string="Sp. Gravity",digits=(16, 2),store=True)
    
    porosity = fields.Float(string="Porosity",digits=(16, 2),store=True)
    water_content = fields.Float(string="Water Content",digits=(16, 2))

    duration_of_test = fields.Float(string="Duration of the test (Sec)",digits=(16, 2))
    stress_rate = fields.Float(string="Stress Rate",digits=(16, 2),store=True)
    mode_of_failure = fields.Char(string="Mode of failure",digits=(16, 2))


    comp_strength1 = fields.Float(string="Compressive Strength qc ",digits=(16, 2),store=True)
    comp_strength2 = fields.Float(string="Compressive Strength  qc at H/D=2",digits=(16, 2),store=True)
    

    


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(ElasticityLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1

    

class TensileStrengthLine(models.Model):
    _name = "rock.tensile.strength.line"
    parent_id = fields.Many2one('mechanical.rock',string="Parent Id",ondelete='cascade')

    serial_no = fields.Integer(string="SR NO",readonly=True, copy=False, default=1)
    is_checked = fields.Boolean(
        string="Calculated",
        default=False
    )
    start_date = fields.Date(string="Start Date")  # manually fill
    end_date = fields.Date(string="End Date")      # auto fill on submit

    

    def action_submit(self):
        self.ensure_one()
        
        # Boolean True save
        self.write({
            'is_checked': True,
            'end_date': fields.Date.context_today(self),  # current date auto fill
        })
        
        # Close inline editor → Save-like back
        return {'type': 'ir.actions.act_window_close'}

    lab_id=  fields.Char(string="Lab ID" )

    bh_id = fields.Char(
        string="BH ID",
        compute="_compute_tensile_strength",
        store=True
    )

    depth = fields.Char(
        string="Depth (m)",
        compute="_compute_tensile_strength",
        store=True
    )

    
    @api.depends('lab_id')
    def _compute_tensile_strength(self):
        ReviewLine = self.env['sample.request.review.lines']

        for line in self:
            line.bh_id = False
            line.depth = False

            if not line.lab_id:
                continue

            review_line = ReviewLine.search(
                [('lab_id', '=', line.lab_id)],
                order='id desc',
                limit=1
            )

            if review_line:
                line.bh_id = review_line.source        # BH ID / Location
                line.depth = review_line.depth         # Depth (m)

    tensile_strength_child_lines = fields.One2many('mechanical.tensile.strength.line','parent_id_tensile_strength',string="Parameter")

    avg_room_temp = fields.Float(
    string="Average Room Temperature",
    compute="_compute_tensile_environment_averages",
    store=True,
    digits=(16, 2)
)

    avg_relative_humidity = fields.Float(
    string="Average Relative Humidity",
    compute="_compute_tensile_environment_averages",
    store=True,
    digits=(16, 2)
)

    avg_water_temperature = fields.Float(
    string="Average Water Temperature",
    compute="_compute_tensile_environment_averages",
    store=True,
    digits=(16, 2)
) 

    avg_dia_rock1 = fields.Float(
    string="Average Diameter 1",
    compute="_compute_tensile_environment_averages",
    store=True,
    digits=(16, 2)
)

    avg_dia_rock2 = fields.Float(
    string="Average Diameter 2",
    compute="_compute_tensile_environment_averages",
    store=True,
    digits=(16, 2)
)

    avg_dia_rock3 = fields.Float(
    string="Average Diameter 3",
    compute="_compute_tensile_environment_averages",
    store=True,
    digits=(16, 2)
)

    

    avg_height_rock1 = fields.Float(
    string="Average Height 1",
    compute="_compute_tensile_environment_averages",
    store=True,
    digits=(16, 2)
)

    avg_height_rock2 = fields.Float(
    string="Average Height 2",
    compute="_compute_tensile_environment_averages",
    store=True,
    digits=(16, 2)
)

    avg_height_rock3 = fields.Float(
    string="Average Height 3",
    compute="_compute_tensile_environment_averages",
    store=True,
    digits=(16, 2)
)

   
   

    avg_volume_of_sample = fields.Float(
    string="Average Volume of Sample",
    compute="_compute_tensile_environment_averages",
    store=True,
    digits=(16, 2)
)

    avg_initial_wt = fields.Float(
    string="Average Initial Weight",
    compute="_compute_tensile_environment_averages",
    store=True,
    digits=(16, 2)
)

    avg_dry_wet = fields.Float(
    string="Average Dry Weight",
    compute="_compute_tensile_environment_averages",
    store=True,
    digits=(16, 2)
)

    avg_saturated_wet = fields.Float(
    string="Average Saturated Weight",
    compute="_compute_tensile_environment_averages",
    store=True,
    digits=(16, 2)
)

    

    avg_wt_of_sample = fields.Float(
    string="Average Weight in Water",
    compute="_compute_tensile_environment_averages",
    store=True,
    digits=(16, 2)
)

   

    avg_load_ucs = fields.Float(
    string="Average Load UCS",
    compute="_compute_tensile_environment_averages",
    store=True,
    digits=(16, 2)
)

    avg_dis_two_loadpoint = fields.Float(
    string="Average Distance",
    compute="_compute_tensile_environment_averages",
    store=True,
    digits=(16, 2)
)

    avg_point_load = fields.Float(
    string="Average Point Load",
    compute="_compute_tensile_environment_averages",
    store=True,
    digits=(16, 2)
)

    avg_duration_of_test = fields.Float(
    string="Average Duration",
    compute="_compute_tensile_environment_averages",
    store=True,
    digits=(16, 2)
)

    avg_tensile_strength = fields.Float(
    string="Average Tensile Strength",
    compute="_compute_tensile_environment_averages",
    store=True,
    digits=(16, 3)
)


    

    



    @api.depends(
    'tensile_strength_child_lines.room_temp',
    'tensile_strength_child_lines.relative_humidity',
    'tensile_strength_child_lines.water_temperature',
    'tensile_strength_child_lines.dia_rock1',
    'tensile_strength_child_lines.dia_rock2',
    'tensile_strength_child_lines.dia_rock3',
    'tensile_strength_child_lines.height_rock1',
    'tensile_strength_child_lines.height_rock2',
    'tensile_strength_child_lines.height_rock3',
    'tensile_strength_child_lines.initial_wt',
    'tensile_strength_child_lines.dry_wet',
    'tensile_strength_child_lines.saturated_wet',
    'tensile_strength_child_lines.wt_of_sample',
    'tensile_strength_child_lines.load_ucs',
    'tensile_strength_child_lines.dis_two_loadpoint',
    'tensile_strength_child_lines.point_load',
    'tensile_strength_child_lines.duration_of_test',
    'tensile_strength_child_lines.volume_of_sample1',
    'tensile_strength_child_lines.tensile_strength',
)
    def _compute_tensile_environment_averages(self):

      def avg(lines, field):
        values = [
            v for v in lines.mapped(field)
            if v not in (False, None)
        ]
        return sum(values) / len(values) if values else 0.0

      for rec in self:

        lines = rec.tensile_strength_child_lines

        rec.avg_room_temp = avg(lines, 'room_temp')
        rec.avg_relative_humidity = avg(lines, 'relative_humidity')
        rec.avg_water_temperature = avg(lines, 'water_temperature')

        rec.avg_dia_rock1 = avg(lines, 'dia_rock1')
        rec.avg_dia_rock2 = avg(lines, 'dia_rock2')
        rec.avg_dia_rock3 = avg(lines, 'dia_rock3')

        rec.avg_volume_of_sample = avg(lines, 'volume_of_sample1')

        rec.avg_height_rock1 = avg(lines, 'height_rock1')
        rec.avg_height_rock2 = avg(lines, 'height_rock2')
        rec.avg_height_rock3 = avg(lines, 'height_rock3')

        rec.avg_initial_wt = avg(lines, 'initial_wt')
        rec.avg_dry_wet = avg(lines, 'dry_wet')
        rec.avg_saturated_wet = avg(lines, 'saturated_wet')
        rec.avg_wt_of_sample = avg(lines, 'wt_of_sample')

        rec.avg_load_ucs = avg(lines, 'load_ucs')
        rec.avg_dis_two_loadpoint = avg(
            lines,
            'dis_two_loadpoint'
        )
        rec.avg_point_load = avg(lines, 'point_load')
        rec.avg_duration_of_test = avg(
            lines,
            'duration_of_test'
        )
        rec.avg_tensile_strength = avg(
                    lines,
                    'tensile_strength'
                )



    avg_diameter = fields.Float(
    string="Average Diameter",
    compute="_compute_tensile_averages",
    store=True,
    digits=(16, 2)
)

    avg_height = fields.Float(
    string="Average Height",
    compute="_compute_tensile_averages",
    store=True,
    digits=(16, 2)
)

    avg_hd = fields.Float(
    string="H/D",
    compute="_compute_tensile_averages",
    store=True,
    digits=(16, 2)
)

    avg_volume_of_void = fields.Float(
    string="Volume of Voids",
    compute="_compute_tensile_averages",
    store=True,
    digits=(16, 2)
)

    avg_sp_gravity = fields.Float(
    string="Sp. Gravity",
    compute="_compute_tensile_averages",
    store=True,
    digits=(16, 2)
)

    avg_bulk_density = fields.Float(
    string="Bulk Density",
    compute="_compute_tensile_averages",
    store=True,
    digits=(16, 2)
)

    avg_sat_density = fields.Float(
    string="Sat Density",
    compute="_compute_tensile_averages",
    store=True,
    digits=(16, 4)
)

    avg_dry_density = fields.Float(
    string="Dry Density",
    compute="_compute_tensile_averages",
    store=True,
    digits=(16, 4)
)

    avg_water_absorption = fields.Float(
    string="Water Absorption",
    compute="_compute_tensile_averages",
    store=True,
    digits=(16, 2)
)

    avg_porosity = fields.Float(
    string="Porosity",
    compute="_compute_tensile_averages",
    store=True,
    digits=(16, 2)
)



    avg_moisture_content = fields.Float(
    string="Moisture Content",
    compute="_compute_tensile_averages",
    store=True,
    digits=(16, 2)
)



    @api.depends(
    'avg_dia_rock1',
    'avg_dia_rock2',
    'avg_dia_rock3',
    'avg_height_rock1',
    'avg_height_rock2',
    'avg_height_rock3',
    'avg_initial_wt',
    'avg_dry_wet',
    'avg_saturated_wet',
    'avg_wt_of_sample',
)
    def _compute_tensile_averages(self):

     for rec in self:

        # ==========================================
        # 1. AVERAGE DIAMETER
        # ==========================================

        diameter_values = [
            rec.avg_dia_rock1,
            rec.avg_dia_rock2,
            rec.avg_dia_rock3,
        ]

        valid_diameters = [
            value for value in diameter_values
            if value not in (False, None, 0)
        ]

        rec.avg_diameter = (
            sum(valid_diameters) / len(valid_diameters)
            if valid_diameters
            else 0.0
        )


        # ==========================================
        # 2. AVERAGE HEIGHT
        # ==========================================

        height_values = [
            rec.avg_height_rock1,
            rec.avg_height_rock2,
            rec.avg_height_rock3,
        ]

        valid_heights = [
            value for value in height_values
            if value not in (False, None, 0)
        ]

        rec.avg_height = (
            sum(valid_heights) / len(valid_heights)
            if valid_heights
            else 0.0
        )


        # ==========================================
        # 3. H/D
        # H/D = Average Height / Average Diameter
        # ==========================================

        if rec.avg_diameter:
            rec.avg_hd = (
                rec.avg_height / rec.avg_diameter
            )
        else:
            rec.avg_hd = 0.0


        # ==========================================
        # 4. VOLUME OF VOIDS
        # Vvoid = Saturated Weight - Dry Weight
        # ==========================================

        if (
            rec.avg_saturated_wet or
            rec.avg_dry_wet
        ):
            rec.avg_volume_of_void = (
                rec.avg_saturated_wet -
                rec.avg_dry_wet
            )
        else:
            rec.avg_volume_of_void = 0.0


        # ==========================================
        # 5. SPECIFIC GRAVITY
        #
        # G = Dry Weight /
        #     ((Saturated Weight - Water Weight)
        #      - Volume of Voids)
        # ==========================================

        denominator = (
            rec.avg_saturated_wet -
            rec.avg_wt_of_sample -
            rec.avg_volume_of_void
        )

        if denominator:
            rec.avg_sp_gravity = (
                rec.avg_dry_wet /
                denominator
            )
        else:
            rec.avg_sp_gravity = 0.0


        # ==========================================
        # VOLUME OF SAMPLE
        #
        # V = Saturated Weight - Weight in Water
        #
        # This is required by density formulas
        # ==========================================

        volume_of_sample = (
            rec.avg_saturated_wet -
            rec.avg_wt_of_sample
        )


        # ==========================================
        # 6. BULK DENSITY
        #
        # Bulk Density = Initial Weight / Volume
        # ==========================================

        if volume_of_sample:
            rec.avg_bulk_density = (
                rec.avg_initial_wt /
                volume_of_sample
            )
        else:
            rec.avg_bulk_density = 0.0


        # ==========================================
        # 7. SATURATED DENSITY
        #
        # Sat Density = Saturated Weight / Volume
        # ==========================================

        if volume_of_sample:
            rec.avg_sat_density = (
                rec.avg_saturated_wet /
                volume_of_sample
            )
        else:
            rec.avg_sat_density = 0.0


        # ==========================================
        # 8. DRY DENSITY
        #
        # Dry Density = Dry Weight / Volume
        # ==========================================

        if volume_of_sample:
            rec.avg_dry_density = (
                rec.avg_dry_wet /
                volume_of_sample
            )
        else:
            rec.avg_dry_density = 0.0


        # ==========================================
        # 9. WATER ABSORPTION
        #
        # ((Sat Density - Dry Density)
        #  / Dry Density) * 100
        # ==========================================

        if rec.avg_dry_density:
            rec.avg_water_absorption = (
                (
                    rec.avg_sat_density -
                    rec.avg_dry_density
                ) /
                rec.avg_dry_density
            ) * 100
        else:
            rec.avg_water_absorption = 0.0


        # ==========================================
        # 10. POROSITY
        #
        # (Sat Density - Dry Density) * 100
        # ==========================================

        if (
            rec.avg_sat_density or
            rec.avg_dry_density
        ):
            rec.avg_porosity = (
                rec.avg_sat_density -
                rec.avg_dry_density
            ) * 100
        else:
            rec.avg_porosity = 0.0


        # ==========================================
        # 11. MOISTURE CONTENT
        #
        # ((Initial Weight - Dry Weight)
        #  / Dry Weight) * 100
        # ==========================================

        if rec.avg_dry_wet:
            rec.avg_moisture_content = (
                (
                    rec.avg_initial_wt -
                    rec.avg_dry_wet
                ) /
                rec.avg_dry_wet
            ) * 100
        else:
            rec.avg_moisture_content = 0.0



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(TensileStrengthLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1



class MechanicalTensileStrengthLine(models.Model):
    _name = "mechanical.tensile.strength.line"
    parent_id_tensile_strength = fields.Many2one('rock.tensile.strength.line',string="Parent Id")
   
    sr_no = fields.Integer(string="Specimen NO.", readonly=True, copy=False, default=1)

    date_received = fields.Date(string="Date of Test Started")
    date_testing = fields.Date(string="Date of Completion")

    lab_id = fields.Char(string="Lab ID") 
    # bh_no = fields.Char(string="BH No./Location",digits=(16, 3))
    # depth = fields.Char(string="Depth")

    piece_no = fields.Char(string="Piece No")
    lithological = fields.Char(string="Lithological Description of rock")
    room_temp = fields.Float(string="Room Temperature")
    relative_humidity = fields.Float(string="Relative humidity %",digits=(16, 2))
    water_temperature = fields.Float(string="Water temperature",digits=(16, 2))

    dia_rock1 = fields.Float(string="Diameter of Rock Sample 1",digits=(16, 2))
    dia_rock2 = fields.Float(string="Diameter of Rock Sample 2",digits=(16, 2))
    dia_rock3 = fields.Float(string="Diameter of Rock Sample 3",digits=(16, 2))
    avg_dia = fields.Float(string="Average Diameter (D)",digits=(16, 13),store=True,compute="_compute_avg_dia")
    height_rock1 = fields.Float(string="Height of Rock Sample 1",digits=(16, 2))
    height_rock2 = fields.Float(string="Height of Rock Sample 2",digits=(16, 2))
    height_rock3 = fields.Float(string="Height of Rock Sample 3",digits=(16, 2))
    avg_height = fields.Float(string="Average Height (H)",digits=(16, 10),store=True,compute="_compute_avg_height")

    hd = fields.Float(string="H/D",digits=(16, 10),store=True,compute="_compute_hd")
    volume_of_sample = fields.Float(string="Volume of Sample(Wsat-Wsub)",digits=(16, 2),store=True,compute="_compute_volume_of_sample")
    volume_of_sample1 = fields.Float(string="Volume of Sample",digits=(16, 2))
    initial_wt = fields.Float(string="Initial Wt of sample",digits=(16, 2))
    dry_wet = fields.Float(string="Dry Wt of sample",digits=(16, 2))
    saturated_wet = fields.Float(string="Saturated Wt of sample",digits=(16, 2))
    volume_of_void = fields.Float(string="Volume of Voids (cm³)",digits=(16, 2),store=True,compute="_compute_volume_of_void")

    wt_of_sample = fields.Float(string="Wt of sample in Water",digits=(16, 2))


    sp_gravity = fields.Float(string="Sp. Gravity",digits=(16, 2),store=True,compute="_compute_sp_gravity")
    bulk_density = fields.Float(string="Bulk Density",digits=(16, 2),store=True,compute="_compute_bulk_density")
    sat_density = fields.Float(string="Sat Density",digits=(16, 4),store=True,compute="_compute_sat_density")
    dry_density = fields.Float(string="Dry Density",digits=(16, 4),store=True,compute="_compute_dry_density")
    water_absorption = fields.Float(string="Water Absorption",digits=(16, 2),store=True,compute="_compute_water_absorption")
    porosity = fields.Float(string="Porosity",digits=(16, 2),store=True,compute="_compute_porosity")

    load_ucs = fields.Float(string="Load (UCS)",digits=(16, 2))
    dis_two_loadpoint = fields.Float(string="Distance between loading points (MUST for Tensile)",digits=(16, 2))
    point_load = fields.Float(string="Point Load",digits=(16, 2))
    duration_of_test = fields.Float(string="Duration of the test (Sec)",digits=(16, 2))
    mode_of_failure = fields.Char(string="Mode of failure",digits=(16, 2))


    tensile_strength = fields.Float(string="Tensile Strength",digits=(16, 2),store=True,compute="_compute_tensile_strength")
    moisture_content = fields.Float(string="Moisture Content %",digits=(16, 2),store=True,compute="_compute_moisture_content")



    @api.depends('dia_rock1', 'dia_rock2', 'dia_rock3')
    def _compute_avg_dia(self):
        for rec in self:
            values = [rec.dia_rock1, rec.dia_rock2, rec.dia_rock3]
            valid_values = [v for v in values if v]  
            rec.avg_dia = sum(valid_values) / len(valid_values) if valid_values else 0.0

    @api.depends('height_rock1', 'height_rock2', 'height_rock3')
    def _compute_avg_height(self):
        for rec in self:
            valuess = [rec.height_rock1, rec.height_rock2, rec.height_rock3]
            valid_valuess = [v for v in valuess if v]  
            rec.avg_height = sum(valid_valuess) / len(valid_valuess) if valid_valuess else 0.0

    @api.depends('avg_height', 'avg_dia')
    def _compute_hd(self):
        for rec in self:
            if rec.avg_dia:
                rec.hd = rec.avg_height / rec.avg_dia
            else:
                rec.hd = 0.0


    # ---- Compute method ----

    @api.depends('saturated_wet', 'wt_of_sample')
    def _compute_volume_of_sample(self):
     for rec in self:
        if rec.saturated_wet or rec.wt_of_sample:
            rec.volume_of_sample = rec.saturated_wet - rec.wt_of_sample
        else:
            rec.volume_of_sample = 0.0
    # @api.depends('saturated_wet', 'wt_of_sample')
    # def _compute_volume_of_sample(self):
    #     for rec in self:
    #         rec.volume_of_sample = rec.saturated_wet - rec.wt_of_sample if rec.saturated_wet and rec.wt_of_sample else 0.0


      # ---- Compute method ----
    @api.depends('saturated_wet', 'dry_wet')
    def _compute_volume_of_void(self):
        for rec in self:
            rec.volume_of_void = rec.saturated_wet - rec.dry_wet if rec.saturated_wet and rec.dry_wet else 0.0

    @api.depends('dry_wet', 'saturated_wet', 'wt_of_sample', 'volume_of_void')
    def _compute_sp_gravity(self):
        for rec in self:
            denominator = (rec.saturated_wet - rec.wt_of_sample) - rec.volume_of_void
            if denominator and denominator != 0:
                rec.sp_gravity = rec.dry_wet / denominator
            else:
                rec.sp_gravity = 0.0

    @api.depends('initial_wt', 'volume_of_sample1')
    def _compute_bulk_density(self):
        for rec in self:
            if rec.volume_of_sample1 and rec.volume_of_sample1 != 0:
                rec.bulk_density = rec.initial_wt / rec.volume_of_sample1
            else:
                rec.bulk_density = 0.0

    @api.depends('saturated_wet', 'volume_of_sample1')
    def _compute_sat_density(self):
        for rec in self:
            if rec.volume_of_sample1 and rec.volume_of_sample1 != 0:
                rec.sat_density = rec.saturated_wet / rec.volume_of_sample1
            else:
                rec.sat_density = 0.0

    @api.depends('dry_wet', 'volume_of_sample1')
    def _compute_dry_density(self):
        for rec in self:
            if rec.volume_of_sample1 and rec.volume_of_sample1 != 0:
                rec.dry_density = rec.dry_wet / rec.volume_of_sample1
            else:
                rec.dry_density = 0.0


    @api.depends('sat_density', 'dry_density')
    def _compute_water_absorption(self):
        for rec in self:
            if rec.dry_density and rec.dry_density != 0:
                # चार दशांश पर्यंत calculation साठी precision control
                sat = float(f"{rec.sat_density:.4f}")
                dry = float(f"{rec.dry_density:.4f}")

                rec.water_absorption = ((sat - dry) / dry) * 100
            else:
                rec.water_absorption = 0.0

    @api.depends('sat_density', 'dry_density')
    def _compute_porosity(self):
        for rec in self:
                rec.porosity = (rec.sat_density - rec.dry_density) * 100


    @api.depends('point_load', 'avg_dia', 'avg_height')
    def _compute_tensile_strength(self):
     for record in self:
        if record.point_load and record.avg_dia and record.avg_height:
            record.tensile_strength = (
                2 * record.point_load * 1000
            ) / (
                math.pi * record.avg_dia * record.avg_height
            )
        else:
            record.tensile_strength = 0.0



    @api.depends('initial_wt', 'dry_wet')
    def _compute_moisture_content(self):
        for rec in self:
            if rec.dry_wet:
                rec.moisture_content = ((rec.initial_wt - rec.dry_wet) / rec.dry_wet) * 100
            else:
                rec.moisture_content = 0.0


    
   

  
    

    



   

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id_tensile_strength'):
            existing_records = self.search([('parent_id_tensile_strength', '=', vals['parent_id_tensile_strength'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(MechanicalTensileStrengthLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


