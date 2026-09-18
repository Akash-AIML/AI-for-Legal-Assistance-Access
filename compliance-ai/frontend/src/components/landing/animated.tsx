"use client"

import * as React from "react"
import { motion } from "framer-motion"
import { cn } from "@/lib/utils"

interface SpotlightProps {
  className?: string
  children: React.ReactNode
  opacity?: number
  color?: string
}

export function Spotlight({
  className,
  children,
  opacity = 0.5,
  color = "hsl(var(--primary))",
}: SpotlightProps) {
  const [position, setPosition] = React.useState({ x: 0, y: 0 })
  const ref = React.useRef<HTMLDivElement>(null)

  React.useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      const rect = ref.current?.getBoundingClientRect()
      if (rect) {
        setPosition({
          x: e.clientX - rect.left,
          y: e.clientY - rect.top,
        })
      }
    }

    const el = ref.current
    el?.addEventListener("mousemove", handleMouseMove)
    return () => el?.removeEventListener("mousemove", handleMouseMove)
  }, [])

  return (
    <div ref={ref} className={cn("relative overflow-hidden", className)}>
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background: `radial-gradient(600px circle at ${position.x}px ${position.y}px, ${color}${Math.floor(opacity * 255).toString(16).padStart(2, "0")}, transparent 60%)`,
        }}
      />
      {children}
    </div>
  )
}

interface MovingBorderProps {
  className?: string
  children: React.ReactNode
  color?: string
  speed?: number
}

export function MovingBorder({
  className,
  children,
  color = "hsl(var(--primary))",
  speed = 3,
}: MovingBorderProps) {
  const [progress, setProgress] = React.useState(0)

  React.useEffect(() => {
    let frame: number
    const animate = () => {
      setProgress((p) => (p + 0.001 * speed) % 1)
      frame = requestAnimationFrame(animate)
    }
    frame = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(frame)
  }, [speed])

  return (
    <div
      className={cn("relative rounded-lg overflow-hidden", className)}
      style={{
        background: `conic-gradient(from ${progress * 360}deg, ${color}, transparent 30%, ${color})`,
      }}
    >
      <div className="bg-background rounded-[inherit] p-[1px]">
        {children}
      </div>
    </div>
  )
}

interface GradientTextProps {
  className?: string
  children: React.ReactNode
  colors?: string[]
}

export function GradientText({
  className,
  children,
  colors = ["hsl(var(--primary))", "hsl(var(--accent-foreground))"],
}: GradientTextProps) {
  return (
    <span
      className={cn("bg-clip-text text-transparent bg-gradient-to-r", className)}
      style={{
        backgroundImage: `linear-gradient(to right, ${colors.join(", ")})`,
      }}
    >
      {children}
    </span>
  )
}

interface ScrollRevealProps {
  className?: string
  children: React.ReactNode
  delay?: number
  duration?: number
  direction?: "up" | "down" | "left" | "right"
}

export function ScrollReveal({
  className,
  children,
  delay = 0,
  duration = 0.6,
  direction = "up",
}: ScrollRevealProps) {
  const ref = React.useRef<HTMLDivElement>(null)
  const [isVisible, setIsVisible] = React.useState(false)

  React.useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true)
          observer.disconnect()
        }
      },
      { threshold: 0.1, rootMargin: "50px" }
    )

    if (ref.current) observer.observe(ref.current)
    return () => observer.disconnect()
  }, [])

  const transforms = {
    up: { initial: { opacity: 0, y: 30 }, visible: { opacity: 1, y: 0 } },
    down: { initial: { opacity: 0, y: -30 }, visible: { opacity: 1, y: 0 } },
    left: { initial: { opacity: 0, x: 30 }, visible: { opacity: 1, x: 0 } },
    right: { initial: { opacity: 0, x: -30 }, visible: { opacity: 1, x: 0 } },
  }

  return (
    <div ref={ref} className={className}>
      <motion.div
        initial={transforms[direction].initial}
        animate={isVisible ? transforms[direction].visible : transforms[direction].initial}
        transition={{ duration, delay, ease: "easeOut" }}
      >
        {children}
      </motion.div>
    </div>
  )
}

interface StaggerContainerProps {
  className?: string
  children: React.ReactNode
  staggerDelay?: number
}

export function StaggerContainer({
  className,
  children,
  staggerDelay = 0.1,
}: StaggerContainerProps) {
  return (
    <motion.div
      className={className}
      initial="hidden"
      animate="visible"
      variants={{
        hidden: { opacity: 0 },
        visible: {
          opacity: 1,
          transition: { staggerChildren: staggerDelay },
        },
      }}
    >
      {children}
    </motion.div>
  )
}

interface StaggerItemProps {
  className?: string
  children: React.ReactNode
  direction?: "up" | "down" | "left" | "right"
}

export function StaggerItem({
  className,
  children,
  direction = "up",
}: StaggerItemProps) {
  const transforms = {
    up: { hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } },
    down: { hidden: { opacity: 0, y: -20 }, visible: { opacity: 1, y: 0 } },
    left: { hidden: { opacity: 0, x: 20 }, visible: { opacity: 1, x: 0 } },
    right: { hidden: { opacity: 0, x: -20 }, visible: { opacity: 1, x: 0 } },
  }

  return (
    <motion.div
      className={className}
      variants={transforms[direction]}
      transition={{ duration: 0.5, ease: "easeOut" }}
    >
      {children}
    </motion.div>
  )
}