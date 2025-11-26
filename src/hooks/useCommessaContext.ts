import { useOutletContext } from "react-router-dom";
import { CommessaOutletContext } from "@/pages/commesse/layout/CommessaLayout";

export function useCommessaContext() {
  return useOutletContext<CommessaOutletContext>();
}
