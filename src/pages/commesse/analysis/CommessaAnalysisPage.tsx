import { useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ConfrontoOfferte } from "@/features/confronto";
import { useCommessaContext } from "@/hooks/useCommessaContext";

export default function CommessaAnalysisPage() {
  const { id, roundParam } = useParams<{ id: string; roundParam?: string }>();
  const navigate = useNavigate();
  const { commessa } = useCommessaContext();
  const commessaId = id ?? (commessa ? String(commessa.id) : undefined);
  const [selectedImpresa, setSelectedImpresa] = useState<"all" | string>("all");

  const selectedRound = useMemo(() => {
    if (!roundParam || roundParam.toLowerCase() === "all") {
      return "all" as const;
    }
    const parsed = Number(roundParam);
    return Number.isFinite(parsed) && parsed > 0 ? parsed : ("all" as const);
  }, [roundParam]);

  const handleRoundChange = (round: "all" | number) => {
    if (!commessaId || selectedRound === round) {
      return;
    }
    const slug = round === "all" ? "all" : String(round);
    navigate(`/commesse/${commessaId}/analisi/round/${slug}`, { replace: false });
  };

  if (!commessaId) {
    return null;
  }

  return (
    <div className="h-full overflow-hidden">
      <ConfrontoOfferte
        commessaId={commessaId}
        selectedRound={selectedRound}
        onRoundChange={handleRoundChange}
        selectedImpresa={selectedImpresa}
        onImpresaChange={setSelectedImpresa}
        onNavigateToCharts={() => navigate(`/commesse/${commessaId}/analisi-avanzate`)}
      />
    </div>
  );
}
