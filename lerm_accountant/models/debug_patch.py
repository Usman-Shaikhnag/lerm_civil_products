import sys
import logging
from odoo.addons.web.models.models import Base

_logger = logging.getLogger(__name__)

original_domain_image = Base._search_panel_domain_image

def patched_domain_image(self, field_name, domain, set_count=False, limit=False):
    if field_name == 'invoice_status':
        print("=== DEBUG _search_panel_domain_image ===", file=sys.stderr)
        print("model=%s field=%s domain=%s set_count=%s limit=%s" % (self._name, field_name, domain, set_count, limit), file=sys.stderr)
        _logger.warning("=== _search_panel_domain_image ===")
        _logger.warning("model=%s field=%s domain=%s", self._name, field_name, domain)
    return original_domain_image(self, field_name, domain, set_count, limit)

Base._search_panel_domain_image = patched_domain_image
