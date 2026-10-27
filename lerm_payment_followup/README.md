# LERM Payment Follow-up

Moves every customer with unpaid invoices through configurable follow-up levels (email, phone call, manual task). Logs every reminder, call, promise to pay and dispute.

## Features

- **Follow-up levels**: steps a number of days after the due date of the customer's oldest unpaid invoice (negative = before the due date). Levels that are already due are skipped up to the highest one, so a customer who is 40 days overdue gets the 30-day step, not the friendly reminder.
- **Status per customer** (stored on `res.partner`, so it can be filtered and grouped): level done, next step, next action date, total due/overdue, responsible (defaults to the salesperson).
- **Follow-up log** (`lerm.followup.log`): emails, calls, meetings, notes, scheduled tasks, promises, disputes, resets.
- **Promise to pay**: pauses escalation until the promised date. The promise counts as kept once the total due drops by the promised amount; otherwise the customer becomes *Broken Promise* and the next step is due.
- **Disputes**: *Mark Disputed* on an invoice keeps it out of reminders and totals until a manager clicks *Resolve Dispute*.
- **From Contacts**: every customer form has a *Follow-up* button (showing the total due) that opens that customer's follow-up.
- **To-do lists**: *My Follow-ups* (customers you are responsible for) and *All Customers* (managers). *Do Next Step* runs the due step for the selected customers.
- **Optional automatic run**: off by default. Turn it on under Settings > Payment Follow-up.
- **Credit limit (optional, per customer)**: tick *Block on Credit Limit* on the customer and set their *Allowed Credit* (Contacts > customer > Sales & Purchase; everyone sees it, only Payment Follow-up Managers can change it; the follow-up form shows it read-only). With the box ticked, a limit of 0 means no credit: any unpaid invoice blocks. When the customer's outstanding amount (unpaid posted invoices, disputed ones included) is above the limit, creating a customer invoice or an SRF for them is blocked. On an SRF both the reporting and the billing customer are checked. Picking such a customer shows a warning straight away. Credit notes are never blocked. On existing draft invoices and SRFs, only changing the customer is checked.

## Daily jobs

| Scheduled action | Default | What it does |
|---|---|---|
| Payment Follow-up: Refresh Status | Active | Recomputes status (it depends on today's date), resets customers who paid everything and closes kept promises. Sends nothing. |
| Payment Follow-up: Automatic Run | Inactive | Toggled and timed from Settings. Does the due step for each customer not excluded from automation. With *Send Emails Automatically* off, it creates a "review and send" task instead of emailing. |

## Security

| Group | Access |
|---|---|
| Payment Follow-up: User | My Follow-ups, send reminders, log calls, mark disputes, see logs of own customers |
| Payment Follow-up: Manager | All customers, all logs, levels, resolve disputes, reset |

Users also need read access to customer invoices (Invoicing) to see the invoice lists.

## Notes

- **Invoice Copy for Customer** (invoice header): upload the copy you sent the customer (e.g. a signed PDF). Reminders, manual and automatic, attach this file instead of the generated PDF.
- Without an uploaded copy, invoice PDFs use `lerm_civil_inv.kes_invoice`. That template reads `request`, so it cannot render in the automatic run. There the email is sent without the PDF and the log says which invoices were not attached. Uploading a copy avoids this.
- Status is tracked on the commercial (parent) partner, matching `account.move.commercial_partner_id`.
