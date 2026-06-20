import Nav from '@/components/Nav'
import Footer from '@/components/Footer'
import OrderForm from '@/components/OrderForm'

export const metadata = {
  title: 'Order Your Map — ELEVON',
}

export default function OrderPage() {
  return (
    <main className="bg-snow">
      <Nav />

      <section className="mx-auto max-w-[1400px] px-6 pb-24 pt-28 md:px-10 md:pt-36">
        <OrderForm />
      </section>

      <Footer />
    </main>
  )
}
