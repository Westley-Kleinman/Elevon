import { NextResponse } from 'next/server'
import { stripe } from '@/lib/stripe'

export const dynamic = 'force-dynamic'

interface CheckoutBody {
  mountain: string
  quantity: number
  notes: string
}

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as Partial<CheckoutBody>

    const mountain = (body.mountain ?? '').trim()
    const quantity = Math.min(Math.max(Math.floor(Number(body.quantity) || 1), 1), 99)
    const notes = (body.notes ?? '').toString().slice(0, 500)

    if (!mountain) {
      return NextResponse.json({ error: 'Mountain is required.' }, { status: 400 })
    }

    const origin =
      request.headers.get('origin') ??
      new URL(request.url).origin

    const session = await stripe.checkout.sessions.create({
      mode: 'payment',
      line_items: [
        {
          quantity,
          price_data: {
            currency: 'usd',
            unit_amount: 4900,
            product_data: {
              name: `ELEVON Topographic Map \u2013 ${mountain}`,
            },
          },
        },
      ],
      metadata: {
        mountain,
        notes,
      },
      success_url: `${origin}/success?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${origin}/order`,
    })

    return NextResponse.json({ url: session.url })
  } catch (err) {
    console.error('create-checkout error:', err)
    return NextResponse.json(
      { error: 'Unable to create checkout session.' },
      { status: 500 },
    )
  }
}
