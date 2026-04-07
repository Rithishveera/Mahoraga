import type { Metadata } from "next"
import "@/styles/globals.css"
import Navbar from "@/components/layout/Navbar"
import { APP_TAGLINE } from "@/lib/constants"

export const metadata: Metadata = {
  title: "Mahoraga",
  description: APP_TAGLINE,
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Outfit:wght@300;400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-screen bg-[#080810] text-white font-sans antialiased">
        <Navbar />
        <main>{children}</main>
      </body>
    </html>
  )
}
