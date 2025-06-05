import { BrowserRouter as Router, Routes, Route } from "react-router-dom"
import { MainLayout } from "@/components/layout/MainLayout"
import { CapabilityMapPage, BusinessGoalsPage, AnalysisPage } from "@/pages"

function App() {
  return (
    <Router>
      <MainLayout>
        <Routes>
          <Route path="/" element={<CapabilityMapPage />} />
          <Route path="/goals" element={<BusinessGoalsPage />} />
          <Route path="/analysis" element={<AnalysisPage />} />
        </Routes>
      </MainLayout>
    </Router>
  )
}

export default App
