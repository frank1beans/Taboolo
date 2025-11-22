import { useOutletContext } from "react-router-dom";
import { CommessaOutletContext } from "@/pages/CommessaLayout";

export function useCommessaContext() {
  return useOutletContext<CommessaOutletContext>();
}
