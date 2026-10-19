import { Bug, FolderGit2, FlaskConical, GitPullRequestDraft, FileText, Plug, ShieldCheck } from "lucide-react";
import type { LucideIcon } from "lucide-react";

interface Item { label: string; icon: LucideIcon; active?: boolean; soon?: boolean }

const GROUPS: { title: string; items: Item[] }[] = [
  {
    title: "Debugging tools",
    items: [
      { label: "Bug investigation", icon: Bug, active: true },
      { label: "Repository index", icon: FolderGit2, soon: true },
      { label: "Patch review", icon: GitPullRequestDraft, soon: true },
      { label: "Test runner", icon: FlaskConical, soon: true },
    ],
  },
  { title: "Documentation", items: [{ label: "Investigation reports", icon: FileText, soon: true }] },
  { title: "Integrations", items: [{ label: "Git & CI", icon: Plug, soon: true }] },
];

export default function Sidebar({ open, onClose }: { open: boolean; onClose: () => void }) {
  return (
    <>
      {open && <div className="fixed inset-0 z-30 bg-black/60 lg:hidden" onClick={onClose} aria-hidden />}
      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-[260px] flex-col border-r border-line bg-panel px-4 py-5 transition-transform lg:static lg:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
        aria-label="Primary"
      >
        <div className="mb-7 flex items-center gap-2 px-2">
          <ShieldCheck className="text-accent-hover" size={22} />
          <span className="text-xl font-semibold tracking-tight">CodeGuard<span className="text-accent-hover">.</span></span>
        </div>

        <nav className="flex-1 space-y-6 overflow-y-auto">
          {GROUPS.map((g) => (
            <div key={g.title}>
              <p className="mb-2 px-2 text-xs text-muted">{g.title}</p>
              <ul className="space-y-1">
                {g.items.map(({ label, icon: Icon, active, soon }) => (
                  <li key={label}>
                    <button
                      disabled={soon}
                      aria-current={active ? "page" : undefined}
                      className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm transition-colors ${
                        active ? "bg-accent text-white" : "text-ink/80 hover:bg-panel-2 disabled:cursor-not-allowed disabled:opacity-60"
                      }`}
                    >
                      <Icon size={18} />
                      <span className="flex-1">{label}</span>
                      {soon && <span className="rounded bg-line px-1.5 py-0.5 text-[10px] text-muted">Soon</span>}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </nav>

        <p className="mt-4 rounded-lg border border-line p-3 text-xs leading-relaxed text-muted">
          Retrieval with optional, opt-in AI explanation. Patching, test execution and repo indexing are not built yet.
        </p>
      </aside>
    </>
  );
}
