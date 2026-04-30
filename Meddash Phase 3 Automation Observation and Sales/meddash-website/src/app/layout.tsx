import type { Metadata } from "next";
import Script from "next/script";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  metadataBase: new URL("https://meddash.ai"),
  title: "Meddash.ai | Therapeutic Intelligence",
  description:
    "Meddash.ai delivers therapeutic intelligence for biotech teams with KOL briefs, catalyst tracking, and clinical-trial search in one decision-ready platform.",
  alternates: {
    canonical: "/",
  },
  openGraph: {
    title: "Meddash.ai | Therapeutic Intelligence",
    description:
      "KOL intelligence, biotech catalyst tracking, and clinical-trial search — unified into one high-signal decision layer.",
    url: "https://meddash.ai",
    siteName: "Meddash.ai",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Meddash.ai | Therapeutic Intelligence",
    description:
      "Decision-ready KOL, catalyst, and trial intelligence for biotech teams.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const gaMeasurementId = process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID;

  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        {children}
        {gaMeasurementId ? (
          <>
            <Script
              src={`https://www.googletagmanager.com/gtag/js?id=${gaMeasurementId}`}
              strategy="afterInteractive"
            />
            <Script id="ga4-init" strategy="afterInteractive">
              {`
                window.dataLayer = window.dataLayer || [];
                function gtag(){dataLayer.push(arguments);}
                window.gtag = gtag;
                gtag('js', new Date());
                gtag('config', '${gaMeasurementId}');
              `}
            </Script>
          </>
        ) : null}
      </body>
    </html>
  );
}
