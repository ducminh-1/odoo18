from odoo import fields, models, api
from odoo.exceptions import UserError

class SlideChannel(models.Model):
    _inherit = "slide.channel"

    allowed_department_ids = fields.Many2many('hr.department', string="Department")
    job_ids = fields.Many2many('hr.job', string="Job Position",)
    sequential_learning = fields.Boolean(string="Sequential Learning")
    date_published = fields.Datetime(string="Published Date", store=True)


    # @api.onchange('job_ids')
    # def _onchange_job_ids(self):
    #     for record in self:
    #         employees = self.env['hr.employee'].sudo().search([
    #             ('job_id', 'in', record.job_ids.ids)
    #         ])
    #         partners = employees.mapped('user_id.partner_id')
    #         for partner in partners:
    #             existing = self.env['slide.channel.partner'].sudo().search([
    #                 ('channel_id', '=', record.id),
    #                 ('partner_id', '=', partner.id)
    #             ])
    #             if not existing:
    #                 self.env['slide.channel.partner'].sudo().create({
    #                     'channel_id': record.id,
    #                     'partner_id': partner.id,
    #                 })


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

    # answer_id = fields.Many2one('slide.answer', string="Correct Answer")
    is_correct = fields.Boolean()

    text_value = fields.Char("Answer", compute='_compute_text_value')

    @api.depends('answer_ids.is_correct', 'answer_ids.text_value')
    def _compute_text_value(self):
        for question in self:
            correct = question.answer_ids.filtered(lambda a: a.text_value and a.is_correct)
            question.text_value = correct.mapped('text_value')[0] if correct else ''


class SlideChannelPartner(models.Model):
    _inherit = 'slide.channel.partner'

    assigned_date = fields.Datetime(string="Assigned Date")
    completion_date = fields.Datetime(string="Completion Date", compute='_compute_completion_date', store=True)

    @api.model
    def create(self, vals):
        if not vals.get('assigned_date'):
            vals['assigned_date'] = fields.Datetime.now()
        return super().create(vals)    

    @api.depends('member_status')
    def _compute_completion_date(self):
        completed  = self.search([('member_status', '=', 'completed')], limit=1)
        for rec in self:
            if completed:
                rec.completion_date = fields.Datetime.now()
            else:
                rec.completion_date = False
