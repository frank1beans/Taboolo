import { FormEvent, useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/features/auth/AuthContext";
import { api } from "@/lib/api-client";
import { ApiUserProfile } from "@/types/api";

const Profile = () => {
  const { user, profile, refreshProfile } = useAuth();
  const [form, setForm] = useState<ApiUserProfile | null>(profile);
  const [status, setStatus] = useState<string | null>(null);

  useEffect(() => {
    setForm(profile);
  }, [profile]);

  if (!user) return null;

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!form) return;
    setStatus(null);
    await api.updateProfile({
      company: form.company,
      language: form.language,
      settings: form.settings,
    });
    await refreshProfile();
    setStatus("Profilo aggiornato");
  };

  return (
    <div className="page-container">
      <div className="page-content">
        <div className="page-header">
          <h1 className="text-display mb-2">Profilo utente</h1>
          <p className="text-body-sm text-muted-foreground">Gestisci i tuoi dati di contatto e preferenze.</p>
        </div>
        <div className="content-grid content-grid-2 section-spacing">
          <Card className="card-padding-lg">
            <CardHeader className="px-0 pt-0">
              <CardTitle className="text-heading-3">Dati account</CardTitle>
              <CardDescription className="text-body-sm">Informazioni di base sull'account.</CardDescription>
            </CardHeader>
            <CardContent className="px-0 pb-0 stack-spacing-xs">
            <div>
              <p className="text-muted-foreground">Email</p>
              <p className="font-medium">{user.email}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Ruolo</p>
              <p className="font-medium">{user.role}</p>
            </div>
          </CardContent>
        </Card>

          <Card className="card-padding-lg">
            <CardHeader className="px-0 pt-0">
              <CardTitle className="text-heading-3">Profilo</CardTitle>
              <CardDescription className="text-body-sm">Aggiorna le preferenze personali.</CardDescription>
            </CardHeader>
            <CardContent className="px-0 pb-0">
            <form className="space-y-4" onSubmit={handleSubmit}>
              <div className="space-y-2">
                <label className="text-sm font-medium" htmlFor="company">
                  Azienda
                </label>
                <Input
                  id="company"
                  value={form?.company ?? ""}
                  onChange={(e) => setForm((prev) => (prev ? { ...prev, company: e.target.value } : prev))}
                  placeholder="Nome azienda"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium" htmlFor="language">
                  Lingua
                </label>
                <Input
                  id="language"
                  value={form?.language ?? ""}
                  onChange={(e) => setForm((prev) => (prev ? { ...prev, language: e.target.value } : prev))}
                  placeholder="it-IT"
                />
              </div>
              <Button type="submit">Salva</Button>
              {status ? <p className="text-sm text-green-600">{status}</p> : null}
            </form>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Profile;
