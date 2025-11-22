export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  // Allows to automatically instantiate createClient with right options
  // instead of createClient<Database, { PostgrestVersion: 'XX' }>(URL, KEY)
  __InternalSupabase: {
    PostgrestVersion: "13.0.5"
  }
  public: {
    Tables: {
      commesse: {
        Row: {
          business_unit: string | null
          cliente: string | null
          codice: string
          created_at: string | null
          descrizione: string | null
          id: string
          importo_totale: number | null
          nome: string
          revisione: string | null
          stato: string | null
          updated_at: string | null
          user_id: string | null
        }
        Insert: {
          business_unit?: string | null
          cliente?: string | null
          codice: string
          created_at?: string | null
          descrizione?: string | null
          id?: string
          importo_totale?: number | null
          nome: string
          revisione?: string | null
          stato?: string | null
          updated_at?: string | null
          user_id?: string | null
        }
        Update: {
          business_unit?: string | null
          cliente?: string | null
          codice?: string
          created_at?: string | null
          descrizione?: string | null
          id?: string
          importo_totale?: number | null
          nome?: string
          revisione?: string | null
          stato?: string | null
          updated_at?: string | null
          user_id?: string | null
        }
        Relationships: []
      }
      computi: {
        Row: {
          commessa_id: string | null
          created_at: string | null
          descrizione: string | null
          file_name: string | null
          id: string
          importo_totale: number | null
          nome: string
          tipo: string
          updated_at: string | null
          user_id: string | null
        }
        Insert: {
          commessa_id?: string | null
          created_at?: string | null
          descrizione?: string | null
          file_name?: string | null
          id?: string
          importo_totale?: number | null
          nome: string
          tipo: string
          updated_at?: string | null
          user_id?: string | null
        }
        Update: {
          commessa_id?: string | null
          created_at?: string | null
          descrizione?: string | null
          file_name?: string | null
          id?: string
          importo_totale?: number | null
          nome?: string
          tipo?: string
          updated_at?: string | null
          user_id?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "computi_commessa_id_fkey"
            columns: ["commessa_id"]
            isOneToOne: false
            referencedRelation: "commesse"
            referencedColumns: ["id"]
          },
        ]
      }
      confronto_voci: {
        Row: {
          created_at: string | null
          criticita: string | null
          delta_importo: number | null
          delta_prezzo_unitario: number | null
          id: string
          note: string | null
          percentuale_delta: number | null
          ritorno_id: string | null
          user_id: string | null
          voce_progetto_id: string | null
          voce_ritorno_id: string | null
        }
        Insert: {
          created_at?: string | null
          criticita?: string | null
          delta_importo?: number | null
          delta_prezzo_unitario?: number | null
          id?: string
          note?: string | null
          percentuale_delta?: number | null
          ritorno_id?: string | null
          user_id?: string | null
          voce_progetto_id?: string | null
          voce_ritorno_id?: string | null
        }
        Update: {
          created_at?: string | null
          criticita?: string | null
          delta_importo?: number | null
          delta_prezzo_unitario?: number | null
          id?: string
          note?: string | null
          percentuale_delta?: number | null
          ritorno_id?: string | null
          user_id?: string | null
          voce_progetto_id?: string | null
          voce_ritorno_id?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "confronto_voci_ritorno_id_fkey"
            columns: ["ritorno_id"]
            isOneToOne: false
            referencedRelation: "ritorni_gara"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "confronto_voci_voce_progetto_id_fkey"
            columns: ["voce_progetto_id"]
            isOneToOne: false
            referencedRelation: "voci_wbs"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "confronto_voci_voce_ritorno_id_fkey"
            columns: ["voce_ritorno_id"]
            isOneToOne: false
            referencedRelation: "voci_wbs"
            referencedColumns: ["id"]
          },
        ]
      }
      ritorni_gara: {
        Row: {
          commessa_id: string | null
          computo_progetto_id: string | null
          created_at: string | null
          delta_vs_progetto: number | null
          file_name: string | null
          id: string
          importo_totale: number | null
          impresa: string
          note: string | null
          percentuale_delta: number | null
          stato: string | null
          updated_at: string | null
          user_id: string | null
        }
        Insert: {
          commessa_id?: string | null
          computo_progetto_id?: string | null
          created_at?: string | null
          delta_vs_progetto?: number | null
          file_name?: string | null
          id?: string
          importo_totale?: number | null
          impresa: string
          note?: string | null
          percentuale_delta?: number | null
          stato?: string | null
          updated_at?: string | null
          user_id?: string | null
        }
        Update: {
          commessa_id?: string | null
          computo_progetto_id?: string | null
          created_at?: string | null
          delta_vs_progetto?: number | null
          file_name?: string | null
          id?: string
          importo_totale?: number | null
          impresa?: string
          note?: string | null
          percentuale_delta?: number | null
          stato?: string | null
          updated_at?: string | null
          user_id?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "ritorni_gara_commessa_id_fkey"
            columns: ["commessa_id"]
            isOneToOne: false
            referencedRelation: "commesse"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "ritorni_gara_computo_progetto_id_fkey"
            columns: ["computo_progetto_id"]
            isOneToOne: false
            referencedRelation: "computi"
            referencedColumns: ["id"]
          },
        ]
      }
      settings: {
        Row: {
          created_at: string | null
          delta_massimo_critico: number | null
          delta_minimo_critico: number | null
          id: string
          percentuale_cme_alto: number | null
          percentuale_cme_basso: number | null
          updated_at: string | null
          user_id: string | null
        }
        Insert: {
          created_at?: string | null
          delta_massimo_critico?: number | null
          delta_minimo_critico?: number | null
          id?: string
          percentuale_cme_alto?: number | null
          percentuale_cme_basso?: number | null
          updated_at?: string | null
          user_id?: string | null
        }
        Update: {
          created_at?: string | null
          delta_massimo_critico?: number | null
          delta_minimo_critico?: number | null
          id?: string
          percentuale_cme_alto?: number | null
          percentuale_cme_basso?: number | null
          updated_at?: string | null
          user_id?: string | null
        }
        Relationships: []
      }
      voci_wbs: {
        Row: {
          codice: string
          computo_id: string | null
          created_at: string | null
          descrizione: string
          id: string
          importo: number | null
          livello: number
          ordine: number | null
          parent_id: string | null
          prezzo_unitario: number | null
          quantita: number | null
          tipo_wbs: string
          um: string | null
          updated_at: string | null
          user_id: string | null
        }
        Insert: {
          codice: string
          computo_id?: string | null
          created_at?: string | null
          descrizione: string
          id?: string
          importo?: number | null
          livello?: number
          ordine?: number | null
          parent_id?: string | null
          prezzo_unitario?: number | null
          quantita?: number | null
          tipo_wbs: string
          um?: string | null
          updated_at?: string | null
          user_id?: string | null
        }
        Update: {
          codice?: string
          computo_id?: string | null
          created_at?: string | null
          descrizione?: string
          id?: string
          importo?: number | null
          livello?: number
          ordine?: number | null
          parent_id?: string | null
          prezzo_unitario?: number | null
          quantita?: number | null
          tipo_wbs?: string
          um?: string | null
          updated_at?: string | null
          user_id?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "voci_wbs_computo_id_fkey"
            columns: ["computo_id"]
            isOneToOne: false
            referencedRelation: "computi"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "voci_wbs_parent_id_fkey"
            columns: ["parent_id"]
            isOneToOne: false
            referencedRelation: "voci_wbs"
            referencedColumns: ["id"]
          },
        ]
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      [_ in never]: never
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type DatabaseWithoutInternals = Omit<Database, "__InternalSupabase">

type DefaultSchema = DatabaseWithoutInternals[Extract<keyof Database, "public">]

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never = never,
> = DefaultSchemaEnumNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never = never,
> = PublicCompositeTypeNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never

export const Constants = {
  public: {
    Enums: {},
  },
} as const
