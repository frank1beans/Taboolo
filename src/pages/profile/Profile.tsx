import { FormEvent, useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/features/auth/AuthContext";
import { api } from "@/lib/api-client";
import type { ApiUserProfile } from "@/types/api";
import { Badge } from "@/components/ui/badge";
import { Loader2 } from "lucide-react";

const Profile = () => {
  const { user, profile, refreshProfile } = useAuth();
  const [form, setForm] = useState<ApiUserProfile | null>(profile);
  const [status, setStatus] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    setForm(profile);
  }, [profile]);

  if (!user) return null;

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!form) return;
    setStatus(null);
    setIsSaving(true);
    try {
      await api.updateProfile({
        company: form.company,
        language: form.language,
        settings: form.settings,
      });
      await refreshProfile();
      setStatus("Profilo aggiornato");
    } catch (error) {
      setStatus("Errore durante l'aggiornamento del profilo");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="page-container">
      <div className="page-content">
        {/* Header pagina */}
        <div className="page-header">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h1 className="text-display mb-1">Profilo utente</h1>
              <p className="text-body-sm text-muted-foreground">
                Gestisci i tuoi dati di contatto e le preferenze dell&apos;account.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
              <Badge variant="outline">ID utente: {user.id}</Badge>
              <Badge variant="secondary">{user.role}</Badge>
            </div>
          </div>
        </div>

        {/* Contenuto */}
        <div className="content-grid content-grid-2 section-spacing">
          {/* Card: dati account */}
          <Card className="card-padding-lg">
            <CardHeader className="px-0 pt-0">
              <CardTitle className="text-heading-3">Dati account</CardTitle>
              <CardDescription className="text-body-sm">
                Informazioni di base sull&apos;account (non modificabili da qui).
              </CardDescription>
            </CardHeader>
            <CardContent className="px-0 pb-0 space-y-4">
              <div className="space-y-1">
                <p className="text-xs font-medium text-muted-foreground">Email</p>
                <p className="font-medium break-all">{user.email}</p>
              </div>
              <div className="space-y-1">
                <p className="text-xs font-medium text-muted-foreground">Ruolo</p>
                <p className="inline-flex items-center gap-2 font-medium">
                  {user.role}
                </p>
              </div>
              {user.full_name && (
                <div className="space-y-1">
                  <p className="text-xs font-medium text-muted-foreground">Nome completo</p>
                  <p className="font-medium">{user.full_name}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Card: preferenze profilo */}
          <Card className="card-padding-lg">
            <CardHeader className="px-0 pt-0">
              <CardTitle className="text-heading-3">Profilo</CardTitle>
              <CardDescription className="text-body-sm">
                Aggiorna le preferenze personali dell&apos;account.
              </CardDescription>
            </CardHeader>
            <CardContent className="px-0 pb-0">
              <form className="space-y-5" onSubmit={handleSubmit}>
                <div className="space-y-2">
                  <Label htmlFor="company">Azienda</Label>
                  <Input
                    id="company"
                    value={form?.company ?? ""}
                    onChange={(e) =>
                      setForm((prev) => (prev ? { ...prev, company: e.target.value } : prev))
                    }
                    placeholder="Nome azienda"
                  />
                  <p className="text-xs text-muted-foreground">
                    Puoi usare il nome legale o una denominazione abbreviata.
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="language">Lingua</Label>
                  <Input
                    id="language"
                    value={form?.language ?? ""}
                    onChange={(e) =>
                      setForm((prev) => (prev ? { ...prev, language: e.target.value } : prev))
                    }
                    placeholder="es. it-IT"
                  />
                  <p className="text-xs text-muted-foreground">
                    Codice lingua in formato locale (es. <span className="font-mono">it-IT</span>,{" "}
                    <span className="font-mono">en-GB</span>).
                  </p>
                </div>

                <div className="flex items-center gap-3 pt-2">
                  <Button type="submit" disabled={!form || isSaving}>
                    {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    Salva modifiche
                  </Button>
                  {status && (
                    <p
                      className={`text-sm ${
                        status.startsWith("Errore")
                          ? "text-destructive"
                          : "text-emerald-600 dark:text-emerald-400"
                      }`}
                    >
                      {status}
                    </p>
                  )}
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Profile;
