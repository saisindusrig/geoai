import Link from "next/link";
import BrandWordmark from "./BrandWordmark";

const FOOTER_LINKS = {
  Product: [
    { label: "Platform", href: "/#platform" },
    { label: "Workflow", href: "/#how-it-works" },
    { label: "Launch Platform", href: "/projects/new" },
  ],
  Resources: [
    { label: "Workspace", href: "/projects/new" },
    { label: "Dashboard", href: "/dashboard" },
    { label: "Demo Project", href: "/dashboard" },
  ],
  Legal: [
    { label: "Contact", href: "mailto:support@sitegeoai.example" },
    { label: "Privacy", href: "/privacy" },
  ],
};

export default function Footer() {
  return (
    <footer className="border-t border-border bg-background-secondary">
      <div className="mx-auto max-w-7xl px-8 py-14">
        <div className="grid grid-cols-5 gap-10">
          <div className="col-span-2">
            <Link href="/" className="inline-block transition-opacity hover:opacity-90">
              <BrandWordmark size="sm" />
            </Link>
            <p className="mt-4 max-w-sm text-sm leading-relaxed text-muted-foreground">
              AI-powered 3D infrastructure planning from real-world maps. Select locations, analyze
              terrain, and generate civil engineering layouts with material estimates.
            </p>
          </div>

          {Object.entries(FOOTER_LINKS).map(([group, links]) => (
            <div key={group}>
              <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-4">
                {group}
              </p>
              <ul className="space-y-2.5">
                {links.map(({ label, href }) => (
                  <li key={label}>
                    <Link
                      href={href}
                      className="text-sm text-muted-foreground transition-colors hover:text-[var(--info-text)]"
                    >
                      {label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-12 flex items-center justify-between gap-2 border-t border-border pt-8">
          <p className="text-xs text-muted-foreground">
            © {new Date().getFullYear()} GeoAI. Preliminary planning only — not for construction
            approval.
          </p>
          <p className="text-xs text-muted-foreground">
            Updated {new Intl.DateTimeFormat("en", { month: "long", year: "numeric" }).format(new Date())} · Final drawings require licensed engineer verification.
          </p>
        </div>
      </div>
    </footer>
  );
}
