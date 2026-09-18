import { Hero } from "@/components/landing/Hero"
import { Features } from "@/components/landing/Features"
import { Stats } from "@/components/landing/Stats"
import { Footer } from "@/components/landing/Footer"
import { Header } from "@/components/landing/Header"

export function Landing() {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main>
        <Hero />
        <Features />
        <Stats />
      </main>
      <Footer />
    </div>
  )
}