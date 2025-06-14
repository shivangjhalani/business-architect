import { BrowserRouter as Router, Routes, Route } from "react-router-dom"
import { MainLayout } from "@/components/layout/MainLayout"
import { CapabilityMapPage, BusinessGoalsPage, AnalysisPage, AIAssistantPage } from "@/pages"

function App() {
  return (
    <Router>
      <MainLayout>
        <Routes>
          <Route path="/" element={<CapabilityMapPage />} />
          <Route path="/goals" element={<BusinessGoalsPage />} />
          <Route path="/analysis" element={<AnalysisPage />} />
          <Route path="/analysis/:goalId" element={<AnalysisPage />} />
          <Route path="/assistant" element={<AIAssistantPage />} />
        </Routes>
      </MainLayout>
    </Router>
  )
}

export default App
