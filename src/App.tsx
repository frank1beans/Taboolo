import React from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate, Outlet } from "react-router-dom";
import { ThemeProvider } from "next-themes";
import { Layout } from "./components/Layout";
import Home from "./pages/Home";
import Commesse from "./pages/Commesse";
import Settings from "./pages/Settings";
import CommessaWbsSettings from "./pages/CommessaWbsSettings";
import CommessaSettings from "./pages/CommessaSettings";
import PreventivoNew from "./pages/PreventivoNew";
import ElencoPrezziNew from "./pages/ElencoPrezziNew";
import PriceCatalogExplorerNew from "./pages/PriceCatalogExplorerNew";
import CommessaLayout from "./pages/CommessaLayout";
import CommessaDetail from "./pages/CommessaDetail";
import CommessaAnalysisPage from "./pages/CommessaAnalysisPage";
import AnalisiAvanzate from "./pages/AnalisiAvanzate";
import CommessaPreventivoPage from "./pages/CommessaPreventivoPage";
import RitorniGaraBatch from "./pages/RitorniGaraBatch";
import TestGrafici from "./pages/TestGrafici";
import NotFound from "./pages/NotFound";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Profile from "./pages/Profile";
import AdminArea from "./pages/AdminArea";
import { AuthProvider } from "./features/auth/AuthContext";
import { RequireAuth, RequireRole } from "./features/auth/RequireAuth";

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
                  <Route path="price-catalog" element={<ElencoPrezziNew />} />
                  <Route path="elenco-prezzi" element={<Navigate to="price-catalog" replace />} />
                  <Route path="preventivo" element={<CommessaPreventivoPage />} />
                  <Route path="preventivo/:computoId" element={<PreventivoNew />} />
                  <Route path="analisi" element={<CommessaAnalysisPage />} />
                  <Route path="analisi/round/:roundParam" element={<CommessaAnalysisPage />} />
                  <Route path="analisi-avanzate" element={<AnalisiAvanzate />} />
                  <Route path="ritorni-batch" element={<RitorniGaraBatch />} />
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
