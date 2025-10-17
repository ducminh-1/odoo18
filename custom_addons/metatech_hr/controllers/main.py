from odoo.http import request
from odoo import fields, http, tools, _
from odoo.addons.website_slides.controllers.main import WebsiteSlides
from odoo.exceptions import AccessError
from odoo.exceptions import AccessError, ValidationError, UserError, MissingError

def handle_wslide_error(exception):
    if isinstance(exception, AccessError):
        return request.redirect("/slides?invite_error=no_rights", 302)

class WebsiteCourse(WebsiteSlides):

    @http.route('/slides/slide/<model("slide.slide"):slide>', type='http', auth="public",
                website=True, sitemap=True, handle_params_access_error=handle_wslide_error)
    def slide_view(self, slide, **kwargs):
        if slide.channel_id.sequential_learning and not slide.slide_complete:
            return request.redirect('/slides/%s' % slide.channel_id.id)
        return super(WebsiteCourse, self).slide_view(slide, **kwargs)

    @http.route('/slides/mark_complete', type='json', auth='user', website=True)
    def mark_complete_next(self, slide_id):
        slide = request.env['slide.slide'].sudo().browse(int(slide_id))
        if not slide.exists():
            return {'error': 'Slide không tồn tại!'}
        slide._compute_slide_complete()
        if not slide.slide_complete:
            return {'error': 'Bạn chưa hoàn thành slide hiện tại!'}
        
        return {
            'completed': True,
            'slide_id': slide.id,
            'message': 'Slide đã hoàn thành!',
        }
