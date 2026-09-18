"use client"

import * as React from "react"
import { motion } from "framer-motion"
import { cn } from "@/lib/utils"

interface TextRevealProps {
  className?: string
  children: string
  delay?: number
  duration?: number
  splitBy?: "words" | "chars" | "lines"
}

export function TextReveal({
  className,
  children,
}: TextRevealProps) {
  const splitText = (text: string) => {
    return text.split(" ").map((word, i) => (
      <span key={i} className="inline-block">
        {word} {i < text.split(" ").length - 1 && "\u00A0"}
      </span>
    ))
  }

  return (
    <span className={cn("inline-block", className)}>
      {splitText(children).map((child, i) =>
        React.cloneElement(child as React.ReactElement<{ className?: string }>, {
          key: i,
          className: cn((child as React.ReactElement<{ className?: string }>).props.className || ""),
        })
      )}
    </span>
  )
}

interface AnimatedTextProps {
  className?: string
  children: string
  delay?: number
  duration?: number
}

export function AnimatedText({
  className,
  children,
  delay = 0,
  duration = 0.5,
}: AnimatedTextProps) {
  const words = children.split(" ").map((word, i) => (
    <motion.span
      key={i}
      initial={{ opacity: 0, y: 20, rotateX: -90 }}
      animate={{ opacity: 1, y: 0, rotateX: 0 }}
      transition={{ duration, delay: delay + i * 0.05, ease: "easeOut" }}
      className="inline-block"
    >
      {word} {i < children.split(" ").length - 1 && "\u00A0"}
    </motion.span>
  ))

  return <span className={cn("inline-block", className)}>{words}</span>
}

interface CounterProps {
  className?: string
  from?: number
  to: number
  duration?: number
  decimals?: number
  suffix?: string
  prefix?: string
}

export function Counter({
  className,
  from = 0,
  to,
  duration = 2,
  decimals = 0,
  suffix = "",
  prefix = "",
}: CounterProps) {
  const [count, setCount] = React.useState(from)
  const ref = React.useRef<HTMLDivElement>(null)

  React.useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          let frame: number
          const startTime = performance.now()
          const animate = (time: number) => {
            const progress = Math.min((time - startTime) / (duration * 1000), 1)
            const eased = 1 - Math.pow(1 - progress, 3)
            const current = from + (to - from) * eased
            setCount(Math.floor(current * Math.pow(10, decimals)) / Math.pow(10, decimals))
            if (progress < 1) {
              frame = requestAnimationFrame(animate)
            } else {
              setCount(to)
            }
          }
          frame = requestAnimationFrame(animate)
          return () => cancelAnimationFrame(frame)
        }
      },
      { threshold: 0.5 }
    )

    if (ref.current) observer.observe(ref.current)
    return () => observer.disconnect()
  }, [from, to, duration, decimals])

  return (
    <div ref={ref} className={cn("font-display font-semibold", className)}>
      {prefix}{count.toLocaleString()}{suffix}
    </div>
  )
}

interface FloatingProps {
  className?: string
  children: React.ReactNode
  amplitude?: number
  period?: number
}

export function Floating({
  className,
  children,
  amplitude = 10,
  period = 3,
}: FloatingProps) {
  return (
    <motion.div
      className={cn("inline-block", className)}
      animate={{ y: [-amplitude, amplitude, -amplitude] }}
      transition={{ duration: period, repeat: Infinity, ease: "easeInOut" }}
    >
      {children}
    </motion.div>
  )
}

interface ShimmerProps {
  className?: string
  children?: React.ReactNode
  width?: string
  height?: string
}

export function Shimmer({
  className,
  children,
  width = "100%",
  height = "100%",
}: ShimmerProps) {
  return (
    <div
      className={cn("relative overflow-hidden bg-muted", className)}
      style={{ width, height }}
    >
      <div
        className="absolute inset-0"
        style={{
          background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent)",
          animation: "shimmer 2s infinite",
        }}
      />
      {children}
    </div>
  )
}

interface RevealProps {
  className?: string
  children: React.ReactNode
  delay?: number
}

export function Reveal({
  className,
  children,
  delay = 0,
}: RevealProps) {
  const ref = React.useRef<HTMLDivElement>(null)
  const [visible, setVisible] = React.useState(false)

  React.useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true)
        }
      },
      { threshold: 0.1 }
    )
    if (ref.current) observer.observe(ref.current)
    return () => observer.disconnect()
  }, [])

  return (
    <motion.div
      ref={ref}
      className={className}
      initial={{ opacity: 0, y: 20 }}
      animate={visible ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
      transition={{ duration: 0.6, delay, ease: "easeOut" }}
    >
      {children}
    </motion.div>
  )
}