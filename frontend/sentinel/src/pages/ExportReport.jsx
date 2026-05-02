import AssetsData from "../Components/AssetsData";
import DiagnosisSummary from "../Components/DiagnosisSummary";
import ExportSidebar from "../Components/ExportSideBar";
import RecommendedActions from "../Components/RecommendedActions";
import ReportFooter from "../Components/ReportFooter";
import ReportHeader from "../Components/ReportHeader";
import TechnicalEvidence from "../Components/TechnicalEvidence";


export default function ExportReport() {
  return (
    <div className="flex min-h-screen bg-light">
      <ExportSidebar />
      <main className="flex-1 p-12 overflow-y-auto">
        <div className="max-w-[850px] mx-auto bg-cards-light shadow-2xl rounded-xl min-h-[1100px] flex flex-col p-12 border border-slate-100">
          <ReportHeader />
          <AssetsData />
          <DiagnosisSummary />
          <TechnicalEvidence />
          <RecommendedActions />
          <ReportFooter />
        </div>
      </main>

    </div>
  );
}