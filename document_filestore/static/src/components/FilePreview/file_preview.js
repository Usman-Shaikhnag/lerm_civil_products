/** @odoo-module **/

import { Component } from "@odoo/owl";

export class FilePreview extends Component {
  static template = "document_filestore.FilePreview";
  static props = {
    file: { type: Object },
    onClose: { type: Function },
  };
}
