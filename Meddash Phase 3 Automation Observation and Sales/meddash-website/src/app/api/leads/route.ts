import { NextRequest, NextResponse } from "next/server";

export const runtime = "edge";

type LeadPayload = {
  name?: string;
  email?: string;
  company?: string;
  phone?: string;
  subscribeUpdates?: boolean;
  briefTypes?: string[];
  source?: string;
};

function esc(s: string) {
  return s.replace(/[&<>]/g, (m) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[m] || m));
}

export async function POST(req: NextRequest) {
  const body = (await req.json()) as LeadPayload;

  const name = (body.name || "").trim();
  const email = (body.email || "").trim();
  const company = (body.company || "").trim();
  const phone = (body.phone || "").trim();
  const briefTypes = Array.isArray(body.briefTypes) ? body.briefTypes.filter(Boolean) : [];
  const subscribeUpdates = Boolean(body.subscribeUpdates);
  const source = body.source || "meddash_website_request_brief";

  if (!name || !email || !company || briefTypes.length === 0) {
    return NextResponse.json({ error: "name, email, company, and at least one brief type are required" }, { status: 400 });
  }

  const telegramToken = process.env.TELEGRAM_BOT_TOKEN;
  const telegramChatId = process.env.TELEGRAM_CHAT_ID;
  const resendApiKey = process.env.RESEND_API_KEY;
  const resendFrom = process.env.RESEND_FROM || "Meddash <contact@meddash.ai>";
  const resendInternalTo = process.env.RESEND_INTERNAL_TO || "contact@meddash.ai";
  const contactEmail = process.env.CONTACT_EMAIL || "contact@meddash.ai";

  let telegramOk = false;
  let emailLeadOk = false;
  let emailInternalOk = false;

  if (telegramToken && telegramChatId) {
    const text = [
      "📥 New Meddash Request Brief",
      `Name: ${name}`,
      `Email: ${email}`,
      `Company: ${company}`,
      `Phone: ${phone || "N/A"}`,
      `Brief types: ${briefTypes.join(", ")}`,
      `Subscribe weekly updates: ${subscribeUpdates ? "Yes" : "No"}`,
      `Source: ${source}`,
    ].join("\n");

    const tgRes = await fetch(`https://api.telegram.org/bot${telegramToken}/sendMessage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ chat_id: telegramChatId, text }),
    });

    telegramOk = tgRes.ok;
  }

  if (resendApiKey) {
    const leadEmailRes = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${resendApiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        from: resendFrom,
        to: [email],
        reply_to: contactEmail,
        subject: "Meddash request received",
        html: `
          <p>Hi ${esc(name)},</p>
          <p>Thanks for your request. We received your submission and will follow up shortly.</p>
          <p><strong>Requested:</strong> ${esc(briefTypes.join(", "))}</p>
          <p>— Meddash Team</p>
        `,
      }),
    });
    emailLeadOk = leadEmailRes.ok;

    const internalRes = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${resendApiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        from: resendFrom,
        to: [resendInternalTo],
        reply_to: email,
        subject: `New Meddash request: ${company}`,
        html: `
          <p><strong>Name:</strong> ${esc(name)}</p>
          <p><strong>Email:</strong> ${esc(email)}</p>
          <p><strong>Company:</strong> ${esc(company)}</p>
          <p><strong>Phone:</strong> ${esc(phone || "N/A")}</p>
          <p><strong>Brief types:</strong> ${esc(briefTypes.join(", "))}</p>
          <p><strong>Subscribe updates:</strong> ${subscribeUpdates ? "Yes" : "No"}</p>
          <p><strong>Source:</strong> ${esc(source)}</p>
        `,
      }),
    });
    emailInternalOk = internalRes.ok;
  }

  return NextResponse.json({
    ok: true,
    telegram_ok: telegramOk,
    email_lead_ok: emailLeadOk,
    email_internal_ok: emailInternalOk,
  });
}
