import SystemConfig from "../Components/Systemconfig";
import DataEngine from "../Components/DataEngine";
import LlmModels from "../Components/LlmModels";
import LocalHardware from "../Components/LocalHardware";
import Maintenancewindow from "../Components/Maintenancewindow";

export default function Config() {
  return (
    <div className="bg-light min-h-screen text-slate-900">
      <main className="max-w-7xl mx-auto px-6 py-10">
        <SystemConfig/>
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">

          <div className="lg:col-span-8 space-y-8">
            <DataEngine />
            <LlmModels />
          </div>


          <div className="lg:col-span-4">
            <LocalHardware />
          </div>

        </div>

        <Maintenancewindow/>

      </main>
    </div>
  );
}