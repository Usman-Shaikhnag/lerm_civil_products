/** @odoo-module */

import { registry } from "@web/core/registry";
import { useEffect, useService } from "@web/core/utils/hooks";

// import { loadJS } from "@web/core/assets"
import { loadJS } from "web.ajax";

const { Component } = owl;
const { useRef, onWillStart, onMounted, onWillUnmount } = owl.hooks;
export class KpiBox extends Component {
  setup() {
    this.subjectRef = useRef("subject");
    this.valueRef = useRef("value");
    this.actionService = useService("action");
  }
  onClick() {
    this.env.bus.trigger("kpi-click", {
      stateName: this.props.state,
    });
  }
}

KpiBox.template = "lerm_civil_dashboard.KpiBox";
