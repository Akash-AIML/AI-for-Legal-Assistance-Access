"use client"

import { ScrollReveal, StaggerContainer, StaggerItem } from "@/components/landing/animated"
import { Counter } from "@/components/landing/text-effects"

const stats = [
  { value: 94, suffix: "%", label: "Accuracy on clause classification" },
  { value: 87, suffix: "%", label: "Time saved on document review" },
  { value: 12, suffix: "+", label: "Supported clause types" },
  { value: 50, suffix: "K+", label: "Documents analyzed in beta" },
]

export function Stats() {
  return (
    <section className="py-24 px-6 bg-legal-blue/95">
      <div className="max-w-7xl mx-auto">
        <div className="text-center max-w-2xl mx-auto mb-16">
          <h2 className="font-display text-4xl md:text-5xl font-bold text-white mb-4">
            Trusted by legal teams worldwide
          </h2>
          <p className="text-lg text-blue-100 leading-relaxed">
            Real results from firms and in-house teams using LegalLens to accelerate their workflows.
          </p>
        </div>

        <StaggerContainer staggerDelay={0.15} className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats.map((stat) => (
            <StaggerItem key={stat.label} direction="up">
              <div className="text-center">
                <Counter
                  className="font-display text-5xl md:text-6xl font-bold text-white mb-2"
                  from={0}
                  to={stat.value}
                  duration={2}
                  decimals={0}
                  suffix={stat.suffix}
                />
                <p className="text-blue-100 text-sm md:text-base font-medium">{stat.label}</p>
              </div>
            </StaggerItem>
          ))}
        </StaggerContainer>

        <div className="mt-16 pt-16 border-t border-white/10">
          <ScrollReveal className="max-w-3xl mx-auto">
            <div className="bg-white/5 rounded-2xl p-8 md:p-12 text-center">
              <h3 className="font-display text-2xl md:text-3xl font-bold text-white mb-4">
                Ready to transform your document review?
              </h3>
              <p className="text-blue-100 mb-8 max-w-xl mx-auto">
                Join 500+ legal professionals who already use LegalLens to work faster and more confidently.
              </p>
              <a
                href="/login"
                className="inline-flex items-center gap-2 px-8 py-3 rounded-lg bg-white text-legal-navy font-semibold hover:bg-white/90 transition-colors"
              >
                Start Free Analysis
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M5 12h14M12 5l7 7-7 7" />
                </svg>
              </a>
            </div>
          </ScrollReveal>
        </div>
      </div>
    </section>
  )
}