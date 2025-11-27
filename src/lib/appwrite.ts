import { Account, Client, Databases } from "appwrite";

export const client = new Client()
  .setProject("69287e78003ca6498d45")
  .setEndpoint("https://fra.cloud.appwrite.io/v1");

export const account = new Account(client);
export const databases = new Databases(client);
