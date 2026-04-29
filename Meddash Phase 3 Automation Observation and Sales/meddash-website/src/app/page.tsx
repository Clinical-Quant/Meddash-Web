import Header from "@/components/ui/Header";
import Hero from "@/components/sections/Hero";
import Features from "@/components/sections/Features";
import CatalystCalendarSection from "@/components/sections/CatalystCalendarSection";
import EnterpriseShowcase from "@/components/sections/EnterpriseShowcase";
import LeadFormSection from "@/components/sections/LeadFormSection";
import Footer from "@/components/sections/Footer";
import LiteCornerTab from "@/components/ui/LiteCornerTab";

export default function Home() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <Header />
      <main>
        <Hero />
        <Features />
        <CatalystCalendarSection />
        <EnterpriseShowcase />
        <LeadFormSection />
      </main>
      <Footer />
      <LiteCornerTab />
    </div>
  );
}
