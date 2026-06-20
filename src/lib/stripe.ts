import Stripe from 'stripe'

// Derive the exact apiVersion type from the installed SDK's constructor.
type StripeOptions = NonNullable<ConstructorParameters<typeof Stripe>[1]>
type StripeApiVersion = StripeOptions['apiVersion']

// The real key lives in .env.local (STRIPE_SECRET_KEY) and is used at runtime.
// The placeholder only prevents `next build` from crashing when the secret is
// not present at build time (e.g. CI). It is never used to make real requests.
const secretKey = process.env.STRIPE_SECRET_KEY ?? 'sk_test_placeholder_build_only'

export const stripe = new Stripe(secretKey, {
  // Pinned per ELEVON spec; the installed SDK's types only reflect its latest version.
  apiVersion: '2024-04-10' as unknown as StripeApiVersion,
})
