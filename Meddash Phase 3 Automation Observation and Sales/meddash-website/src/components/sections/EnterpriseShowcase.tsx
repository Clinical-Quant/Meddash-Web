"use client";

import { FormEvent, useState } from "react";

export default function EnterpriseShowcase() {
  const [open, setOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [status, setStatus] = useState("");

  async function onSampleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    const data = new FormData(form);

    const payload = {
      name: String(data.get("name") || "").trim(),
      email: String(data.get("email") || "").trim(),
      company: String(data.get("company") || "").trim(),
      phone: String(data.get("phone") || "").trim(),
      subscribeUpdates: data.get("subscribeUpdates") === "on",
      briefTypes: ["Intelligent KOL Brief"],
      source: "meddash_website_request_sample",
    };

    if (!payload.name || !payload.email || !payload.company) {
      setStatus("Please complete name, work email, and company.");
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
        setStatus("Sample request submitted. We will contact you shortly.");
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
    <section id="enterprise" className="px-6 md:px-10 py-16">
      <h2 className="text-3xl font-semibold text-white mb-4">Enterprise Services</h2>
      <p className="text-slate-300 max-w-3xl mb-8">Built for biotech teams needing signal over noise across KOL influence, therapeutic landscapes, and catalyst timing.</p>
      <div className="grid md:grid-cols-3 gap-4">
        <div className="rounded-2xl border border-meddash-cyan/40 bg-meddash-surface p-6 hover:border-meddash-cyan/70">
          <h3 className="text-meddash-cyan font-semibold">Intelligent KOL Briefs</h3>
          <p className="text-slate-300 mt-2">Decision-ready expert influence maps with therapeutic context and action framing.</p>
          <a href="#lead" className="mt-5 inline-block rounded-xl bg-meddash-cyan text-black px-4 py-2 text-sm font-semibold hover:opacity-90">Request Brief</a>
        </div>

        <div className="rounded-2xl border border-meddash-emerald/40 bg-meddash-surface p-6 hover:border-meddash-emerald/70">
          <h3 className="text-meddash-emerald font-semibold">Therapeutic Area Intelligence Briefs</h3>
          <p className="text-slate-300 mt-2">Broader therapeutic area scoring in one decision-ready brief.</p>
          <a href="#lead" className="mt-5 inline-block rounded-xl border border-meddash-emerald/70 text-meddash-emerald px-4 py-2 text-sm font-semibold hover:bg-meddash-emerald/10">Request Brief</a>
        </div>

        <div className="rounded-2xl border border-white/10 bg-meddash-surface p-6 hover:border-white/30">
          <h3 className="text-white font-semibold">Biotech Catalyst Interpretation</h3>
          <p className="text-slate-300 mt-2">Coming soon.</p>
        </div>
      </div>

      <div className="mt-6">
        <button
          onClick={() => {
            setOpen(true);
            setStatus("");
          }}
          className="rounded-lg border border-white/20 text-slate-200 px-4 py-2 text-xs font-semibold hover:bg-white/5"
        >
          Request Sample
        </button>
      </div>

      {open ? (
        <div className="fixed inset-0 z-50 bg-black/70 p-4 flex items-center justify-center">
          <div className="w-full max-w-xl rounded-2xl border border-white/15 bg-[#0b1220] p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-white text-lg font-semibold">Request Sample</h3>
              <button onClick={() => setOpen(false)} className="text-slate-300 text-sm hover:text-white">Close</button>
            </div>

            <form onSubmit={onSampleSubmit} className="grid gap-3">
              <input required name="name" placeholder="Full name" className="rounded-lg bg-meddash-surface border border-white/10 px-3 py-3 text-white" />
              <input required name="email" type="email" placeholder="Work email" className="rounded-lg bg-meddash-surface border border-white/10 px-3 py-3 text-white" />
              <input required name="company" placeholder="Company" className="rounded-lg bg-meddash-surface border border-white/10 px-3 py-3 text-white" />
              <input name="phone" placeholder="Phone (optional)" className="rounded-lg bg-meddash-surface border border-white/10 px-3 py-3 text-white" />

              <div className="rounded-lg border border-white/10 bg-meddash-surface p-4 text-slate-300 text-sm">
                Brief type: Intelligent KOL Brief
              </div>

              <label className="flex items-center gap-2 text-slate-300">
                <input type="checkbox" name="subscribeUpdates" defaultChecked className="accent-meddash-emerald" />
                Subscribe to Meddash weekly newsletter on therapeutic area updates.
              </label>

              <div>
                <button disabled={submitting} className="rounded-lg bg-meddash-cyan text-black font-semibold px-5 py-3 disabled:opacity-60">
                  {submitting ? "Submitting..." : "Submit Sample Request"}
                </button>
              </div>
            </form>

            {status ? <p className="text-sm text-meddash-emerald mt-3">{status}</p> : null}
          </div>
        </div>
      ) : null}
    </section>
  );
}
