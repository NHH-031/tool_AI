import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Whiteboard Video Production Studio",
  description: "Xưởng sản xuất video hoạt hình Whiteboard tự động hóa bằng AI",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi" suppressHydrationWarning>
      <body className="antialiased min-h-screen flex flex-col" suppressHydrationWarning>
        {children}
      </body>
    </html>
  );
}
