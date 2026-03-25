# InvoicePilot Skill

You are helping the user manage and download SaaS invoices using InvoicePilot.

## When to use this skill
- User says anything about downloading invoices, billing records, or SaaS statements
- User asks which services are connected
- User wants to initialize InvoicePilot

## Tool Mapping

**"download invoices [for/from/since] [date range]"**
→ Use `invoicepilot_download` with the date range as the query argument.

Examples:
- "download all invoices for last month" → `invoicepilot_download "last month"`
- "get invoices from April 2024 to now" → `invoicepilot_download "since April 2024"`
- "download March 2025 invoices" → `invoicepilot_download "March 2025"`
- "download only AWS and Stripe for Q1" → `invoicepilot_download "Q1 2025" --only AWS Stripe`

**"check which services are connected" / "list connectors" / "what's configured"**
→ Use `invoicepilot_list`

**"set up InvoicePilot" / "create config" / "initialize"**
→ Use `invoicepilot_init`

## After running a download
- Report the summary output to the user
- If any service shows an error with a hint, surface the hint clearly
- If files were downloaded, confirm the folder path
