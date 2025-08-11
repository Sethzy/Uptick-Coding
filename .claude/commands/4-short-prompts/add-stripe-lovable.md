I want to **add Stripe payments** to the app.

- Use **Stripe in test mode** for now.
- We have a product in Stripe with ID `prod_12345` and a price ID `price_67890` (one-time purchase).
- Implement a checkout button on the **Pricing page** that starts a Stripe checkout for that product.
- After successful payment, redirect the user to `/payment-success`. If the payment is canceled, redirect to `/payment-cancelled`.

Important:

- Assume API keys and webhook secrets are configured securely (do **not** hard-code them).
- Do **not** modify any other pages or features unrelated to payments.

Once done, provide any webhook endpoint setup instructions I need (e.g., URL to add in Stripe dashboard for post-payment events).
