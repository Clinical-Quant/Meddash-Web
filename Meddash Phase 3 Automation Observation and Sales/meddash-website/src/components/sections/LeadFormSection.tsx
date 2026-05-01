"use client";

import { FormEvent, useState } from "react";

type BriefType = "Therapeutic Area Intelligence Brief" | "Intelligent KOL Brief";

export default function LeadFormSection() {
  const [status, setStatus] = useState<string>("");
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    const data = new FormData(form);

    const briefTypes = data.getAll("briefTypes").map(String) as BriefType[];

    const payload = {
      name: String(data.get("name") || "").trim(),
      email: String(data.get("email") || "").trim(),
      company: String(data.get("company") || "").trim(),
      phone: String(data.get("phone") || "").trim(),
      subscribeUpdates: data.get("subscribeUpdates") === "on",
      briefTypes,
      source: "meddash_website_request_brief"
    };

    if (!payload.name || !payload.email || !payload.company || briefTypes.length === 0) {
      setStatus("Please complete name, work email, company, and select at least one brief type.");
      return;
    }

    setSubmitting(true);
    setStatus("");

    try {
      const res = await fetch("/api/leads", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        if (typeof window !== "undefined" && typeof (window as Window & { gtag?: (...args: unknown[]) => void }).gtag === "function") {
          (window as Window & { gtag?: (...args: unknown[]) => void }).gtag?.("event", "request_brief_submit", {
            selected_briefs: briefTypes.join(", "),
          });
        }
        setStatus("Thanks — your request brief form was submitted. We will contact you shortly.");
        form.reset();
      } else {
        setStatus("Could not submit right now. Please try again or email contact@meddash.ai.");
      }
    } catch {
      setStatus("Could not submit right now. Please try again or email contact@meddash.ai.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section id="lead" className="px-6 md:px-10 py-16">
      <h2 className="text-3xl font-semibold text-white mb-3">Request Brief</h2>
      <p className="text-slate-300 mb-6">Tell us your focus area and we will send a decision-ready brief path for your team.</p>

      <form onSubmit={onSubmit} className="max-w-5xl grid md:grid-cols-2 gap-3">
        <input required name="name" placeholder="Full name" className="rounded-lg bg-meddash-surface border border-white/10 px-3 py-3 text-white" />
        <input required name="email" type="email" placeholder="Work email" className="rounded-lg bg-meddash-surface border border-white/10 px-3 py-3 text-white" />
        <input required name="company" placeholder="Company" className="rounded-lg bg-meddash-surface border border-white/10 px-3 py-3 text-white" />
        <input name="phone" placeholder="Phone (optional)" className="rounded-lg bg-meddash-surface border border-white/10 px-3 py-3 text-white" />

        <div className="md:col-span-2 rounded-lg border border-white/10 bg-meddash-surface p-4">
          <p className="text-sm text-slate-200 mb-2">Brief type (select one or both)</p>
          <label className="flex items-center gap-2 text-slate-300 mb-2">
            <input type="checkbox" name="briefTypes" value="Therapeutic Area Intelligence Brief" className="accent-meddash-cyan" />
            Therapeutic Area Intelligence Brief
          </label>
          <label className="flex items-center gap-2 text-slate-300">
            <input type="checkbox" name="briefTypes" value="Intelligent KOL Brief" className="accent-meddash-cyan" />
            Intelligent KOL Brief
          </label>
        </div>

        <label className="md:col-span-2 flex items-center gap-2 text-slate-300">
          <input type="checkbox" name="subscribeUpdates" defaultChecked className="accent-meddash-emerald" />
          Subscribe to Meddash weekly newsletter on therapeutic area updates.
        </label>

        <div className="md:col-span-2">
          <button disabled={submitting} className="rounded-lg bg-meddash-cyan text-black font-semibold px-5 py-3 disabled:opacity-60">
            {submitting ? "Submitting..." : "Submit Request"}
          </button>
        </div>
      </form>

      {status ? <p className="text-sm text-meddash-emerald mt-3">{status}</p> : null}
    </section>
  );
}
