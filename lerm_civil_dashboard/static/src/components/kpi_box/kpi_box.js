/** @odoo-module */
import { Component, useRef, onWillStart, onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

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

// 👇 Register your component so it can be imported elsewhere
registry.category("components").add("KpiBox", KpiBox);