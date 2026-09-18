"use client"

import { Shield, Scale, GitBranch, Mail } from "lucide-react"
import { Link } from "react-router-dom"

export function Footer() {
  const currentYear = new Date().getFullYear()

  const navGroups = {
    Product: [
      { label: "Document X-Ray", href: "#" },
      { label: "Contract Compare", href: "#" },
      { label: "Lawyer Briefs", href: "#" },
      { label: "Legal Q&A", href: "#" },
      { label: "Pricing", href: "#" },
    ],
    Company: [
      { label: "About", href: "#" },
      { label: "Blog", href: "#" },
      { label: "Careers", href: "#" },
      { label: "Press", href: "#" },
      { label: "Contact", href: "#" },
    ],
    Resources: [
      { label: "Documentation", href: "#" },
      { label: "API Reference", href: "#" },
      { label: "Security", href: "#" },
      { label: "Compliance", href: "#" },
      { label: "Status", href: "#" },
    ],
    Legal: [
      { label: "Privacy Policy", href: "#" },
      { label: "Terms of Service", href: "#" },
      { label: "Cookie Policy", href: "#" },
      { label: "DPA", href: "#" },
    ],
  }

  const socialLinks = [
    { icon: GitBranch, href: "#", label: "GitHub" },
    { icon: Mail, href: "#", label: "Email" },
  ]

  return (
    <footer className="bg-legal-navy text-white border-t border-white/10">
      <div className="max-w-7xl mx-auto px-6 py-16">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-8 mb-12">
          <div className="md:col-span-2">
            <div className="flex items-center gap-2 mb-4">
              <Shield className="h-8 w-8 text-primary" />
              <span className="font-display text-xl font-bold">LegalLens</span>
            </div>
            <p className="text-blue-300 max-w-sm mb-6 leading-relaxed">
              Evidence-first AI for understanding legal documents. Built for lawyers,
              compliance teams, and business professionals who need precision.
            </p>
            <div className="flex gap-4">
              {socialLinks.map((social) => (
                <a
                  key={social.label}
                  href={social.href}
                  className="text-blue-300 hover:text-white transition-colors"
                  aria-label={social.label}
                >
                  <social.icon className="h-5 w-5" />
                </a>
              ))}
            </div>
          </div>

          {Object.entries(navGroups).map(([title, links]) => (
            <div key={title}>
              <h4 className="font-semibold text-white mb-4">{title}</h4>
              <ul className="space-y-3">
                {links.map((link) => (
                  <li key={link.label}>
                    <Link
                      to={link.href}
                      className="text-blue-300 hover:text-white transition-colors text-sm"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="pt-8 border-t border-white/10 flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-blue-400 text-sm">
            © {currentYear} LegalLens. All rights reserved.
          </p>
          <div className="flex items-center gap-6 text-sm text-blue-400">
            <span className="flex items-center gap-1">
              <Shield className="h-4 w-4" />
              SOC 2 Type II
            </span>
            <span className="flex items-center gap-1">
              <Scale className="h-4 w-4" />
              GDPR Compliant
            </span>
          </div>
        </div>
      </div>
    </footer>
  )
}