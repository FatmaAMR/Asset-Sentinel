

import PageHeader from "../Components/Knowledge/PageHeader";
import UploadCard from "../Components/Knowledge/UploadCard";
import DocumentLibrary from "../Components/Knowledge/DocumentLibrary";
import ContextExplorer from "../Components/Knowledge/ContextExplorer";
import StatsRow from "../Components/Knowledge/StatsRow";
import CTASection from "../Components/Knowledge/CTASection";


export default function KnowledgeBase() {
  

  return (
    <div className="bg-light  text-slate-900 min-h-screen ">
      

      <main className="max-w-7xl mx-auto px-6 py-12 flex-1">
        <PageHeader />

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          <div className="lg:col-span-8 space-y-8">
            <UploadCard />
            <DocumentLibrary />
          </div>

          <div className="lg:col-span-4">
            <ContextExplorer />
          </div>
        </div>

        <StatsRow />
        <CTASection />
      </main>

      
    </div>
  );
}
