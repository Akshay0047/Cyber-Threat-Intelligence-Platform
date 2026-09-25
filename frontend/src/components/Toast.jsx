import { useEffect, useState } from "react";

export default function Toast() {
  const [toast, setToast] = useState(null);

  useEffect(() => {
    const stored = sessionStorage.getItem("cti-toast");
    if (stored) {
      sessionStorage.removeItem("cti-toast");
      setToast(stored);
    }
    function onToast(event) {
      setToast(event.detail?.message || "Unauthorized");
    }
    window.addEventListener("cti-toast", onToast);
    return () => window.removeEventListener("cti-toast", onToast);
  }, []);

  useEffect(() => {
    if (!toast) return undefined;
    const timer = window.setTimeout(() => setToast(null), 4200);
    return () => window.clearTimeout(timer);
  }, [toast]);

  if (!toast) return null;

  return (
    <div className="fixed bottom-5 right-5 z-[80] max-w-sm rounded-lg border border-red-500/50 bg-red-950/90 px-4 py-3 text-sm text-red-100 shadow-glow backdrop-blur-md">
      {toast}
    </div>
  );
}
