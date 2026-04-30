"use client";

import { FormEvent, useState } from "react";

export default function LeadFormSection() {
  const [status, setStatus] = useState<string>("");

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    const data = new FormData(form);
    const payload = Object.fromEntries(data.entries());

    const res = await fetch("/api/leads", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (res.ok) {
      if (typeof window !== "undefined" && typeof (window as Window & { gtag?: (...args: unknown[]) => void }).gtag === "function") {
        (window as Window & { gtag?: (...args: unknown[]) => void }).gtag?.("event", "register_submit");
      }
      setStatus("Thanks — we received your request.");
      form.reset();
    } else {
      setStatus("Could not submit right now. Please try again.");
    }
  }

  return (
    <section id="lead" className="px-6 md:px-10 py-16">
      <h2 className="text-3xl font-semibold text-white mb-3">Get Meddash Updates</h2>
      <p className="text-slate-300 mb-6">Join for catalyst alerts and therapeutic intelligence releases.</p>
      <form onSubmit={onSubmit} className="grid md:grid-cols-4 gap-3 max-w-5xl">
        <input required name="email" type="email" placeholder="Work email" className="rounded-lg bg-meddash-surface border border-white/10 px-3 py-3 text-white" />
        <input name="company" placeholder="Company" className="rounded-lg bg-meddash-surface border border-white/10 px-3 py-3 text-white" />
        <input name="role" placeholder="Role" className="rounded-lg bg-meddash-surface border border-white/10 px-3 py-3 text-white" />
        <button className="rounded-lg bg-meddash-cyan text-black font-semibold px-4 py-3">Register</button>
      </form>
      {status ? <p className="text-sm text-meddash-emerald mt-3">{status}</p> : null}
    </section>
  );
}
