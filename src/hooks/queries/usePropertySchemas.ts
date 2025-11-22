import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import { queryKeys, staleTime } from "./index";
import type { PropertySchemaResponse } from "@/types/api";

export function usePropertySchemas() {
  return useQuery<PropertySchemaResponse>({
    queryKey: queryKeys.propertySchemas.all(),
    queryFn: () => api.getPropertySchemas(),
    staleTime: staleTime.static,
  });
}
