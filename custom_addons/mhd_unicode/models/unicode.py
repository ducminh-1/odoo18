import unicodedata
from odoo import api, models

class UnicodeNormalizationMixin(models.AbstractModel):
    _name = 'unicode.normalization.mixin'
    _description = 'Unicode Normalization Mixin'

    def normalize_unicode(self, unicode_str):
        return unicodedata.normalize('NFC', unicode_str)

    def normalize_unicode_fields(self, vals):
        for field_name, field in self._fields.items():
            if field.type == 'char' and field_name in vals:
                vals[field_name] = self.normalize_unicode(vals[field_name])
        return vals

    @api.model
    def create(self, vals):
        vals = self.normalize_unicode_fields(vals)
        return super(UnicodeNormalizationMixin, self).create(vals)

    @api.model
    def write(self, vals):
        vals = self.normalize_unicode_fields(vals)
        return super(UnicodeNormalizationMixin, self).write(vals)

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        normalized_args = []
        for arg in args:
            if isinstance(arg, (list, tuple)) and len(arg) > 1 and isinstance(arg[1], str):
                if isinstance(arg[2], str):
                    arg = (arg[0], arg[1], self.normalize_unicode(arg[2]))
            normalized_args.append(arg)
        return super(UnicodeNormalizationMixin, self)._search(normalized_args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)