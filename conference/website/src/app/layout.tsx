import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = {
 title: "StudentIQ — Learning Performance Intelligence",
 description: "An explainable machine-learning research platform for early student performance analysis using the Open University Learning Analytics Dataset.",
 applicationName: "StudentIQ",
 keywords: ["learning analytics","student performance","machine learning","OULAD"]
};
export default function RootLayout({children}:{children:React.ReactNode}) {
 return <html lang="en"><body>{children}</body></html>;
}
