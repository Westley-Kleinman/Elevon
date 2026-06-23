import Nav from '@/components/Nav'
import Footer from '@/components/Footer'
import OrderForm from '@/components/OrderForm'

export const metadata = {
  title: 'Order Your Map — ELEVON',
}

interface Props {
  searchParams: { id?: string; name?: string; lat?: string; lng?: string }
}

export default function OrderPage({ searchParams }: Props) {
  const initialId = searchParams.id ?? null
  const initialName = searchParams.name ?? ''
  const initialLat = searchParams.lat ? Number(searchParams.lat) : null
  const initialLng = searchParams.lng ? Number(searchParams.lng) : null

  return (
    <main className="bg-snow">
      <Nav />

      <section className="mx-auto max-w-[1400px] px-6 pb-24 pt-28 md:px-10 md:pt-36">
        <OrderForm
          initialId={initialId}
          initialName={initialName}
          initialLat={initialLat}
          initialLng={initialLng}
        />
      </section>

      <Footer />
    </main>
  )
}
