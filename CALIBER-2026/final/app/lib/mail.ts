import "server-only";
import { t } from "./i18n";
import nodemailer from "nodemailer";
import type { Person } from "./people";

/** Real delivery through Gmail SMTP with an App Password. Both values come from the server environment only. */
const USER = () => process.env.GMAIL_USER?.trim();
const PASS = () => process.env.GMAIL_APP_PASSWORD?.replace(/\s+/g, "");

export const mailConfigured = () => !!(USER() && PASS());

const HOUR_CAP = 40;
let windowStart = 0;
let sent = 0;

export async function sendMail(m: { from: Person; toName: string; toEmail: string; subject: string; body: string }) {
  const now = Date.now();
  if (now - windowStart > 3_600_000) {
    windowStart = now;
    sent = 0;
  }
  if (sent >= HOUR_CAP) throw new Error(t("The demo mailbox has reached its hourly limit.", "Kotak surat demo sudah mencapai batas per jam."));
  const transport = nodemailer.createTransport({ service: "gmail", auth: { user: USER(), pass: PASS() } });
  const info = await transport.sendMail({
    from: { name: `${m.from.name} via Sparekit`, address: USER()! },
    replyTo: { name: m.from.name, address: m.from.email },
    to: { name: m.toName, address: m.toEmail },
    subject: m.subject,
    text: m.body,
  });
  sent++;
  return info.messageId;
}
