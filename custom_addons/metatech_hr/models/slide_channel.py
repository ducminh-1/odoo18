from odoo import fields, models, api
from odoo.exceptions import UserError

class SlideChannel(models.Model):
    _inherit = "slide.channel"

    allowed_department_ids = fields.Many2many('hr.department', string="Department")
    job_ids = fields.Many2many('hr.job', string="Job Position")
    sequential_learning = fields.Boolean(string="Sequential Learning")
    date_published = fields.Datetime(string="Published Date", store=True)

    @api.onchange('is_published')
    def _onchange_is_published(self):
        if self.is_published and not self.date_published:
            self.date_published = fields.Datetime.now()
    
    def _auto_set_prerequisites(self):
        for channel in self:
            slides = channel.slide_ids.sorted('sequence')
            previous_slide = False
            for slide in slides:
                if previous_slide:
                    slide.prerequisite_slide_ids = [(6, 0, [previous_slide.id])]
                else:
                    slide.prerequisite_slide_ids = [(5, 0, 0)]
                previous_slide = slide
                
    def _clear_prerequisites(self):
        for channel in self:
            for slide in channel.slide_ids:
                slide.prerequisite_slide_ids = [(5, 0, 0)]

    @api.model
    def write(self, vals):
        if 'is_published' in vals and vals['is_published']:
            if not self.date_published:
                self.date_published = fields.Datetime.now()
        res = super(SlideChannel, self).write(vals)
        if 'sequential_learning' in vals:
            if self.sequential_learning:
                self._auto_set_prerequisites()
            else:
                self._clear_prerequisites()
        return res

        
class SlideSlide(models.Model):
    _inherit = "slide.slide"

    prerequisite_slide_ids = fields.Many2many('slide.slide', 'slide_prerequisite_rel' ,'slide_id', 'prerequisite_slide_id', string="Prerequisites")
    slide_complete = fields.Boolean(compute='_compute_slide_complete')
    # user_has_completed = fields.Boolean('Is Member', compute='_compute_user_membership_id', compute_sudo=False, store=True)
    user_has_complete = fields.Boolean()
    
    @api.depends('prerequisite_slide_ids')
    def _compute_slide_complete(self):
        for slide in self:
            if not slide.prerequisite_slide_ids:
                slide.slide_complete = True
                continue
            prereq_ids = slide.prerequisite_slide_ids.ids
            completed = self.env['slide.slide.partner'].sudo().search_count([
                ('partner_id', '=', self.env.user.partner_id.id),
                ('slide_id.id', 'in', prereq_ids),
                ('completed', '=', True),
            ])
            slide.slide_complete = (completed == len(prereq_ids)) if prereq_ids else False
    


class SlideQuestion(models.Model):
    _inherit = "slide.question"

    answer_id = fields.Many2one('slide.answer', string="Correct Answer")


# class SlideSlidePartner(models.Model):
#     _inherit = 'slide.slide.partner'

#     prerequisite_slide_ids = fields.Many2many(
#         comodel_name='slide.slide',
#         related='slide_id.prerequisite_slide_ids',
#         string="Prerequisite Slides",
#         store=True,   # nếu cần search domain
#         readonly=True,
#     )