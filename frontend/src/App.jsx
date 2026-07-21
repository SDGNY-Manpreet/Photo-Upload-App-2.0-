import { useState } from "react";
import Sidebar from "./components/Sidebar";
import ProcoreProjects from "./pages/ProcoreProjects";
import ShopifyOrders from "./pages/ShopifyOrders";
import SpecialProjects from "./pages/SpecialProjects";
import "./index.css";

export default function App() {
  const [activeTab, setActiveTab] = useState("procore");

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col md:flex-row font-sans text-slate-800 antialiased selection:bg-brand-200 selection:text-brand-900">
      {/* Sidebar / Top Nav on Mobile */}
      <Sidebar activeTab={activeTab} onChangeTab={setActiveTab} />
      
      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-h-[calc(100vh-130px)] md:min-h-screen md:h-screen w-full overflow-x-hidden md:overflow-y-auto">
        {/* Top subtle bar for visual balance (Desktop only) */}
        <header className="hidden md:flex h-20 border-b border-slate-200/60 bg-white/50 backdrop-blur-sm sticky top-0 z-30 items-center px-8 shrink-0">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-widest">
            <span>SDGNY Apps</span>
            <span className="text-slate-300">/</span>
            <span className="text-slate-800">
              {activeTab === "procore" && "Procore Projects"}
              {activeTab === "shopify" && "Shopify Orders"}
              {activeTab === "special" && "Special Projects"}
            </span>
          </div>
        </header>

        {/* Scrollable Canvas */}
        <div className="flex-1 p-4 sm:p-6 md:p-8 overflow-y-auto pb-24">
          {activeTab === "procore" && <ProcoreProjects />}
          {activeTab === "shopify" && <ShopifyOrders />}
          {activeTab === "special" && <SpecialProjects />}
        </div>
      </main>
    </div>
  );
}
