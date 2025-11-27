import { Outlet, Navigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import { CommessaTabs } from "@/features/commessa";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiCommessaDetail } from "@/types/api";

export type CommessaOutletContext = {
  commessa?: ApiCommessaDetail;
  refetchCommessa: () => void;
};


export default function CommessaLayout() {
  const { id } = useParams();
  const commessaId = id ?? "";

  const {
    data: commessa,
    isLoading,
    refetch,
  } = useQuery({
    queryKey: ["commessa", commessaId, "layout"],
    queryFn: () => api.getCommessa(commessaId),
    enabled: Boolean(commessaId),
  });

  if (!commessaId) {
    return <Navigate to="/commesse" replace />;
  }

  return (
    <div className="workspace-shell">
      <div className="workspace-inner">
        <CommessaTabs commessa={commessa} isLoading={isLoading} />

        <div className="workspace-panel workspace-panel--scroll">
          {isLoading && !commessa ? (
            <div className="p-8">
              <Skeleton className="h-96 w-full rounded-xl" />
            </div>
          ) : (
            <div className="p-4 lg:p-6">
              <Outlet context={{ commessa, refetchCommessa: refetch }} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
