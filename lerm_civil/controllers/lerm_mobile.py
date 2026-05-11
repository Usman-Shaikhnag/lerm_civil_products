# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import logging
import json
_logger = logging.getLogger(__name__)

class MobileAppController(http.Controller):

    @http.route('/mobile/login_with_session', type='json', auth='none', methods=['POST'], csrf=False, cors='*')
    def login_with_session(self, **kwargs):
        """
        Endpoint to validate a session ID from the mobile app.
        Checks if the provided X-Session-Id header corresponds to a valid, active session.
        Works across Odoo 14, 15, 16, 17, and 18.
        """
        # In newer Odoo versions (16+), headers are accessed slightly differently 
        # than older versions. We try the standard Werkzeug way first.
        try:
            # Try to get the session ID from the custom header first
            headers = request.httprequest.headers
            session_id = headers.get('X-Session-Id')
            
            if not session_id:
                return {'status': 'error', 'message': 'Missing X-Session-Id header'}

            # Get the session storage/store mechanism
            # In older Odoo (<=15): request.session.store
            # In newer Odoo (>=16): http.root.session_store
            session_store = getattr(http.root, 'session_store', None)
            if not session_store and hasattr(request, 'session'):
                session_store = getattr(request.session, 'store', None)
                
            if not session_store:
                # Fallback mechanism if we can't find the session store directly
                from odoo.tools._vendor.sessions import SessionStore
                # This is a bit hacky but works if the standard attributes changed
                return {'status': 'error', 'message': 'Could not access session store'}
            _logger.info("VALIDATING SESSION ID: %s", session_id)
            
            # Retrieve the session using the session ID
            # In werkzeug 0.x (Odoo <= 15): session_store.get(session_id)
            # In werkzeug 2.x+ (Odoo >= 16): session_store.get(session_id) still generally works
            _logger.info("SESSION STORE: %s", session_store)
            session = session_store.get(session_id)
            _logger.info("RETRIEVED SESSION: %s", session)
            
            # Odoo 17 session behavior workaround: sometimes the session is valid but uid is retrieved via a different key or property depending on how Werkzeug loaded it.
            if session and not session.get('uid') and hasattr(session, 'uid'):
                session['uid'] = session.uid

            if not session:
               return {'status': 'error', 'message': 'Invalid or expired session'}

            # Check if the session is authenticated (has a UID)
            uid = session.get('uid')
            
            if not uid:
                 return {'status': 'error', 'message': 'Session is not authenticated (no uid)'}

            # Verify the user exists and is active
            # We need to use the environment with sudo to check the user as we aren't fully auth'd
            # In newer Odoo, we might need request.env(su=True) instead of sudo()
            try:
                env = request.env(user=1) # Use superuser environment
            except TypeError:
                 env = request.env['res.users'].sudo().env # Fallback for older odoo

            user = env['res.users'].browse(uid)
            if not user.exists() or not user.active:
                return {'status': 'error', 'message': 'User associated with session is inactive or deleted'}

            # Return success with basic user info
            return {
                'status': 'success',
                'user': {
                    'id': user.id,
                    'name': user.name,
                    'login': user.login
                }
            }

        except Exception as e:
            _logger.exception("Error during mobile session validation")
            return {'status': 'error', 'message': str(e)}

    @http.route('/mobile/db_list', type='json', auth='none', methods=['POST'], csrf=False, cors='*')
    def db_list(self, **kwargs):
        """
        Return the list of databases available on this Odoo server.
        Works even when no database is selected (auth='none').
        If list_db is disabled in the server config, returns an empty list.
        """
        try:
            from odoo.service.db import list_dbs
            databases = list_dbs(force=True)
            return {'success': True, 'databases': databases}
        except Exception as e:
            _logger.warning("Could not list databases: %s", e)
            return {'success': True, 'databases': []}

    @http.route('/mobile_login', type='json', auth='none', methods=['POST'], csrf=False, cors='*')
    def mobile_login(self, **kwargs):
        """
        Endpoint to authenticate a user from the mobile app.
        Checks if the provided email and password correspond to a valid user.
        Accepts an optional 'db' parameter to select the target database.
        """
        try:
            data = request.params
            email = data.get('email')
            password = data.get('password')

            if not email or not password:
                return {'success': False, 'error': 'Missing email or password'}

            # Use the provided db name, or fall back to the current database
            db = data.get('db') or request.env.cr.dbname
            uid = request.session.authenticate(db, email, password)

            if uid:
                session_id = request.session.sid
                return {
                    'success': True,
                    'uid': uid,
                    'session_id': session_id
                }
            else:
                return {'success': False, 'error': 'Invalid credentials'}

        except Exception as e:
            _logger.exception("Error during mobile login")
            return {'success': False, 'error': str(e)}

    @http.route('/mobile/installed_apps', type='json', auth='user', methods=['POST'], csrf=False, cors='*')
    def get_installed_apps(self, **kwargs):
        """
        Endpoint to return the apps visible to the current user in the Odoo web menu.
        This mirrors the Odoo web client by returning root-level menus the user has access to.
        """
        try:
            user = request.env.user

            # Odoo web shows root menus (parent_id = False) that the user can access.
            # ir.ui.menu respects access rights automatically via its _visible_menu_ids method.
            visible_menu_ids = request.env['ir.ui.menu']._visible_menu_ids()
            root_menus = request.env['ir.ui.menu'].browse(visible_menu_ids).filtered(
                lambda m: not m.parent_id
            ).sorted(key=lambda m: m.sequence)

            apps_list = []
            for menu in root_menus:
                # web_icon format is typically "module,static/description/icon.png"
                icon = ''
                if menu.web_icon:
                    parts = menu.web_icon.split(',')
                    if len(parts) == 2:
                        icon = '/%s/%s' % (parts[0].strip(), parts[1].strip())

                apps_list.append({
                    'name': menu.name or '',
                    'display_name': menu.name or '',
                    'summary': '',
                    'category': '',
                    'icon': icon,
                    'menu_id': menu.id,
                })

            return {
                'success': True,
                'user_name': user.name,
                'apps': apps_list,
            }

        except Exception as e:
            _logger.exception("Error fetching installed apps")
            return {'success': False, 'error': str(e)}

    @http.route('/mobile/app_menus', type='json', auth='user', methods=['POST'], csrf=False, cors='*')
    def get_app_menus(self, **kwargs):
        """
        Given a root menu_id, return the visible sub-menu tree.
        Each leaf menu includes its action's model so the mobile app can fetch records.
        """
        try:
            data = request.params
            root_menu_id = data.get('menu_id')
            if not root_menu_id:
                return {'success': False, 'error': 'Missing menu_id'}

            visible_menu_ids = request.env['ir.ui.menu']._visible_menu_ids()
            all_menus = request.env['ir.ui.menu'].browse(visible_menu_ids)

            def _get_children(parent_id):
                children = all_menus.filtered(
                    lambda m: m.parent_id.id == parent_id
                ).sorted(key=lambda m: m.sequence)
                result = []
                for menu in children:
                    # Resolve action to get model name
                    model = ''
                    action_id = None
                    action_type = ''
                    if menu.action:
                        action = menu.action
                        action_type = action._name  # e.g. 'ir.actions.act_window'
                        if hasattr(action, 'res_model'):
                            model = action.res_model or ''
                        action_id = action.id

                    sub_children = _get_children(menu.id)
                    result.append({
                        'id': menu.id,
                        'name': menu.name or '',
                        'model': model,
                        'action_id': action_id,
                        'action_type': action_type,
                        'children': sub_children,
                        'has_children': len(sub_children) > 0,
                    })
                return result

            menu_tree = _get_children(root_menu_id)

            return {
                'success': True,
                'menus': menu_tree,
            }

        except Exception as e:
            _logger.exception("Error fetching app menus")
            return {'success': False, 'error': str(e)}

    @http.route('/mobile/records', type='json', auth='user', methods=['POST'], csrf=False, cors='*')
    def get_records(self, **kwargs):
        """
        Fetch records for a given model with pagination.
        Returns records, total count, and field metadata (labels + types).
        """
        try:
            data = request.params
            model_name = data.get('model')
            if not model_name:
                return {'success': False, 'error': 'Missing model'}

            limit = data.get('limit', 20)
            offset = data.get('offset', 0)
            search_query = data.get('search', '')
            search_field = data.get('search_field', '')
            group_by = data.get('group_by', '')
            order = data.get('order', 'id desc')

            if group_by:
                order = f"{group_by} asc, {order}"

            Model = request.env[model_name]

            # Build domain — start with action_domain if provided (from stat buttons / actions)
            action_domain = data.get('action_domain', [])
            domain = list(action_domain) if action_domain else []
            
            if search_query:
                if search_field and search_field in Model._fields:
                    field_type = Model._fields[search_field].type
                    if field_type in ('integer', 'float', 'monetary'):
                        try:
                            domain.append((search_field, '=', float(search_query)))
                        except ValueError:
                            domain.append(('id', '=', -1))
                    elif field_type == 'many2one':
                        domain.append((search_field + '.name', 'ilike', search_query))
                    else:
                        domain.append((search_field, 'ilike', search_query))
                else:
                    # Try to search on 'name' or 'display_name' if they exist
                    name_field = 'name' if 'name' in Model._fields else 'display_name'
                    domain.append((name_field, 'ilike', search_query))

            # Get total count
            total_count = Model.search_count(domain)

            # Determine which fields to read — pick key visible fields
            all_fields = Model.fields_get()
            # Filter to show meaningful fields (skip internal/technical ones)
            skip_types = {'binary', 'one2many', 'many2many', 'html', 'reference'}
            skip_names = {
                'id', 'create_uid', 'write_uid', 'create_date', 'write_date',
                '__last_update', 'activity_ids', 'message_ids', 'message_follower_ids',
                'message_partner_ids', 'message_channel_ids', 'website_message_ids',
                'access_url', 'access_token', 'access_warning',
            }

            display_fields = []
            for fname, finfo in all_fields.items():
                if fname in skip_names:
                    continue
                if finfo.get('type') in skip_types:
                    continue
                if not finfo.get('string'):
                    continue
                display_fields.append(fname)

            # Limit to first 8 most important fields to keep it clean
            # Prioritize: name, state/status fields, date fields, then others
            priority_fields = []
            other_fields = []
            for f in display_fields:
                if f in ('name', 'display_name', 'state', 'stage_id', 'partner_id',
                         'date', 'date_order', 'date_start'):
                    priority_fields.append(f)
                else:
                    other_fields.append(f)

            selected_fields = (priority_fields + other_fields)[:8]

            # Always include 'name' or 'display_name' if available
            if 'name' in all_fields and 'name' not in selected_fields:
                selected_fields.insert(0, 'name')
            elif 'display_name' not in selected_fields:
                selected_fields.insert(0, 'display_name')

            # Always include grouped field in selected_fields to fetch it properly
            if group_by and group_by not in selected_fields:
                selected_fields.append(group_by)

            # Fetch records
            records = Model.search_read(
                domain,
                fields=selected_fields,
                limit=limit,
                offset=offset,
                order=order or False,
            )

            # Process many2one fields to return [id, name] → just the name string
            for rec in records:
                for key, val in rec.items():
                    if isinstance(val, (list, tuple)) and len(val) == 2 and isinstance(val[0], int):
                        rec[key] = val[1]  # Use display name

            # Build field metadata
            fields_meta = {}
            for fname in selected_fields:
                if fname in all_fields:
                    finfo = all_fields[fname]
                    fields_meta[fname] = {
                        'label': finfo.get('string', fname),
                        'type': finfo.get('type', 'char'),
                    }

            return {
                'success': True,
                'records': records,
                'total_count': total_count,
                'fields': fields_meta,
                'limit': limit,
                'offset': offset,
            }

        except Exception as e:
            _logger.exception("Error fetching records for model: %s", data.get('model', ''))
            return {'success': False, 'error': str(e)}

    @http.route('/mobile/model_fields', type='json', auth='user', methods=['POST'], csrf=False, cors='*')
    def get_model_fields(self, **kwargs):
        """ Fetch the schema and structured layout for a given model's form view. """
        data = request.params or kwargs
        try:
            model = data.get('model')
            
            if not model:
                return {'success': False, 'error': 'Model is required'}
                
            Model = request.env[model]
            
            # 1. Get field definitions
            all_fields = Model.fields_get()
            
            # 2. Get the form view architecture
            views_data = Model.get_views([(False, 'form')])
            form_view = views_data.get('views', {}).get('form', {})
            arch = form_view.get('arch')
            
            exclude = ['create_uid', 'create_date', 'write_uid', 'write_date',
                        '__last_update', 'activity_ids', 'message_ids', 'message_follower_ids']
            seen_fields = set()
            
            def _get_invisible_expr(node):
                """
                Return the invisible expression for a node.
                Returns None if always visible, True if always hidden,
                or a string expression for dynamic visibility.
                """
                invisible = node.get('invisible')
                if not invisible:
                    # Check modifiers for static invisible (Odoo <= 16 style)
                    modifiers_str = node.get('modifiers', '{}')
                    try:
                        modifiers = json.loads(modifiers_str)
                        mod_invisible = modifiers.get('invisible')
                        if mod_invisible == True:
                            return True
                        if mod_invisible and isinstance(mod_invisible, list):
                            # Domain-style modifiers — convert to a string repr
                            return json.dumps(mod_invisible)
                    except:
                        pass
                    return None
                if invisible in ('1', 'True', 'true'):
                    return True  # Always hidden
                # Dynamic expression like "state != 'draft'"
                return invisible

            def _parse_node(node):
                """ Recursively parse an XML node into a layout structure. """
                tag = node.tag
                result = None
                
                # Check if node is always invisible (skip it)
                inv = _get_invisible_expr(node)
                if inv is True:
                    return None
                # inv is either None (always visible) or a string expression (dynamic)
                
                if tag == 'header':
                    buttons = []
                    for child in node:
                        if child.tag == 'button':
                            btn_inv = _get_invisible_expr(child)
                            if btn_inv is True:
                                continue
                            btn_name = child.get('name', '')
                            btn_string = child.get('string', btn_name)
                            btn_type = child.get('type', 'object')
                            btn_class = child.get('class', '')
                            btn_data = {
                                'type': 'button',
                                'name': btn_name,
                                'string': btn_string,
                                'btn_type': btn_type,
                                'btn_class': btn_class,
                            }
                            if btn_inv:
                                btn_data['invisible'] = btn_inv
                            buttons.append(btn_data)
                        elif child.tag == 'field':
                            fname = child.get('name')
                            if fname and fname in all_fields and fname not in exclude:
                                # Status widget field in header (e.g. state)
                                widget = child.get('widget', '')
                                field_data = {
                                    'type': 'status_field',
                                    'name': fname,
                                    'widget': widget,
                                }
                                field_inv = _get_invisible_expr(child)
                                if field_inv and field_inv is not True:
                                    field_data['invisible'] = field_inv
                                buttons.append(field_data)
                                seen_fields.add(fname)
                    if buttons:
                        result = {'type': 'header', 'children': buttons}
                
                elif tag == 'group':
                    children = []
                    for child in node:
                        parsed = _parse_node(child)
                        if parsed:
                            children.append(parsed)
                    if children:
                        result = {
                            'type': 'group',
                            'string': node.get('string', ''),
                            'children': children,
                        }

                elif tag == 'notebook':
                    pages = []
                    for child in node:
                        if child.tag == 'page':
                            page_inv = _get_invisible_expr(child)
                            if page_inv is True:
                                continue
                            page_children = []
                            for sub in child:
                                parsed = _parse_node(sub)
                                if parsed:
                                    page_children.append(parsed)
                            if page_children:
                                page_data = {
                                    'type': 'page',
                                    'string': child.get('string', 'Tab'),
                                    'children': page_children,
                                }
                                if page_inv:
                                    page_data['invisible'] = page_inv
                                pages.append(page_data)
                    if pages:
                        result = {'type': 'notebook', 'pages': pages}
                
                elif tag == 'separator':
                    result = {
                        'type': 'separator',
                        'string': node.get('string', ''),
                    }
                
                elif tag == 'button':
                    btn_name = node.get('name', '')
                    btn_string = node.get('string', btn_name)
                    btn_type = node.get('type', 'object')
                    btn_class = node.get('class', '')
                    
                    # Handle stat buttons (oe_stat_button with nested statinfo field)
                    is_stat = 'oe_stat_button' in btn_class
                    stat_field = None
                    if is_stat:
                        for child in node:
                            if child.tag == 'field':
                                child_widget = child.get('widget', '')
                                child_string = child.get('string', '')
                                child_name = child.get('name', '')
                                if child_widget == 'statinfo' and child_string:
                                    btn_string = child_string
                                    stat_field = child_name
                                    if child_name and child_name in all_fields:
                                        seen_fields.add(child_name)
                                    break
                    
                    result = {
                        'type': 'button',
                        'name': btn_name,
                        'string': btn_string,
                        'btn_type': btn_type,
                        'btn_class': btn_class,
                    }
                    if is_stat and stat_field:
                        result['is_stat_button'] = True
                        result['stat_field'] = stat_field
                    if inv:
                        result['invisible'] = inv
                
                elif tag == 'field':
                    fname = node.get('name')
                    if fname and fname in all_fields and fname not in exclude and fname not in seen_fields:
                        seen_fields.add(fname)
                        widget = node.get('widget', '')
                        result = {
                            'type': 'field',
                            'name': fname,
                            'widget': widget,
                        }
                        if inv:
                            result['invisible'] = inv
                            
                        statusbar_visible = node.get('statusbar_visible')
                        if statusbar_visible:
                            result['statusbar_visible'] = statusbar_visible
                            
                        # A field (like one2many) might have an inline <tree> or <form> child
                        children = []
                        for child in node:
                            parsed = _parse_node(child)
                            if parsed:
                                children.append(parsed)
                        if children:
                            result['children'] = children
                
                elif tag in ('sheet', 'form', 'div', 'footer', 'tree', 'kanban'):
                    # Container tags — recurse into children
                    children = []
                    for child in node:
                        parsed = _parse_node(child)
                        if parsed:
                            children.append(parsed)
                    if children or tag in ('tree', 'kanban'):
                        # Keep tree/kanban nodes identifiable even if they have 1 child or are empty
                        if tag in ('tree', 'kanban'):
                            result = {'type': tag, 'children': children}
                        elif len(children) == 1:
                            result = children[0]
                        else:
                            result = {'type': 'container', 'children': children}
                
                return result
            
            # Parse the XML arch
            layout = []
            if arch:
                import lxml.etree as etree
                try:
                    doc = etree.fromstring(arch)
                    for child in doc:
                        parsed = _parse_node(child)
                        if parsed:
                            layout.append(parsed)
                except Exception as xml_e:
                    _logger.warning("Failed to parse XML arch for model %s: %s", model, xml_e)
            
            # Build field schema dict for all fields referenced in the layout
            clean_fields = {}
            for fname in seen_fields:
                if fname in all_fields:
                    finfo = all_fields[fname]
                    clean_fields[fname] = {
                        'type': finfo.get('type'),
                        'string': finfo.get('string'),
                        'required': finfo.get('required', False),
                        'readonly': finfo.get('readonly', False),
                        'selection': finfo.get('selection', []),
                        'help': finfo.get('help', ''),
                        'relation': finfo.get('relation', ''),
                    }
            
            # Fallback if layout is empty
            if not layout:
                fallback_exclude = exclude + ['id']
                field_order = [f for f in all_fields.keys() if f not in fallback_exclude][:30]
                for fname in field_order:
                    finfo = all_fields[fname]
                    clean_fields[fname] = {
                        'type': finfo.get('type'),
                        'string': finfo.get('string'),
                        'required': finfo.get('required', False),
                        'readonly': finfo.get('readonly', False),
                        'selection': finfo.get('selection', []),
                        'help': finfo.get('help', ''),
                        'relation': finfo.get('relation', ''),
                    }
                layout = [{'type': 'group', 'string': '', 'children': [{'type': 'field', 'name': f, 'widget': ''} for f in field_order]}]
            
            return {
                'success': True,
                'fields': clean_fields,
                'layout': layout,
            }

        except Exception as e:
            _logger.exception("Error fetching fields for model: %s", data.get('model', ''))
            return {'success': False, 'error': str(e)}

    @http.route('/mobile/record_read', type='json', auth='user', methods=['POST'], csrf=False, cors='*')
    def read_record(self, **kwargs):
        """ Read a single record by ID with all its fields. """
        data = request.params or kwargs
        try:
            model = data.get('model')
            record_id = data.get('id')
            
            if not model or not record_id:
                return {'success': False, 'error': 'Model and ID are required'}
                
            Model = request.env[model]
            record = Model.browse(record_id)
            
            if not record.exists():
                return {'success': False, 'error': 'Record not found'}
                
            # Read all fields
            record_data = record.read()[0]
            
            # Resolve names for x2many fields to display [id, name] instead of just id
            for fname, val in record_data.items():
                if isinstance(val, list) and val and isinstance(val[0], int):
                    # Check if it's an x2many field by looking at the model fields
                    field_type = Model._fields.get(fname).type
                    if field_type in ['one2many', 'many2many']:
                        rel_model = Model._fields.get(fname).comodel_name
                        if rel_model:
                            rel_records = request.env[rel_model].browse(val)
                            # Convert list of IDs to list of [id, display_name]
                            record_data[fname] = [[r.id, r.display_name] for r in rel_records]
            
            return {
                'success': True,
                'data': record_data,
            }

        except Exception as e:
            _logger.exception("Error reading record %s in model %s", data.get('id', ''), data.get('model', ''))
            return {'success': False, 'error': str(e)}

    @http.route('/mobile/record_create', type='json', auth='user', methods=['POST'], csrf=False, cors='*')
    def create_record(self, **kwargs):
        """ Create a new record in the specified model. """
        data = request.params or kwargs
        try:
            model = data.get('model')
            values = data.get('values', {})
            context = data.get('context', {})
            
            if not model or not values:
                return {'success': False, 'error': 'Model and values are required'}
                
            Model = request.env[model]
            if context:
                Model = Model.with_context(**context)
            
            # Clean up the values (e.g. remove many2one tuples if they slip through, though frontend should handle this)
            clean_values = self._clean_form_values(values, Model)
                
            record = Model.create(clean_values)
            
            return {
                'success': True,
                'id': record.id,
                'message': 'Record created successfully',
            }

        except Exception as e:
            _logger.exception("Error creating record in model %s", data.get('model', ''))
            return {'success': False, 'error': str(e)}

    @http.route('/mobile/record_update', type='json', auth='user', methods=['POST'], csrf=False, cors='*')
    def update_record(self, **kwargs):
        """ Update an existing record in the specified model. """
        data = request.params or kwargs
        try:
            model = data.get('model')
            record_id = data.get('id')
            values = data.get('values', {})
            
            if not model or not record_id or not values:
                return {'success': False, 'error': 'Model, ID, and values are required'}
                
            Model = request.env[model]
            record = Model.browse(record_id)
            
            if not record.exists():
                return {'success': False, 'error': 'Record not found'}
                
            clean_values = self._clean_form_values(values, Model)
                
            record.write(clean_values)
            
            return {
                'success': True,
                'id': record.id,
                'message': 'Record updated successfully',
            }

        except Exception as e:
            _logger.exception("Error updating record %s in model %s", data.get('id', ''), data.get('model', ''))
            return {'success': False, 'error': str(e)}

    def _clean_form_values(self, values, Model):
        """ 
        Helper to sanitize incoming values from the mobile app 
        before passing them to Odoo's create/write methods.
        """
        clean_values = {}
        fields_info = Model.fields_get()
        
        for key, val in values.items():
            if key not in fields_info:
                continue
                
            field_type = fields_info[key].get('type')
            
            # Frontend sometimes sends empty strings for numbers or false
            if val == '' and field_type in ['integer', 'float', 'monetary', 'many2one', 'date', 'datetime']:
                clean_values[key] = False
                continue
                
            if field_type == 'many2one':
                # If it's a list/tuple like [1, "Admin"], extract just the ID
                if isinstance(val, (list, tuple)) and len(val) > 0:
                    clean_values[key] = val[0]
                elif isinstance(val, dict) and 'id' in val:
                    clean_values[key] = val['id']
                else:
                    clean_values[key] = val
            elif field_type in ['one2many', 'many2many']:
                # For now, we skip updating complex relations from the mobile app to ensure stability.
                # Only standard fields are updated in this iteration.
                pass
            else:
                clean_values[key] = val
                
        return clean_values

    @http.route('/mobile/render_pdf', type='http', auth='user', methods=['GET'], csrf=False, cors='*')
    def mobile_render_pdf(self, report_name, id, model_name, data=None, **kwargs):
        """
        Explicitly generates and downloads a PDF report for the mobile app,
        bypassing HTML previews.
        """
        try:
            record_id = int(id)
            context = dict(request.env.context)
            context.update({
                'active_id': record_id, 
                'active_ids': [record_id], 
                'active_model': model_name
            })
            
            report_data = {}
            if data:
                try:
                    report_data = json.loads(data)
                except ValueError:
                    pass
                    
            # Inject context into data so _get_report_values can access data['context']
            if 'context' not in report_data:
                report_data['context'] = context

            report_sudo = request.env['ir.actions.report'].sudo()._get_report_from_name(reportname=report_name)
            if not report_sudo:
                return request.make_response("Report not found", status=404)

            # Render the PDF server-side using wkhtmltopdf
            pdf_content, ext = report_sudo.with_context(context)._render_qweb_pdf(report_name, [record_id], data=report_data)

            filename = "%s_%s.pdf" % (report_name.replace('.', '_'), record_id)
            headers = [
                ('Content-Type', 'application/pdf'),
                ('Content-Length', str(len(pdf_content))),
                ('Content-Disposition', 'attachment; filename="%s"' % filename)
            ]
            return request.make_response(pdf_content, headers=headers)
        except Exception as e:
            _logger.exception("Error rendering mobile PDF for report %s", report_name)
            # Return a visible text error if rendering fails, rather than silence
            return request.make_response(f"PDF Rendering Error: {str(e)}", status=500)
