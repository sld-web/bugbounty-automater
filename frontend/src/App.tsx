import { Routes, Route, Navigate } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import TargetDetail from './pages/TargetDetail'
import ProgramList from './pages/ProgramList'
import Approvals from './pages/Approvals'
import Settings from './pages/Settings'
import Layout from './components/Layout'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="targets/:targetId" element={<TargetDetail />} />
        <Route path="programs" element={<ProgramList />} />
        <Route path="approvals" element={<Approvals />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  )
}
