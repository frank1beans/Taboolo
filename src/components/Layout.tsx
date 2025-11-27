import { SidebarProvider, SidebarInset } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/layout/AppSidebar";
import { TopBar } from "@/components/layout/TopBar";

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <SidebarProvider defaultOpen={true}>
      <div className="flex min-h-screen w-full bg-[hsl(220,18%,92%)]">
        <AppSidebar />
        <SidebarInset className="flex flex-1 flex-col h-screen overflow-hidden">
          <TopBar />
          <main className="flex-1 overflow-y-auto">
            <div className="app-surface">
              <div className="page-content">{children}</div>
            </div>
          </main>
        </SidebarInset>
      </div>
    </SidebarProvider>
  );
}
