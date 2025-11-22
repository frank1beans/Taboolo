-- Aggiunge le colonne business_unit e revisione alla tabella commessa
-- Esegui questo script sul database SQLite per aggiornare lo schema

ALTER TABLE commessa ADD COLUMN business_unit TEXT;
ALTER TABLE commessa ADD COLUMN revisione TEXT;
