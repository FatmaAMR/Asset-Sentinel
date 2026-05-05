import { Routes, Route, Navigate } from "react-router-dom";
import PropTypes from 'prop-types';
import AlertsSidebar from "./Components/AlertsSideBar";
import AssetsCard from "./Components/AssetsCards";
import Navbar from "./Components/Navbar";
import StatusCard from "./Components/StatusCards";

import AssetDiagnosis from "./pages/AssetDiagnosis";
import KnowledgeBase from "./pages/KnowledgeBase";
import HistoryTrends from "./pages/HistoryTrends";
import Config from "./pages/Config";
import ExportReport from "./pages/ExportReport";
import VibrationStream from "./Components/vibrationStream";
import Footer from "./Components/Footer";

import Login from "./pages/Login";
import Assets from "./pages/Assets";
import Thresholds from "./pages/Thresholds";
import useManagerialStore from "./stores/managerialStore";

function ProtectedRoute({ children }) {
  const token = useManagerialStore((state) => state.token);
  return token ? children : <Navigate to="/login" />;
}

ProtectedRoute.propTypes = {
  children: PropTypes.node.isRequired,
};

export default function App() {
  return (
    <div className="bg-light min-h-screen text-slate-900">
      <Navbar />

      <Routes>
    
        <Route
          path="/"
          element={
            <main className="max-w-[1440px] mx-auto px-6 py-8">
              <StatusCard />
              <div className="grid grid-cols-12 gap-8">
                <div className="col-span-12 lg:col-span-9 space-y-8">
                  <AssetsCard />
                  <VibrationStream />
                </div>
                <div className="col-span-12 lg:col-span-3">
                  <AlertsSidebar />

                </div>

              </div>
            </main>
          }
        />

  
        <Route path="/diagnosis" element={<AssetDiagnosis />} />
        <Route path="/knowledge" element={<KnowledgeBase />} />
        <Route path="/history" element={<HistoryTrends />} />

        <Route path="/config" element={<Config />} />
        <Route path="/export" element={<ExportReport />} />

        <Route path="/login" element={<Login />} />

        <Route path="/assets" element={<ProtectedRoute><Assets /></ProtectedRoute>} />
        <Route path="/thresholds" element={<ProtectedRoute><Thresholds /></ProtectedRoute>} />
      </Routes>

      <Footer />
    </div>
  );

}
