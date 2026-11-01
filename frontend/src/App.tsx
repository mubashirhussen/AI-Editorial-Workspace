import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { DashboardLayout } from './components/layout/DashboardLayout';
import { LoadingState } from './components/common/LoadingState';

// Lazy-load route components to optimize initial bundle size & page speed
const DashboardPage = lazy(() =>
  import('./pages/DashboardPage').then((m) => ({ default: m.DashboardPage }))
);
const ResearchPage = lazy(() =>
  import('./pages/ResearchPage').then((m) => ({ default: m.ResearchPage }))
);
const WritingPage = lazy(() =>
  import('./pages/WritingPage').then((m) => ({ default: m.WritingPage }))
);
const EditorialPage = lazy(() =>
  import('./pages/EditorialPage').then((m) => ({ default: m.EditorialPage }))
);
const ProjectsPage = lazy(() =>
  import('./pages/ProjectsPage').then((m) => ({ default: m.ProjectsPage }))
);
const SettingsPage = lazy(() =>
  import('./pages/SettingsPage').then((m) => ({ default: m.SettingsPage }))
);
const OrganizationPage = lazy(() =>
  import('./pages/OrganizationPage').then((m) => ({ default: m.OrganizationPage }))
);
import { AuthProvider } from './context/AuthContext';

const ViewSuspenseFallback: React.FC = () => (
  <div className="flex h-[60vh] w-full items-center justify-center p-8">
    <LoadingState message="Loading module view..." />
  </div>
);

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
        <Route element={<DashboardLayout />}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route
            path="/dashboard"
            element={
              <Suspense fallback={<ViewSuspenseFallback />}>
                <DashboardPage />
              </Suspense>
            }
          />

          {/* Research Routes */}
          <Route
            path="/research"
            element={
              <Suspense fallback={<ViewSuspenseFallback />}>
                <ResearchPage />
              </Suspense>
            }
          />
          <Route
            path="/research/:projectId"
            element={
              <Suspense fallback={<ViewSuspenseFallback />}>
                <ResearchPage />
              </Suspense>
            }
          />

          {/* Writing Routes */}
          <Route
            path="/writing"
            element={
              <Suspense fallback={<ViewSuspenseFallback />}>
                <WritingPage />
              </Suspense>
            }
          />
          <Route
            path="/writing/:draftId"
            element={
              <Suspense fallback={<ViewSuspenseFallback />}>
                <WritingPage />
              </Suspense>
            }
          />

          {/* Editorial Routes */}
          <Route
            path="/editorial"
            element={
              <Suspense fallback={<ViewSuspenseFallback />}>
                <EditorialPage />
              </Suspense>
            }
          />
          <Route
            path="/editorial/:editorialId"
            element={
              <Suspense fallback={<ViewSuspenseFallback />}>
                <EditorialPage />
              </Suspense>
            }
          />

          {/* Projects & Settings */}
          <Route
            path="/projects"
            element={
              <Suspense fallback={<ViewSuspenseFallback />}>
                <ProjectsPage />
              </Suspense>
            }
          />
          <Route
            path="/settings"
            element={
              <Suspense fallback={<ViewSuspenseFallback />}>
                <SettingsPage />
              </Suspense>
            }
          />
          <Route
            path="/organization"
            element={
              <Suspense fallback={<ViewSuspenseFallback />}>
                <OrganizationPage />
              </Suspense>
            }
          />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Route>
      </Routes>
    </AuthProvider>
  </BrowserRouter>
  );
};

export default App;
