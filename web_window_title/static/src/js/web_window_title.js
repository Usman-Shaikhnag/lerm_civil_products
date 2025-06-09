/** @odoo-module alias=web.window.title **/

import { WebClient } from "@web/webclient/webclient";
import { preferencesItem } from "@web/webclient/user_menu/user_menu_items";
import {patch} from "@web/core/utils/patch";
import { registry } from "@web/core/registry";
import { UserMenu } from "@web/webclient/user_menu/user_menu";

const userMenuItemRegistry = registry.category("user_menuitems");


patch(WebClient.prototype, "Web Window Title", {
    setup() {
        const title = document.title;
        this._super();
        this.title.setParts({ zopenerp: title });
    }
});




patch(UserMenu.prototype, "User Menu", {

    
    setup() {
        this._super.apply(this, arguments);
        userMenuItemRegistry.remove("odoo_account")
        userMenuItemRegistry.remove("documentation")
        userMenuItemRegistry.remove("support")




    },
    
    // odooAccountItem(env) {
    //     // this._super();
    //     // console.log("working")
    //     return this.super({
    //         type: "item",
    //         id: "account",
    //         description: env._t("My Esehat account"),
    //         callback: () => {
    //             env.services
    //                 .rpc("/web/session/account")
    //                 .then((url) => {
    //                     browser.location.href = url;
    //                 })
    //                 .catch(() => {
    //                     browser.location.href = "https://accounts.odoo.com/account";
    //                 });
    //         },
    //         sequence: 60,
    //     });
    // }
    
    
    


    
});
