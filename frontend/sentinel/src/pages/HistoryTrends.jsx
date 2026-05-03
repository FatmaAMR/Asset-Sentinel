
import FiltersSidebar from "../Components/HistoryTrends/FiltersSidebar";
import AIInsightCard from "../Components/HistoryTrends/AIInsightCard";
import TrendVisualization from "../Components/HistoryTrends/TrendVisualization";
import HistoricalTimeline from "../Components/HistoryTrends/HistoricalTimeline";
import BottomStats from "../Components/HistoryTrends/BottomStats";


export default function HistoryTrends() {
  

  

  return (
    <div className="bg-light text-slate-900 min-h-screen ">
      
      <main className="max-w-[1600px] mx-auto p-6 grid grid-cols-12 gap-6">
        <aside className="col-span-12 lg:col-span-3 space-y-6">
          <FiltersSidebar />
          <AIInsightCard />
        </aside>

        <div className="col-span-12 lg:col-span-9 space-y-6">
          <TrendVisualization />
          <HistoricalTimeline />
          <BottomStats />
        </div>
      </main>


    </div>
  );
}
