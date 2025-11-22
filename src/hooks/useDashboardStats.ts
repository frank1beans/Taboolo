import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import { ApiDashboardStats } from "@/types/api";

interface DashboardActivityEntry {
  action: string;
  commessa: string;
  time: string;
}

export interface DashboardStats {
  commesseAttive: number;
  computiCaricati: number;
  ritorni: number;
  reportGenerati: number;
  attivitaRecente: DashboardActivityEntry[];
}

export function useDashboardStats() {
  return useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: async (): Promise<DashboardStats> => {
      const stats = await api.getDashboardStats();
      return mapDashboardStats(stats);
    },
  });
}

function mapDashboardStats(apiStats: ApiDashboardStats): DashboardStats {
  const attivitaRecente = apiStats.attivita_recente.slice(0, 5).map((item) => ({
    action: item.tipo === "progetto" ? "Caricato computo" : "Nuovo ritorno gara",
    commessa: `${item.commessa_codice} - ${item.commessa_nome}`,
    time: getRelativeTime(new Date(item.created_at)),
  }));

  return {
    commesseAttive: apiStats.commesse_attive ?? 0,
    computiCaricati: apiStats.computi_caricati ?? 0,
    ritorni: apiStats.ritorni ?? 0,
    reportGenerati: apiStats.report_generati ?? 0,
    attivitaRecente,
  };
}

function getRelativeTime(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "Appena ora";
  if (diffMins < 60) return `${diffMins} ${diffMins === 1 ? "minuto" : "minuti"} fa`;
  if (diffHours < 24) return `${diffHours} ${diffHours === 1 ? "ora" : "ore"} fa`;
  if (diffDays === 1) return "1 giorno fa";
  if (diffDays < 30) return `${diffDays} giorni fa`;
  return date.toLocaleDateString("it-IT");
}
