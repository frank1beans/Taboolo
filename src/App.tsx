import React from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate, Outlet } from "react-router-dom";
import { ThemeProvider } from "next-themes";
import { Layout } from "./components/Layout";
import AdminArea from "./pages/admin/AdminArea";
import Login from "./pages/auth/Login";
import Register from "./pages/auth/Register";
import CommessaAnalysisPage from "./pages/commesse/analysis/CommessaAnalysisPage";
import AnalisiAvanzate from "./pages/commesse/analysis/AnalisiAvanzate";
import CommessaLayout from "./pages/commesse/layout/CommessaLayout";
import CommessaDetail from "./pages/commesse/overview/CommessaDetail";
import CommessaPreventivoPage from "./pages/commesse/preventivo/CommessaPreventivoPage";
import PreventivoNew from "./pages/commesse/preventivo/PreventivoNew";
import ElencoPrezziNew from "./pages/commesse/pricing/ElencoPrezziNew";
import Commesse from "./pages/commesse/Commesse";
import CommessaSettings from "./pages/commesse/settings/CommessaSettings";
import CommessaWbsSettings from "./pages/commesse/settings/CommessaWbsSettings";
import NotFound from "./pages/errors/NotFound";
import Home from "./pages/home/Home";
import TestGrafici from "./pages/lab/TestGrafici";
import PriceCatalogExplorerNew from "./pages/price-catalog/PriceCatalogExplorerNew";
import Profile from "./pages/profile/Profile";
import Settings from "./pages/settings/Settings";
import { AuthProvider } from "./features/auth/AuthContext";
import { RequireAuth, RequireRole } from "./features/auth/RequireAuth";
import UnifiedImport from "./pages/import/UnifiedImport";

const queryClient = new QueryClient();

const ProtectedLayout = () => (
  <RequireAuth>
    <Layout>
      <Outlet />
    </Layout>
  </RequireAuth>
);

const App = () => (
  <QueryClientProvider client={queryClient}>
    <ThemeProvider attribute="class" defaultTheme="light" enableSystem>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <AuthProvider>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />

              <Route element={<ProtectedLayout />}>
                <Route path="/" element={<Home />} />
                <Route path="/commesse" element={<Commesse />} />
                <Route path="/commesse/:id" element={<Navigate to="/commesse/:id/overview" replace />} />
                <Route path="/commesse/:id/*" element={<CommessaLayout />}>
                  <Route index element={<Navigate to="overview" replace />} />
                  <Route path="overview" element={<CommessaDetail />} />
                  <Route path="import" element={<UnifiedImport />} />
                  <Route path="import-unificato" element={<UnifiedImport />} />
                  <Route path="price-catalog" element={<ElencoPrezziNew />} />
                  <Route path="elenco-prezzi" element={<Navigate to="price-catalog" replace />} />
                  <Route path="preventivo" element={<CommessaPreventivoPage />} />
                  <Route path="preventivo/:computoId" element={<PreventivoNew />} />
                  <Route path="analisi" element={<CommessaAnalysisPage />} />
                  <Route path="analisi/round/:roundParam" element={<CommessaAnalysisPage />} />
                  <Route path="analisi-avanzate" element={<AnalisiAvanzate />} />
                  <Route path="ritorni-batch" element={<UnifiedImport />} />
                  <Route path="wbs" element={<CommessaWbsSettings />} />
                  <Route path="settings" element={<CommessaSettings />} />
                </Route>
                <Route path="/elenco-prezzi" element={<PriceCatalogExplorerNew />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="/profile" element={<Profile />} />
                <Route
                  path="/admin"
                  element={
                    <RequireRole allowedRoles={["admin", "manager"]}>
                      <AdminArea />
                    </RequireRole>
                  }
                />
                <Route path="/test-grafici" element={<TestGrafici />} />
              </Route>

              <Route path="*" element={<NotFound />} />
            </Routes>
          </AuthProvider>
        </BrowserRouter>
      </TooltipProvider>
    </ThemeProvider>
  </QueryClientProvider>
);

export default App;
