import { useMemo, useState } from "react";
import {
  BadgeCheck,
  Bell,
  Clock3,
  Copy,
  Download,
  MoreHorizontal,
  Pencil,
  Plus,
  Printer,
  Search,
  Send,
  ShoppingBag,
  Undo2,
  Wallet,
} from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";
import { Separator } from "@/components/ui/separator";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PageShell } from "@/components/layout/PageShell";
import { useAuth } from "@/features/auth/AuthContext";
import { cn } from "@/lib/utils";

type OrderStatus = "pending" | "completed" | "refunded" | "ongoing";
type PaymentStatus = "paid" | "unpaid";
type OrderFilter = "all" | "pending" | "completed" | "refunded" | "unpaid";

type OrderRow = {
  id: string;
  customer: string;
  customerRole?: string;
  location: string;
  orderDate: string;
  status: OrderStatus;
  total: number;
  paymentStatus: PaymentStatus;
  avatarSeed: string;
};

const ORDER_ROWS: OrderRow[] = [
  {
    id: "#ORD0008",
    customer: "Esther Klein",
    customerRole: "Brand lead",
    location: "Berlino, DE",
    orderDate: "2024-12-17",
    status: "pending",
    total: 10150,
    paymentStatus: "unpaid",
    avatarSeed: "EstherKlein",
  },
  {
    id: "#ORD0007",
    customer: "Denise Kuhn",
    customerRole: "Product ops",
    location: "Vienna, AT",
    orderDate: "2024-12-16",
    status: "pending",
    total: 10050,
    paymentStatus: "unpaid",
    avatarSeed: "DeniseKuhn",
  },
  {
    id: "#ORD0006",
    customer: "Clint Hoppe",
    customerRole: "Logistics lead",
    location: "Amsterdam, NL",
    orderDate: "2024-12-16",
    status: "completed",
    total: 6056,
    paymentStatus: "paid",
    avatarSeed: "ClintHoppe",
  },
  {
    id: "#ORD0005",
    customer: "Darin Deckow",
    customerRole: "CS owner",
    location: "Milano, IT",
    orderDate: "2024-12-16",
    status: "refunded",
    total: 9640.5,
    paymentStatus: "paid",
    avatarSeed: "DarinDeckow",
  },
  {
    id: "#ORD0004",
    customer: "Jacquelyn Robel",
    customerRole: "Finance",
    location: "Paris, FR",
    orderDate: "2024-12-15",
    status: "completed",
    total: 3939.5,
    paymentStatus: "paid",
    avatarSeed: "JacquelynRobel",
  },
  {
    id: "#ORD0003",
    customer: "Clint Hoppe",
    customerRole: "Logistics lead",
    location: "Amsterdam, NL",
    orderDate: "2024-12-15",
    status: "completed",
    total: 2959.5,
    paymentStatus: "paid",
    avatarSeed: "ClintHoppe-2",
  },
  {
    id: "#ORD0002",
    customer: "Erin Bins",
    customerRole: "CX",
    location: "Madrid, ES",
    orderDate: "2024-12-15",
    status: "completed",
    total: 120.35,
    paymentStatus: "paid",
    avatarSeed: "ErinBins",
  },
  {
    id: "#ORD0001",
    customer: "Gretchen Quitzon",
    customerRole: "Marketing",
    location: "Roma, IT",
    orderDate: "2024-12-14",
    status: "refunded",
    total: 123.5,
    paymentStatus: "paid",
    avatarSeed: "GretchenQuitzon",
  },
  {
    id: "#ORD0000",
    customer: "Stewart Kubas",
    customerRole: "Operations",
    location: "Seattle, US",
    orderDate: "2024-12-13",
    status: "ongoing",
    total: 630.7,
    paymentStatus: "unpaid",
    avatarSeed: "StewartKubas",
  },
];

const statusStyles: Record<OrderStatus, { label: string; className: string }> = {
  pending: {
    label: "In attesa",
    className: "bg-amber-50 text-amber-700 border-amber-100",
  },
  completed: {
    label: "Completato",
    className: "bg-emerald-50 text-emerald-700 border-emerald-100",
  },
  refunded: {
    label: "Rimborsato",
    className: "bg-rose-50 text-rose-700 border-rose-100",
  },
  ongoing: {
    label: "In corso",
    className: "bg-blue-50 text-blue-700 border-blue-100",
  },
};

const paymentStyles: Record<PaymentStatus, { label: string; className: string }> = {
  paid: {
    label: "Pagato",
    className: "bg-emerald-50 text-emerald-700 border-emerald-100",
  },
  unpaid: {
    label: "Da incassare",
    className: "bg-slate-100 text-slate-700 border-slate-200",
  },
};

const currencyFormatter = new Intl.NumberFormat("it-IT", {
  style: "currency",
  currency: "EUR",
  minimumFractionDigits: 2,
});

const dateFormatter = new Intl.DateTimeFormat("it-IT", {
  day: "2-digit",
  month: "short",
  year: "numeric",
});

const getAvatarUrl = (seed: string) =>
  `https://api.dicebear.com/7.x/initials/svg?seed=${encodeURIComponent(seed)}&backgroundType=gradientLinear`;

const AdminArea = () => {
  const { user } = useAuth();
  const [searchValue, setSearchValue] = useState("");
  const [activeFilter, setActiveFilter] = useState<OrderFilter>("all");
  const [selectedOrders, setSelectedOrders] = useState<string[]>([ORDER_ROWS[2].id]);

  const totals = useMemo(
    () => ({
      pending: ORDER_ROWS.filter((order) => order.status === "pending").length,
      completed: ORDER_ROWS.filter((order) => order.status === "completed").length,
      refunded: ORDER_ROWS.filter((order) => order.status === "refunded").length,
      unpaid: ORDER_ROWS.filter((order) => order.paymentStatus === "unpaid").length,
      revenue: ORDER_ROWS.reduce((sum, order) => sum + order.total, 0),
    }),
    [],
  );

  const filteredOrders = useMemo(() => {
    const term = searchValue.trim().toLowerCase();
    return ORDER_ROWS.filter((order) => {
      const matchesFilter =
        activeFilter === "all"
          ? true
          : activeFilter === "unpaid"
            ? order.paymentStatus === "unpaid"
            : order.status === activeFilter;

      const matchesSearch =
        !term ||
        order.customer.toLowerCase().includes(term) ||
        order.id.toLowerCase().includes(term) ||
        order.location.toLowerCase().includes(term);

      return matchesFilter && matchesSearch;
    });
  }, [activeFilter, searchValue]);

  const visibleIds = filteredOrders.map((order) => order.id);
  const selectedInView = visibleIds.filter((id) => selectedOrders.includes(id));

  const headerChecked: boolean | "indeterminate" =
    selectedInView.length === 0
      ? false
      : selectedInView.length === visibleIds.length
        ? true
        : "indeterminate";

  const handleSelectAll = (checked: boolean | "indeterminate") => {
    if (checked) {
      const merged = new Set([...selectedOrders, ...visibleIds]);
      setSelectedOrders(Array.from(merged));
    } else {
      setSelectedOrders((prev) => prev.filter((id) => !visibleIds.includes(id)));
    }
  };

  const handleRowSelect = (orderId: string, checked: boolean | "indeterminate") => {
    if (checked) {
      setSelectedOrders((prev) => (prev.includes(orderId) ? prev : [...prev, orderId]));
    } else {
      setSelectedOrders((prev) => prev.filter((id) => id !== orderId));
    }
  };

  const filterCounts = {
    all: ORDER_ROWS.length,
    pending: totals.pending,
    completed: totals.completed,
    refunded: totals.refunded,
    unpaid: totals.unpaid,
  };

  const summaryCards = [
    {
      label: "Ordini mese",
      value: 240,
      helper: "+12% vs mese scorso",
      icon: ShoppingBag,
      accent: "bg-indigo-100 text-indigo-700",
    },
    {
      label: "In lavorazione",
      value: totals.pending,
      helper: "Da evadere",
      icon: Clock3,
      accent: "bg-amber-100 text-amber-700",
    },
    {
      label: "Evasioni",
      value: totals.completed,
      helper: "Ordini spediti",
      icon: Send,
      accent: "bg-emerald-100 text-emerald-700",
    },
    {
      label: "Rimborsi",
      value: totals.refunded,
      helper: "Gestione resi",
      icon: Undo2,
      accent: "bg-rose-100 text-rose-700",
    },
  ];

  return (
    <PageShell
      title="Ordini"
      description="Panoramica stile gestionale: stato spedizioni e incassi in un colpo d'occhio."
      headerAside={
        <div className="flex items-center gap-2">
          <Badge
            variant="secondary"
            className="flex items-center gap-1 rounded-full border px-3 py-1 text-[11px] uppercase tracking-widest"
          >
            <BadgeCheck className="h-4 w-4" />
            {user?.full_name || user?.email || "Admin"}
          </Badge>
          <Button size="sm" variant="accent" className="rounded-full px-3.5">
            <Plus className="h-4 w-4" />
            Nuovo ordine
          </Button>
        </div>
      }
      bodyClassName="space-y-4"
    >
      <Card className="border border-border/50 bg-gradient-to-br from-white via-slate-50 to-slate-100 shadow-sm">
        <CardHeader className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-1">
            <p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted-foreground">Workflow giornaliero</p>
            <CardTitle className="text-2xl tracking-tight">Tieni sotto controllo ogni ordine</CardTitle>
            <CardDescription className="max-w-2xl">
              Aggiorna stati, incassi e rimborsi da un'unica vista coerente con la grafica mostrata in esempio.
            </CardDescription>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex -space-x-3">
              {ORDER_ROWS.slice(0, 4).map((order) => (
                <Avatar
                  key={order.id}
                  className="h-10 w-10 border-2 border-white shadow-xs"
                >
                  <AvatarImage src={getAvatarUrl(order.avatarSeed)} alt={order.customer} />
                  <AvatarFallback>{order.customer.slice(0, 2).toUpperCase()}</AvatarFallback>
                </Avatar>
              ))}
              <Button variant="secondary" size="icon" className="h-10 w-10 rounded-full border border-border/70">
                <Plus className="h-4 w-4" />
              </Button>
            </div>
            <Separator orientation="vertical" className="h-10" />
            <div className="flex flex-col text-right">
              <span className="text-xs uppercase tracking-[0.1em] text-muted-foreground">Aggiornato</span>
              <span className="text-sm font-semibold text-foreground">Oggi alle 10:24</span>
            </div>
          </div>
        </CardHeader>
        <CardContent className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 rounded-full border border-border/70 bg-white/60 px-3 py-2 text-sm shadow-xs">
            <Wallet className="h-4 w-4 text-muted-foreground" />
            <span className="font-semibold text-foreground">
              {currencyFormatter.format(totals.revenue)} di ticket atteso
            </span>
          </div>
          <div className="flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700 shadow-xs">
            <Send className="h-4 w-4" />
            <span>48h SLA spedizione media</span>
          </div>
          <div className="flex items-center gap-2 rounded-full border border-indigo-200 bg-indigo-50 px-3 py-2 text-sm text-indigo-700 shadow-xs">
            <Bell className="h-4 w-4" />
            <span>Reminder su rimborsi in sospeso</span>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {summaryCards.map((card) => (
          <Card key={card.label} className="overflow-hidden border-border/60 shadow-xs">
            <CardHeader className="space-y-3 pb-4">
              <div className="flex items-center justify-between">
                <p className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">{card.label}</p>
                <span className={cn("inline-flex h-9 w-9 items-center justify-center rounded-full", card.accent)}>
                  <card.icon className="h-4 w-4" />
                </span>
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-semibold tracking-tight">{card.value}</span>
                <span className="text-xs text-muted-foreground">unità</span>
              </div>
              <p className="text-sm text-muted-foreground">{card.helper}</p>
            </CardHeader>
          </Card>
        ))}
      </div>

      <Card className="border border-border/70 shadow-sm">
        <CardHeader className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.16em] text-muted-foreground">Tutti gli ordini</p>
              <CardTitle className="text-xl leading-tight">Controllo rapido</CardTitle>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" className="rounded-full px-3.5">
                <Download className="h-4 w-4" />
                Esporta
              </Button>
              <Button size="sm" className="rounded-full px-3.5">
                <Plus className="h-4 w-4" />
                Aggiungi ordine
              </Button>
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3">
            <Tabs value={activeFilter} onValueChange={(value) => setActiveFilter(value as OrderFilter)}>
              <TabsList className="h-11 rounded-full bg-muted/60 p-1">
                {[
                  { value: "all", label: "Tutti" },
                  { value: "pending", label: "In lavorazione" },
                  { value: "completed", label: "Conclusi" },
                  { value: "refunded", label: "Rimborsati" },
                  { value: "unpaid", label: "Non pagati" },
                ].map((filter) => (
                  <TabsTrigger
                    key={filter.value}
                    value={filter.value}
                    className="rounded-full px-4 py-2 text-xs data-[state=active]:bg-background data-[state=active]:shadow-sm"
                  >
                    <span>{filter.label}</span>
                    <span className="ml-2 rounded-full bg-white px-2 py-0.5 text-[11px] font-semibold text-muted-foreground shadow-xs">
                      {filterCounts[filter.value as OrderFilter]}
                    </span>
                  </TabsTrigger>
                ))}
              </TabsList>
            </Tabs>

            <div className="flex items-center gap-2">
              <div className="relative w-64">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  value={searchValue}
                  onChange={(event) => setSearchValue(event.target.value)}
                  placeholder="Cerca ordine o cliente"
                  className="h-10 rounded-full pl-9 text-sm"
                />
              </div>
              <Button variant="outline" size="icon" className="h-10 w-10 rounded-full">
                <Bell className="h-4 w-4" />
                <span className="sr-only">Notifiche</span>
              </Button>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
            <BadgeCheck className="h-4 w-4 text-emerald-600" />
            <span>Selezione multipla per azioni di bulk update.</span>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          <div className="overflow-hidden rounded-2xl border border-border/70 bg-card">
            <Table aria-label="Tabella ordini">
              <TableHeader className="bg-muted/70">
                <TableRow className="hover:bg-muted/70">
                  <TableHead className="w-12">
                    <Checkbox checked={headerChecked} onCheckedChange={handleSelectAll} aria-label="Seleziona tutti" />
                  </TableHead>
                  <TableHead>Numero ordine</TableHead>
                  <TableHead>Cliente</TableHead>
                  <TableHead>Data ordine</TableHead>
                  <TableHead>Stato</TableHead>
                  <TableHead>Totale</TableHead>
                  <TableHead>Pagamento</TableHead>
                  <TableHead className="text-right">Azione</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredOrders.map((order) => (
                  <TableRow key={order.id} className="bg-white/80 last:border-0 hover:bg-muted/40">
                    <TableCell>
                      <Checkbox
                        checked={selectedOrders.includes(order.id)}
                        onCheckedChange={(checked) => handleRowSelect(order.id, checked)}
                        aria-label={`Seleziona ${order.id}`}
                      />
                    </TableCell>
                    <TableCell className="font-semibold tracking-tight text-foreground">{order.id}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <Avatar className="h-9 w-9 border border-border/70">
                          <AvatarImage src={getAvatarUrl(order.avatarSeed)} alt={order.customer} />
                          <AvatarFallback>{order.customer.slice(0, 2).toUpperCase()}</AvatarFallback>
                        </Avatar>
                        <div className="flex flex-col">
                          <span className="text-sm font-semibold leading-tight text-foreground">
                            {order.customer}
                          </span>
                          <span className="text-xs text-muted-foreground">
                            {order.customerRole ? `${order.customerRole} • ` : null}
                            {order.location}
                          </span>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {dateFormatter.format(new Date(order.orderDate))}
                    </TableCell>
                    <TableCell>
                      <span
                        className={cn(
                          "inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold",
                          statusStyles[order.status].className,
                        )}
                      >
                        {statusStyles[order.status].label}
                      </span>
                    </TableCell>
                    <TableCell className="text-sm font-semibold">{currencyFormatter.format(order.total)}</TableCell>
                    <TableCell>
                      <span
                        className={cn(
                          "inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold",
                          paymentStyles[order.paymentStatus].className,
                        )}
                      >
                        {paymentStyles[order.paymentStatus].label}
                      </span>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <Button variant="ghost" size="icon" className="h-8 w-8 rounded-lg border border-border/60">
                          <Copy className="h-4 w-4" />
                          <span className="sr-only">Duplica ordine</span>
                        </Button>
                        <Button variant="ghost" size="icon" className="h-8 w-8 rounded-lg border border-border/60">
                          <Pencil className="h-4 w-4" />
                          <span className="sr-only">Modifica ordine</span>
                        </Button>
                        <Button variant="ghost" size="icon" className="h-8 w-8 rounded-lg border border-border/60">
                          <MoreHorizontal className="h-4 w-4" />
                          <span className="sr-only">Altre azioni</span>
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3 text-sm">
            <div className="flex items-center gap-2">
              <span className="text-muted-foreground">
                {selectedOrders.length > 0
                  ? `${selectedOrders.length} ordine${selectedOrders.length > 1 ? "i" : ""} selezionat${selectedOrders.length > 1 ? "i" : "o"}`
                  : "Nessuna selezione"}
              </span>
              <Separator orientation="vertical" className="h-5" />
              <div className="flex items-center gap-1">
                <Button variant="ghost" size="sm" className="h-8 rounded-full px-3">
                  <Copy className="h-4 w-4" />
                  Duplica
                </Button>
                <Button variant="ghost" size="sm" className="h-8 rounded-full px-3">
                  <Printer className="h-4 w-4" />
                  Stampa
                </Button>
                <Button variant="ghost" size="sm" className="h-8 rounded-full px-3 text-destructive">
                  Elimina
                </Button>
              </div>
            </div>

            <Pagination className="w-auto">
              <PaginationContent className="gap-1">
                <PaginationItem>
                  <PaginationPrevious href="#" />
                </PaginationItem>
                <PaginationItem>
                  <PaginationLink href="#" isActive>
                    1
                  </PaginationLink>
                </PaginationItem>
                <PaginationItem>
                  <PaginationLink href="#">2</PaginationLink>
                </PaginationItem>
                <PaginationItem>
                  <PaginationNext href="#" />
                </PaginationItem>
              </PaginationContent>
            </Pagination>
          </div>
        </CardContent>
      </Card>
    </PageShell>
  );
};

export default AdminArea;
