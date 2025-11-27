import { Home, FolderOpen, Settings, PackageSearch, Shield, Building2, Layers3, ListChecks, FolderKanban, ChevronRight } from "lucide-react";
import { NavLink, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { cn } from "@/lib/utils";
import { STATUS_CONFIG } from "@/lib/constants";
import logo from "@/assets/logo.png";
import { useAuth } from "@/features/auth/AuthContext";
import { api } from "@/lib/api-client";
import { ApiCommessa, CommessaStato } from "@/types/api";
import { useMemo, useState } from "react";

const baseItems = [
  { title: "HOME", url: "/", icon: Home },
  { title: "COMMESSE", url: "/commesse", icon: FolderOpen },
  { title: "ELENCO PREZZI", url: "/elenco-prezzi", icon: PackageSearch },
  { title: "IMPOSTAZIONI", url: "/settings", icon: Settings },
];

export function AppSidebar() {
  const { open } = useSidebar();
  const { user } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  
  const isCommessePage = location.pathname.startsWith("/commesse");
  const filterType = searchParams.get("filter");
  const filterValue = searchParams.get("value");

  const [commesseOpen, setCommesseOpen] = useState(isCommessePage);
  const [businessUnitOpen, setBusinessUnitOpen] = useState(false);
  const [statusOpen, setStatusOpen] = useState(false);

  const commesseQuery = useQuery<ApiCommessa[]>({
    queryKey: ["commesse"],
    queryFn: () => api.listCommesse(),
  });

  const commesse = useMemo(() => commesseQuery.data ?? [], [commesseQuery.data]);

  const businessUnitFolders = useMemo(() => {
    const map = new Map<string, { label: string; value: string | null; count: number }>();
    commesse.forEach((commessa) => {
      const value = commessa.business_unit?.trim() || null;
      const key = value ?? "__none__";
      if (!map.has(key)) {
        map.set(key, { label: value ?? "Senza Business Unit", value, count: 0 });
      }
      map.get(key)!.count++;
    });
    return Array.from(map.values()).sort((a, b) => a.label.localeCompare(b.label));
  }, [commesse]);

  const statusFolders = useMemo(() => {
    return (["setup", "in_corso", "chiusa"] as CommessaStato[]).map((status) => ({
      status,
      count: commesse.filter((c) => c.stato === status).length,
      label: STATUS_CONFIG[status].label,
      badgeVariant: STATUS_CONFIG[status].badgeVariant,
    }));
  }, [commesse]);

  const items = [
    ...baseItems,
    { title: "PROFILO", url: "/profile", icon: Settings },
    ...(user && ["admin", "manager"].includes(user.role)
      ? [{ title: "ADMIN", url: "/admin", icon: Shield }]
      : []),
  ];

  const handleFilterClick = (type: string, value: string | null) => {
    if (type === "root") {
      navigate("/commesse");
    } else {
      const params = new URLSearchParams();
      params.set("filter", type);
      if (value !== null) {
        params.set("value", value);
      }
      navigate(`/commesse?${params.toString()}`);
    }
  };

  const isFilterActive = (type: string, value?: string | null) => {
    if (type === "root") {
      return !filterType;
    }
    if (type === "businessUnit") {
      return filterType === "businessUnit" && filterValue === (value ?? null);
    }
    if (type === "status") {
      return filterType === "status" && filterValue === value;
    }
    return false;
  };

  return (
    <Sidebar collapsible="icon" className="border-r border-border/40">
      <SidebarContent className="bg-sidebar">
        {/* Logo Area - Clean and minimal */}
        <div className="border-b border-border/40 h-[69px] flex items-center">
          {open ? (
            <div className="px-6 w-full">
              <div className="flex items-center gap-3">
                <img
                  src={logo}
                  alt="Taboolo"
                  className="h-9 w-9 rounded-2xl"
                />
                <div>
                  <h2 className="font-semibold text-base text-foreground">
                    Taboolo
                  </h2>
                  <p className="text-[11px] text-muted-foreground font-normal">
                    Measure Maker
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex justify-center w-full">
              <img
                src={logo}
                alt="Taboolo"
                className="h-9 w-9 rounded-2xl"
              />
            </div>
          )}
        </div>

        {/* Tree Navigation */}
        <ScrollArea className="flex-1">
          <SidebarGroup className="px-2 py-2">
            <SidebarGroupContent>
              <SidebarMenu className="space-y-0.5">
                {/* Home */}
                <SidebarMenuItem>
                  <SidebarMenuButton asChild>
                    <NavLink
                      to="/"
                      end
                      className={({ isActive }) =>
                        `flex items-center gap-2 px-2 py-2 rounded transition-colors ${
                          isActive
                            ? "bg-primary/10 text-primary font-bold"
                            : "text-muted-foreground hover:text-foreground hover:bg-muted"
                        } ${!open ? "justify-center px-0" : ""}`
                      }
                    >
                      <Home className="h-4 w-4 flex-shrink-0" />
                      {open && <span className="text-xs font-bold tracking-wider">HOME</span>}
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>

                {/* Commesse - Collapsible Tree */}
                <Collapsible open={commesseOpen} onOpenChange={setCommesseOpen}>
                  <SidebarMenuItem>
                    <CollapsibleTrigger asChild>
                      <SidebarMenuButton
                        className={cn(
                          "flex items-center gap-2 px-2 py-2 rounded transition-colors w-full cursor-pointer",
                          isCommessePage
                            ? "bg-primary/10 text-primary font-bold"
                            : "text-muted-foreground hover:text-foreground hover:bg-muted",
                          !open && "justify-center px-0"
                        )}
                      >
                        <FolderOpen className="h-4 w-4 flex-shrink-0" />
                        {open && (
                          <>
                            <span className="text-xs font-bold tracking-wider flex-1 text-left">COMMESSE</span>
                            <ChevronRight
                              className={cn(
                                "h-3.5 w-3.5 flex-shrink-0 transition-transform",
                                commesseOpen && "rotate-90"
                              )}
                            />
                          </>
                        )}
                      </SidebarMenuButton>
                    </CollapsibleTrigger>
                  </SidebarMenuItem>

                  {open && (
                    <CollapsibleContent className="ml-4 space-y-1 mt-1">
                      {/* Tutte le cartelle */}
                      <SidebarMenuItem>
                        <SidebarMenuButton
                          onClick={() => handleFilterClick("root", null)}
                          className={cn(
                            "flex items-center gap-2 px-2 py-1.5 rounded transition-colors cursor-pointer text-xs",
                            isFilterActive("root")
                              ? "bg-primary/10 text-primary font-semibold"
                              : "text-muted-foreground hover:text-foreground hover:bg-muted"
                          )}
                        >
                          <FolderKanban className="h-3.5 w-3.5 flex-shrink-0" />
                          <span className="flex-1">Tutte le cartelle</span>
                          <span className="text-[10px] font-mono">{commesse.length}</span>
                        </SidebarMenuButton>
                      </SidebarMenuItem>

                      {/* Business Unit - Nested Collapsible */}
                      <Collapsible open={businessUnitOpen} onOpenChange={setBusinessUnitOpen}>
                        <SidebarMenuItem>
                          <CollapsibleTrigger asChild>
                            <SidebarMenuButton className="flex items-center gap-2 px-2 py-1.5 rounded transition-colors w-full cursor-pointer text-xs text-muted-foreground hover:text-foreground hover:bg-muted">
                              <Building2 className="h-3.5 w-3.5 flex-shrink-0" />
                              <span className="flex-1 text-left">Business Unit</span>
                              <ChevronRight
                                className={cn(
                                  "h-3 w-3 flex-shrink-0 transition-transform",
                                  businessUnitOpen && "rotate-90"
                                )}
                              />
                            </SidebarMenuButton>
                          </CollapsibleTrigger>
                        </SidebarMenuItem>

                        <CollapsibleContent className="ml-4 space-y-0.5 mt-0.5">
                          {businessUnitFolders.map((folder) => (
                            <SidebarMenuItem key={folder.value ?? "__none__"}>
                              <SidebarMenuButton
                                onClick={() => handleFilterClick("businessUnit", folder.value)}
                                className={cn(
                                  "flex items-center gap-2 px-2 py-1 rounded transition-colors cursor-pointer text-[11px]",
                                  isFilterActive("businessUnit", folder.value)
                                    ? "bg-primary/10 text-primary font-medium"
                                    : "text-muted-foreground hover:text-foreground hover:bg-muted"
                                )}
                              >
                                <span className="truncate flex-1">{folder.label}</span>
                                <span className="text-[10px] font-mono">{folder.count}</span>
                              </SidebarMenuButton>
                            </SidebarMenuItem>
                          ))}
                        </CollapsibleContent>
                      </Collapsible>

                      {/* Stato Commessa - Nested Collapsible */}
                      <Collapsible open={statusOpen} onOpenChange={setStatusOpen}>
                        <SidebarMenuItem>
                          <CollapsibleTrigger asChild>
                            <SidebarMenuButton className="flex items-center gap-2 px-2 py-1.5 rounded transition-colors w-full cursor-pointer text-xs text-muted-foreground hover:text-foreground hover:bg-muted">
                              <ListChecks className="h-3.5 w-3.5 flex-shrink-0" />
                              <span className="flex-1 text-left">Stato Commessa</span>
                              <ChevronRight
                                className={cn(
                                  "h-3 w-3 flex-shrink-0 transition-transform",
                                  statusOpen && "rotate-90"
                                )}
                              />
                            </SidebarMenuButton>
                          </CollapsibleTrigger>
                        </SidebarMenuItem>

                        <CollapsibleContent className="ml-4 space-y-0.5 mt-0.5">
                          {statusFolders.map((folder) => (
                            <SidebarMenuItem key={folder.status}>
                              <SidebarMenuButton
                                onClick={() => handleFilterClick("status", folder.status)}
                                className={cn(
                                  "flex items-center gap-2 px-2 py-1 rounded transition-colors cursor-pointer text-[11px]",
                                  isFilterActive("status", folder.status)
                                    ? "bg-primary/10 text-primary font-medium"
                                    : "text-muted-foreground hover:text-foreground hover:bg-muted"
                                )}
                              >
                                <span className="truncate flex-1">{folder.label}</span>
                                <span className="text-[10px] font-mono">{folder.count}</span>
                              </SidebarMenuButton>
                            </SidebarMenuItem>
                          ))}
                        </CollapsibleContent>
                      </Collapsible>
                    </CollapsibleContent>
                  )}
                </Collapsible>

                {/* Elenco Prezzi */}
                <SidebarMenuItem>
                  <SidebarMenuButton asChild>
                    <NavLink
                      to="/elenco-prezzi"
                      className={({ isActive }) =>
                        `flex items-center gap-2 px-2 py-2 rounded transition-colors ${
                          isActive
                            ? "bg-primary/10 text-primary font-bold"
                            : "text-muted-foreground hover:text-foreground hover:bg-muted"
                        } ${!open ? "justify-center px-0" : ""}`
                      }
                    >
                      <PackageSearch className="h-4 w-4 flex-shrink-0" />
                      {open && <span className="text-xs font-bold tracking-wider">ELENCO PREZZI</span>}
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>

                {/* Impostazioni */}
                <SidebarMenuItem>
                  <SidebarMenuButton asChild>
                    <NavLink
                      to="/settings"
                      className={({ isActive }) =>
                        `flex items-center gap-2 px-2 py-2 rounded transition-colors ${
                          isActive
                            ? "bg-primary/10 text-primary font-bold"
                            : "text-muted-foreground hover:text-foreground hover:bg-muted"
                        } ${!open ? "justify-center px-0" : ""}`
                      }
                    >
                      <Settings className="h-4 w-4 flex-shrink-0" />
                      {open && <span className="text-xs font-bold tracking-wider">IMPOSTAZIONI</span>}
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>

                {/* Profilo */}
                <SidebarMenuItem>
                  <SidebarMenuButton asChild>
                    <NavLink
                      to="/profile"
                      className={({ isActive }) =>
                        `flex items-center gap-2 px-2 py-2 rounded transition-colors ${
                          isActive
                            ? "bg-primary/10 text-primary font-bold"
                            : "text-muted-foreground hover:text-foreground hover:bg-muted"
                        } ${!open ? "justify-center px-0" : ""}`
                      }
                    >
                      <Settings className="h-4 w-4 flex-shrink-0" />
                      {open && <span className="text-xs font-bold tracking-wider">PROFILO</span>}
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>

                {/* Admin - Conditional */}
                {user && ["admin", "manager"].includes(user.role) && (
                  <SidebarMenuItem>
                    <SidebarMenuButton asChild>
                      <NavLink
                        to="/admin"
                        className={({ isActive }) =>
                          `flex items-center gap-2 px-2 py-2 rounded transition-colors ${
                            isActive
                              ? "bg-primary/10 text-primary font-bold"
                              : "text-muted-foreground hover:text-foreground hover:bg-muted"
                          } ${!open ? "justify-center px-0" : ""}`
                        }
                      >
                        <Shield className="h-4 w-4 flex-shrink-0" />
                        {open && <span className="text-xs font-bold tracking-wider">ADMIN</span>}
                      </NavLink>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                )}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        </ScrollArea>
      </SidebarContent>

      {/* Footer - Minimal */}
      <SidebarFooter className="border-t border-border/40 bg-sidebar">
        {open ? (
          <div className="px-4 py-3">
            <div className="text-muted-foreground/60">
              <p className="text-[10px] font-medium">
                Taboolo v1.0
              </p>
              <p className="text-[9px] mt-0.5">
                © 2024 Taboo
              </p>
            </div>
          </div>
        ) : (
          <div className="flex justify-center py-3">
            <div className="h-1 w-1 rounded-full bg-muted-foreground/30"></div>
          </div>
        )}
      </SidebarFooter>
    </Sidebar>
  );
}
