import { Routes, Route, Navigate, useParams } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import TargetDetail from './pages/TargetDetail'
import ProgramList from './pages/ProgramList'
import ProgramDetail from './pages/ProgramDetail'
import ProgramImport from './pages/ProgramImport'
import ProgramIngestionWizard from './pages/ProgramIngestionWizard'
import WorkflowVisualization from './pages/WorkflowVisualization'
import AICommandCenter from './pages/AICommandCenter'
import Approvals from './pages/Approvals'
import Settings from './pages/Settings'
import Integrations from './pages/Integrations'
import Targets from './pages/Targets'
import Plugins from './pages/Plugins'
import Findings from './pages/Findings'
import Intel from './pages/Intel'
import Jobs from './pages/Jobs'
import CustomHeaders from './pages/CustomHeaders'
import Testing from './pages/Testing'
import Layout from './components/Layout'

function WorkflowWrapper() {
  const { programId } = useParams<{ programId: string }>()
  return <WorkflowVisualization programId={programId!} />
}

function AIWrapper() {
  const { programId } = useParams<{ programId: string }>()
  return <AICommandCenter programId={programId!} />
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="targets" element={<Targets />} />
        <Route path="targets/:targetId" element={<TargetDetail />} />
        <Route path="programs" element={<ProgramList />} />
        <Route path="programs/:programId" element={<ProgramDetail />} />
        <Route path="programs/:programId/workflow" element={<WorkflowWrapper />} />
        <Route path="programs/:programId/ai" element={<AIWrapper />} />
        <Route path="programs/import" element={<ProgramImport />} />
        <Route path="programs/wizard" element={<ProgramIngestionWizard />} />
        <Route path="approvals" element={<Approvals />} />
        <Route path="integrations" element={<Integrations />} />
        <Route path="plugins" element={<Plugins />} />
        <Route path="findings" element={<Findings />} />
        <Route path="intel" element={<Intel />} />
        <Route path="jobs" element={<Jobs />} />
        <Route path="headers" element={<CustomHeaders />} />
        <Route path="testing" element={<Testing />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  )
}
