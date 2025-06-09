/** @odoo-module **/
const spreadsheet =
  require("@documents_spreadsheet/js/o_spreadsheet/o_spreadsheet_loader")[
    Symbol.for("default")
  ];
const { createEmptyWorkbookData } = spreadsheet.helpers;
import field_registry from "web.field_registry_owl";
import AbstractFieldOwl from "web.AbstractFieldOwl";
const {
  getDataFromTemplate,
  base64ToJson,
} = require("documents_spreadsheet.pivot_utils");
var rpc = require("web.rpc");
const { Component, useState } = owl;
const { Model } = spreadsheet;

class Spreadsheet extends AbstractFieldOwl {
  setup() {
    super.setup(...arguments);
    // this.action = useService("action");
    this.state = useState({ name: "Test" });
    // createEmptyWorkbookData
  }

  async insertInDatasheet() {
    if (!this.props.record.data.datasheet) {
      var datasheet = await this.getDatasheetData();
      var templateId = datasheet[0].spreadsheet_template[0];
      const data = await getDataFromTemplate(this.env.services.rpc, templateId);
      const name =
        this.props.record.data.eln_id.data.display_name +
        "-" +
        this.record.data.parameter.parameter_name;

      const spreadsheetId = await this.env.services.rpc({
        model: "documents.document",
        method: "create",
        args: [
          {
            name,
            mimetype: "application/o-spreadsheet",
            folder_id: this.props.folderId,
            handler: "spreadsheet",
            raw: JSON.stringify(data),
          },
        ],
        context: this.props.context,
      });

      this.env.services.notification.notify({
        type: "info",
        message: this.env._t("New sheet saved in Documents"),
        sticky: false,
      });

      this.trigger("spreadsheet-created", { spreadsheetId });

      var eln_parameters_id = this.record.data.id;
      await this.env.services.rpc({
        model: "eln.parameters",
        method: "write",
        args: [[eln_parameters_id], { datasheet: spreadsheetId }],
      });

      this.__owl__.parent.parentWidget.do_action({
        type: "ir.actions.client",
        tag: "action_open_spreadsheet",
        params: { spreadsheet_id: spreadsheetId },
      });
    } else {
      // var datasheet = await this.getDatasheetData()
      // var templateId = datasheet[0].spreadsheet_template[0]
      // const data = await getDataFromTemplate(this.env.services.rpc, templateId)

      this.__owl__.parent.parentWidget.do_action({
        type: "ir.actions.client",
        tag: "action_open_spreadsheet",
        params: { spreadsheet_id: this.props.record.data.datasheet.data.id },
      });
      // var rpc = this.env.services.rpc
      // debugger

      // const model = await new Model(data, {
      //     mode: "normal",
      //     evalContext: {
      //         env: {
      //             delayedRPC: rpc,
      //             services: { rpc },
      //         },
      //     },
      // });

      // // await model.waitForIdle();
      // // await model.dispatch("EVALUATE_CELLS", { sheetId: "Sheet1" })
      // await model.waitForIdle();

      // var xlsx =  await model.exportXLSX();

      // // await waitForEvaluation(model);
      // debugger
      // // rpc.query({
      // //     model: "ir.attachment",
      // //     method: "create",
      // //     args: [posted],
      // // })
      // // debugger
    }
  }

  async getDatasheetData() {
    // console.log(this.record.data)
    // debugger
    var datasheet_id = this.record.data.parameter.data.id;
    var datasheet_data = await rpc.query({
      model: "lerm.parameter.master",
      method: "read",
      args: [[datasheet_id], []],
    });

    // console.log(datasheet_data)

    return datasheet_data;
  }
}

class SetResult extends AbstractFieldOwl {
  async getDataSheetFromParameter() {
    var datasheet_id = this.props.record.data.datasheet.data.id;
    var datasheet_data = await rpc.query({
      model: "documents.document",
      method: "read",
      args: [[datasheet_id], ["datas"]],
    });
    var data = base64ToJson(datasheet_data[0].datas);
    // const model = await new Model(data, {
    //     mode: "normal",
    //     evalContext: {
    //         env: {
    //             delayedRPC: rpc,
    //             services: { rpc },
    //         },
    //     },
    // });

    const model = await new Model(data, {
      mode: "normal",
    });



    var sheets = model.getters.getSheets();
    for (let index = 0; index < sheets.length; index++) {
      await model.dispatch("EVALUATE_CELLS", { sheetId: sheets[index].id });
    }

    // await model.dispatch("EVALUATE_CELLS", { sheetId: "UPV DATA SHEET" })
    // await model.dispatch("EVALUATE_CELLS", { sheetId: "Sheet1" })
    await model.waitForIdle();
    await model.waitForIdle();
    await model.waitForIdle();
    await model.waitForIdle();
    await model.waitForIdle();
    await model.waitForIdle();
    await model.waitForIdle();
    await model.waitForIdle();
    await model.waitForIdle();
    await model.waitForIdle();
    await model.waitForIdle();
    await model.waitForIdle();

    const sheet = model.getters.getSheets();
    debugger;
    console.log(sheet, "shhett");
    const filteredSheet = sheet.filter((result) => {
      return result.name == "Report";
    });
    console.log(filteredSheet, "sheet");
    // const id = filteredSheet[0].rows[12].cells[1].evaluated.value;
    // console.log(id , 'evalutaed value')

    const filteredDataFromSheet = filteredSheet[0].rows.filter((result) => {
      return Object.keys(result.cells).length !== 0;
    });

    let columnsHeading = Object.values(filteredDataFromSheet[0].cells).map(
      (entry) => entry.evaluated.value
    );

    columnsHeading = columnsHeading.map(function (value) {
      return { name: value };
    });

    var rows = [];
    // Iterate over each object in the array
    for (var i = 1; i < filteredDataFromSheet.length; i++) {
      var obj = filteredDataFromSheet[i];

      // Create an empty array to store the evaluated values for the current row
      var rowValues = [];

      // Iterate over each cell in the current object
      // for (var cellKey in obj.cells) {
      for (let i = 0; i <= columnsHeading.length - 1; i++) {
        if (obj.cells[i]) {
          var cellValue = obj.cells[i];

          // Check if the 'evaluated' key exists in the cell
          if (cellValue.evaluated && cellValue.evaluated.value) {
            // Append the 'value' from 'evaluated' to the row values
            rowValues.push(cellValue.evaluated.value);
          }
        } else {
          rowValues.push("-");
        }
      }
      // Append the row values to the rows array
      rows.push(rowValues);
    }

    rows = rows.map(function (row) {
      return {
        row: [{ value: row[0] }, { value: row[1] }],
      };
    });
    var formatedFinalData = [{ columns: columnsHeading }, { rows: rows }];
    // debugger
    console.log(formatedFinalData);
    formatedFinalData = JSON.stringify(formatedFinalData);

    var eln_parameters_id = this.record.data.id;
    await this.env.services.rpc({
      model: "eln.parameters",
      method: "write",
      args: [[eln_parameters_id], { result_json: formatedFinalData }],
    });

    $(".set_result_class").val(String(10));
    $(".set_result_class").trigger("change");
  }
}

class FetchDatasheet extends AbstractFieldOwl {
  async FetchDataSheets() {
    var existedds = await rpc.query({
      model: "eln.spreadsheets",
      method: "search_read",
      args: [[["eln_id", "=", this.record.data.id]], ["id"]],
    });

    if (existedds.length > 0) {
      var idstodelete = [];
      for (let index = 0; index < existedds.length; index++) {
        const elementid = existedds[index].id;
        idstodelete.push(elementid);
      }
      await rpc.query({
        model: "eln.spreadsheets",
        method: "unlink",
        args: [idstodelete],
      });
    }

    // console.log(this.props.record.data)
    var spreadsheet_templates_ids = [];
    var parameters = this.props.record.data.parameters.data;
    for (var i = 0; i < parameters.length; i++) {
      // console.log(parameters[i].data.parameter.data.id);
      var parameter_id = parameters[i].data.parameter.data.id;

      var datasheet_data = await rpc.query({
        model: "lerm.parameter.master",
        method: "read",
        args: [[parameter_id], []],
      });
      // debugger
      if (datasheet_data[0].spreadsheet_template) {
        var spreadsheet_template_id = datasheet_data[0].spreadsheet_template[0];
        spreadsheet_templates_ids.push(spreadsheet_template_id);
      }
    }

    var unique_spreadsheet_templates_ids = [
      ...new Set(spreadsheet_templates_ids),
    ];

    for (
      let index = 0;
      index < unique_spreadsheet_templates_ids.length;
      index++
    ) {
      const templateId = unique_spreadsheet_templates_ids[index];
      const data = await this.getDataFromTemplate(this.env.services.rpc, templateId);
      debugger
      // name for spreadsheet
      const name = "Spreadsheet";

      const spreadsheetId = await this.env.services.rpc({
        model: "documents.document",
        method: "create",
        args: [
          {
            name,
            mimetype: "application/o-spreadsheet",
            folder_id: this.props.folderId,
            handler: "spreadsheet",
            raw: JSON.stringify(data),
          },
        ],
        context: this.props.context,
      });

      var eln_parameters_ids = await rpc.query({
        model: "eln.parameters",
        method: "search_read",
        domain: [
          ["eln_id", "=", this.record.data.id],
          ["spreadsheet_template", "=", templateId],
        ],
        fields: [],
      });

      debugger;

      var eln_parameters = [];
      for (let index = 0; index < eln_parameters_ids.length; index++) {
        // const element = eln_parameters_id[index].id;
        eln_parameters.push(eln_parameters_ids[index].id);
      }

      var spreadsheet_data = {
        eln_id: this.props.record.data.id,
        datasheet: spreadsheetId,
        spreadsheet_template: templateId,
        related_parameters: eln_parameters,
      };

      // var spreadsheet_data = {
      //     'eln_id': this.props.record.data.id,
      //     'datasheet':spreadsheetId,
      //     'spreadsheet_template': templateId
      // }

      var spreadSheet = await this.env.services.rpc({
        model: "eln.spreadsheets",
        method: "create",
        args: [spreadsheet_data],
      });
    }

    this.trigger("reload");
  }

   async getDataFromTemplate(rpc, templateId) {
    let [{ data }] = await rpc({
        method: "read",
        model: "spreadsheet.template",
        args: [templateId, ["data"]],
    });
    data = base64ToJson(data);
    const model = new Model(data, {
        mode: "headless",
        evalContext: {
            env: {
                delayedRPC: rpc,
                services: { rpc },
            },
        },
    });
    debugger
    await model.waitForIdle();
    model.dispatch("CONVERT_PIVOT_FROM_TEMPLATE");
    return model.exportData();
  }



}





class FillDataSheet extends AbstractFieldOwl {
  async openDatasheet() {
    // console.log("Coming from DataSheet")

    this.__owl__.parent.parentWidget.do_action({
      type: "ir.actions.client",
      tag: "action_open_spreadsheet",
      params: { spreadsheet_id: this.props.record.data.datasheet.data.id },
    });
  }
}

class UpdateResult extends AbstractFieldOwl {


  async updateResult() {
    console.log("Coming from update");

    var datasheets = this.recordData.datasheets.data;

    for (let index = 0; index < datasheets.length; index++) {
      var datasheet_document_id = datasheets[index].data.datasheet.data.id;

      var datasheet_data = await rpc.query({
        model: "documents.document",
        method: "read",
        args: [[datasheet_document_id], ["datas"]],
      });
      var data = base64ToJson(datasheet_data[0].datas);

      const model = await new Model(data, {
        mode: "normal",
      });

      debugger
      

      var sheets = model.getters.getSheets();
      for (let index = 0; index < sheets.length; index++) {
        await model.dispatch("EVALUATE_CELLS", { sheetId: sheets[index].id });
      }

      var parameters = datasheets[index].data.related_parameters.data

      for (let index = 0; index < parameters.length; index++) {
        const eln_parameter_id = parameters[index].data.id;
        
        var eln_parameter = await rpc.query({
            model: "eln.parameters",
            method: "read",
            args: [[eln_parameter_id], []],
          });

          

          
        var parameter_id = eln_parameter[0].parameter[0]

        var parameters_master = await rpc.query({
            model: "lerm.parameter.master",
            method: "read",
            args: [[parameter_id], []],
          });

        var sheet_name =   model.getters.getSheetIdByName(parameters_master[0].sheets)

        var cell =  parameters_master[0].cell
        var cordinates = this.convertCellToCoordinate(cell)
        debugger

        var result = model.getters.getCell(sheet_name,cordinates.column,cordinates.row).evaluated.value
        // debugger

        await this.env.services.rpc({
            model: "eln.parameters",
            method: "write",
            args: [[eln_parameter_id], { result: result }],
          });
      }
      
    }
    this.trigger("reload");
  }

   convertCellToCoordinate(cell) {
    const column = cell.charCodeAt(0) - 65; // Convert the column letter to a numerical value (0-based index)
    const row = parseInt(cell.slice(1)) - 1; // Extract the row number and subtract 1 (0-based index)
  
    return { row, column };
  }


}

SetResult.template = "lerm_civil.set_result";
Spreadsheet.template = "lerm_civil.fill_datasheet";
FetchDatasheet.template = "lerm_civil.fetch_required_datasheet";
FillDataSheet.template = "lerm_civil.fill_datasheet_eln";
UpdateResult.template = "lerm_civil.update_result";

field_registry.add("set_result", SetResult);
field_registry.add("fetch_datasheet", FetchDatasheet);
field_registry.add("datasheet", Spreadsheet);
field_registry.add("update_result", UpdateResult);
field_registry.add("fill_datasheet", FillDataSheet);


export default Spreadsheet;
