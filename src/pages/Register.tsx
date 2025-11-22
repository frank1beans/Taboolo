import { FormEvent, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/features/auth/AuthContext";
import { CheckCircle2, Circle, Info, ShieldCheck, UserCheck } from "lucide-react";

const Register = () => {
  const { registerUser } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const passwordChecks = useMemo(
    () => [
      { label: "Almeno 16 caratteri", valid: password.length >= 16 },
      { label: "Almeno una lettera (a-z)", valid: /[A-Za-z]/.test(password) },
      { label: "Almeno una lettera maiuscola", valid: /[A-Z]/.test(password) },
      { label: "Almeno un numero", valid: /\d/.test(password) },
      { label: "Almeno un carattere speciale (!@#$&...)", valid: /[^A-Za-z0-9]/.test(password) },
    ],
    [password],
  );
  const isPasswordValid = passwordChecks.every((rule) => rule.valid);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await registerUser({ email, password, full_name: fullName });
      navigate("/login", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registrazione fallita");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-start justify-center bg-background px-4 py-12">
      <div className="grid w-full max-w-5xl gap-6 lg:grid-cols-[1.3fr,0.9fr]">
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle>Richiedi l&apos;abilitazione a Taboolo</CardTitle>
            <CardDescription>
              Gli account vengono creati solo per clienti e partner autorizzati. Completa il form e
              rispetta i requisiti di sicurezza indicati di seguito.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-5" onSubmit={handleSubmit}>
              <div className="space-y-2">
                <label className="text-sm font-medium" htmlFor="fullName">
                  Nome completo
                </label>
                <Input
                  id="fullName"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Nome Cognome"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium" htmlFor="email">
                  Email aziendale
                </label>
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="nome.cognome@taboolo.com"
                  required
                />
              </div>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium" htmlFor="password">
                    Password
                  </label>
                  <span className="text-xs text-muted-foreground">Max 72 caratteri</span>
                </div>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  minLength={16}
                  maxLength={72}
                  required
                />
                <ul className="space-y-1 text-sm">
                  {passwordChecks.map((rule) => (
                    <li
                      key={rule.label}
                      className="flex items-center gap-2 text-muted-foreground"
                    >
                      {rule.valid ? (
                        <CheckCircle2 className="h-4 w-4 text-emerald-500" aria-hidden />
                      ) : (
                        <Circle className="h-4 w-4" aria-hidden />
                      )}
                      <span className={rule.valid ? "text-foreground" : ""}>{rule.label}</span>
                    </li>
                  ))}
                </ul>
              </div>
              {error ? <p className="text-sm text-destructive">{error}</p> : null}
              <Button type="submit" className="w-full" disabled={loading || !isPasswordValid}>
                {loading ? "Verifica in corso..." : "Invia richiesta"}
              </Button>
              {!isPasswordValid ? (
                <p className="text-sm text-muted-foreground">
                  Completa tutti i requisiti per abilitare il pulsante di invio.
                </p>
              ) : null}
              <p className="text-sm text-muted-foreground">
                Hai gia un account? <Link className="text-primary" to="/login">Accedi</Link>
              </p>
            </form>
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Alert>
            <ShieldCheck className="h-5 w-5" aria-hidden />
            <AlertTitle>Accesso riservato</AlertTitle>
            <AlertDescription>
              Registriamo solo indirizzi approvati e monitoriamo ogni nuova abilitazione. Account non
              autorizzati vengono rimossi automaticamente.
            </AlertDescription>
          </Alert>

          <Card>
            <CardHeader className="space-y-1">
              <CardTitle className="flex items-center gap-2 text-base">
                <UserCheck className="h-4 w-4 text-primary" aria-hidden />
                Chi puo registrarsi
              </CardTitle>
              <CardDescription>
                Effettua la richiesta solo se fai parte del team Taboolo o se hai ricevuto un invito
                formale.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3 text-sm text-muted-foreground">
                <li className="flex gap-2">
                  <Info className="mt-0.5 h-4 w-4 text-primary" aria-hidden />
                  <span>
                    Utilizza un indirizzo aziendale verificato (preferibilmente @taboolo.com).
                  </span>
                </li>
                <li className="flex gap-2">
                  <Info className="mt-0.5 h-4 w-4 text-primary" aria-hidden />
                  <span>
                    Ogni richiesta viene controllata manualmente: riceverai una mail di conferma
                    quando l&apos;account sara abilitato.
                  </span>
                </li>
                <li className="flex gap-2">
                  <Info className="mt-0.5 h-4 w-4 text-primary" aria-hidden />
                  <span>
                    Per ulteriori abilitazioni scrivi a{" "}
                    <a className="text-primary underline" href="mailto:security@taboolo.com">
                      security@taboolo.com
                    </a>
                    .
                  </span>
                </li>
              </ul>
            </CardContent>
          </Card>

          <Card className="border-primary/40">
            <CardHeader>
              <CardTitle>Accesso demo immediato</CardTitle>
              <CardDescription>
                Per i test interni e le demo e gia presente un amministratore di default.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-sm text-muted-foreground">
                Accedi direttamente dalla pagina di login con queste credenziali:
              </p>
              <div className="rounded-lg bg-muted p-3 font-mono text-sm">
                <p>
                  <span className="font-semibold">Email:</span> admin@taboolo.com
                </p>
                <p>
                  <span className="font-semibold">Password:</span> !1235813AbCdEf$
                </p>
              </div>
              <p className="text-xs text-muted-foreground">
                Ricorda di cambiare la password appena saranno disponibili i flussi di gestione
                utenti.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Register;
